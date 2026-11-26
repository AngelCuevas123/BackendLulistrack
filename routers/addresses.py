from functools import lru_cache
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query
from auth import verificar_administrador

router = APIRouter(prefix="/addresses", tags=["Addresses"])

POSTAL_API = "https://api.zippopotam.us/mx"
PHOTON_API = "https://photon.komoot.io/api/"


@lru_cache(maxsize=2048)
def _postal_lookup(postal_code: str):
    try:
        response = httpx.get(
            f"{POSTAL_API}/{postal_code}",
            headers={"User-Agent": "Lulistrack/1.0 (address autocomplete)"},
            timeout=8.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No fue posible consultar el catálogo postal nacional") from exc

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="No encontramos ese código postal en el catálogo disponible")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="El servicio de códigos postales no está disponible temporalmente")

    data = response.json()
    places = data.get("places") or []
    return {
        "postal_code": data.get("post code", postal_code),
        "country": data.get("country", "Mexico"),
        "places": [
            {
                "name": place.get("place name"),
                "state": place.get("state"),
                "state_abbreviation": place.get("state abbreviation"),
                "latitude": float(place["latitude"]) if place.get("latitude") else None,
                "longitude": float(place["longitude"]) if place.get("longitude") else None,
            }
            for place in places
        ],
    }


@router.get("/postal-codes/{postal_code}")
def lookup_postal_code(
    postal_code: str,
    usuario: dict = Depends(verificar_administrador),
):
    if len(postal_code) != 5 or not postal_code.isdigit():
        raise HTTPException(status_code=422, detail="El código postal debe contener exactamente cinco dígitos")
    return _postal_lookup(postal_code)


@router.get("/search")
def search_address(
    q: str = Query(..., min_length=2, max_length=120),
    postal_code: str | None = Query(default=None, pattern=r"^\\d{5}$"),
    locality: str | None = None,
    municipality: str | None = None,
    state: str | None = None,
    usuario: dict = Depends(verificar_administrador),
):
    query_parts = [q, locality, municipality, state, postal_code, "Mexico"]
    search_text = ", ".join(part.strip() for part in query_parts if part and part.strip())

    try:
        response = httpx.get(
            PHOTON_API,
            params={"q": search_text, "limit": 8, "lang": "es"},
            headers={"User-Agent": "Lulistrack/1.0 (address autocomplete)"},
            timeout=8.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="No fue posible consultar las calles. Puedes capturar la dirección manualmente o ajustar el mapa.") from exc

    features = response.json().get("features") or []
    results = []
    for feature in features:
        properties = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) != 2:
            continue
        results.append({
            "name": properties.get("name") or properties.get("street") or q,
            "street": properties.get("street") or properties.get("name"),
            "district": properties.get("district") or properties.get("suburb"),
            "locality": properties.get("city") or properties.get("locality") or properties.get("village") or properties.get("town"),
            "municipality": properties.get("county"),
            "state": properties.get("state"),
            "postal_code": properties.get("postcode"),
            "latitude": coordinates[1],
            "longitude": coordinates[0],
            "country": properties.get("country"),
        })
    return {"results": results}
