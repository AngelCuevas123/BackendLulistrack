import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from fastapi import HTTPException


ORS_API_KEY = os.getenv("ORS_API_KEY", "").strip()
ORS_BASE_URL = os.getenv(
    "ORS_BASE_URL",
    "https://api.openrouteservice.org/v2/directions"
).rstrip("/")


def calcular_ruta(
    origen_latitude: float,
    origen_longitude: float,
    destino_latitude: float,
    destino_longitude: float,
    preference: str = "recommended",
) -> dict[str, Any]:
    """
    Solicita a openrouteservice una ruta en automóvil y normaliza
    la respuesta para que Flutter pueda dibujarla y mostrar instrucciones.
    Las coordenadas GeoJSON se conservan en orden [longitud, latitud].
    """
    if not ORS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="El servicio de rutas no está configurado en el servidor"
        )

    url = f"{ORS_BASE_URL}/driving-car/geojson"
    payload = {
        "coordinates": [
            [origen_longitude, origen_latitude],
            [destino_longitude, destino_latitude],
        ],
        "instructions": True,
        "instructions_format": "text",
        "language": "es",
        "preference": preference,
    }

    try:
        response = httpx.post(
            url,
            json=payload,
            headers={
                "Authorization": ORS_API_KEY,
                "Accept": "application/geo+json, application/json",
                "Content-Type": "application/json",
            },
            timeout=25.0,
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="El servicio de rutas tardó demasiado en responder"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con el servicio de rutas"
        )

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="Se alcanzó el límite temporal de consultas de rutas"
        )
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail="El proveedor de rutas rechazó la configuración del servidor"
        )
    if response.status_code in (400, 404):
        raise HTTPException(
            status_code=422,
            detail="No se encontró una ruta válida entre las ubicaciones indicadas"
        )
    if response.status_code >= 500:
        raise HTTPException(
            status_code=503,
            detail="El servicio externo de rutas no está disponible temporalmente"
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="El servicio externo de rutas devolvió una respuesta inesperada"
        )

    try:
        data = response.json()
        feature = data["features"][0]
        geometry = feature["geometry"]
        properties = feature["properties"]
        summary = properties["summary"]
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="El proveedor de rutas devolvió datos incompletos"
        )

    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") != "LineString" or len(coordinates) < 2:
        raise HTTPException(
            status_code=502,
            detail="El proveedor no devolvió una geometría de ruta válida"
        )

    distance_meters = float(summary.get("distance", 0))
    duration_seconds = float(summary.get("duration", 0))
    if distance_meters <= 0 or duration_seconds <= 0:
        raise HTTPException(
            status_code=422,
            detail="No se pudo calcular una distancia y duración válidas"
        )

    steps = []
    for segment in properties.get("segments", []):
        for step in segment.get("steps", []):
            steps.append({
                "instruction": step.get("instruction", ""),
                "name": step.get("name") or None,
                "distance_meters": float(step.get("distance", 0)),
                "duration_seconds": float(step.get("duration", 0)),
                "type": step.get("type"),
            })

    now = datetime.now(timezone.utc)
    return {
        "profile": "driving-car",
        "preference": preference,
        "geometry": coordinates,
        "distance_meters": round(distance_meters, 1),
        "duration_seconds": round(duration_seconds, 1),
        "distance_km": round(distance_meters / 1000, 2),
        "duration_minutes": round(duration_seconds / 60, 1),
        "estimated_arrival_at": now + timedelta(seconds=duration_seconds),
        "steps": steps,
    }
