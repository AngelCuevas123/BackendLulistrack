from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import obtener_usuario_actual
from database import get_db
from models import DriverDB, DriverLocationDB, OrderDB
from schemas import RoutePreviewRequest, RoutePreviewResponse
from services.routing_service import calcular_ruta


router = APIRouter(prefix="/routes", tags=["Routes"])


def _obtener_contexto_ruta(
    order_id: str,
    usuario: dict,
    db: Session,
    origin_latitude: Optional[float] = None,
    origin_longitude: Optional[float] = None,
):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=403,
            detail="Esta cuenta no tiene un perfil de repartidor autorizado"
        )

    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    if order.driver_id != driver.driver_id:
        raise HTTPException(
            status_code=403,
            detail="Este pedido no está asignado a tu cuenta"
        )

    if order.status == "entregado":
        raise HTTPException(
            status_code=409,
            detail="El pedido ya fue entregado"
        )

    if order.latitude is None or order.longitude is None:
        raise HTTPException(
            status_code=422,
            detail="El pedido todavía no tiene coordenadas de destino"
        )

    # Si Flutter envía la posición GPS actual, se utiliza directamente.
    # Si no, se utiliza la última posición guardada y se exige que sea reciente.
    if origin_latitude is not None and origin_longitude is not None:
        latitude = origin_latitude
        longitude = origin_longitude
    else:
        location = db.query(DriverLocationDB).filter(
            DriverLocationDB.driver_id == driver.driver_id,
            DriverLocationDB.updated_at >= func.now() - timedelta(minutes=5)
        ).first()

        if not location:
            raise HTTPException(
                status_code=409,
                detail="No hay una ubicación GPS reciente del repartidor"
            )

        latitude = location.latitude
        longitude = location.longitude

    return latitude, longitude, order.latitude, order.longitude


@router.post("/preview", response_model=RoutePreviewResponse)
def preview_route(
    request: RoutePreviewRequest,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    if (request.origin_latitude is None) != (request.origin_longitude is None):
        raise HTTPException(
            status_code=422,
            detail="Debes enviar latitud y longitud de origen juntas"
        )

    origin_lat, origin_lon, destination_lat, destination_lon = (
        _obtener_contexto_ruta(
            order_id=request.order_id,
            usuario=usuario,
            db=db,
            origin_latitude=request.origin_latitude,
            origin_longitude=request.origin_longitude,
        )
    )

    return calcular_ruta(
        origen_latitude=origin_lat,
        origen_longitude=origin_lon,
        destino_latitude=destination_lat,
        destino_longitude=destination_lon,
        preference=request.preference,
    )


@router.get("/{order_id}", response_model=RoutePreviewResponse)
def get_route_for_order(
    order_id: str,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db),
):
    origin_lat, origin_lon, destination_lat, destination_lon = (
        _obtener_contexto_ruta(
            order_id=order_id,
            usuario=usuario,
            db=db,
        )
    )

    return calcular_ruta(
        origen_latitude=origin_lat,
        origen_longitude=origin_lon,
        destino_latitude=destination_lat,
        destino_longitude=destination_lon,
        preference="recommended",
    )
