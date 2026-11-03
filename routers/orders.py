
import os
import base64
import binascii

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List
from uuid import uuid4

from storage import subir_evidencia, obtener_url_temporal
from database import get_db
from models import OrderDB, DriverDB
from schemas import (
    OrderCreate,
    OrderResponse,
    OrderAssign,
    ProofSubmission
)
from auth import obtener_usuario_actual, verificar_administrador


router = APIRouter(prefix="/orders", tags=["Orders"])


# Buscar pedido por ID o numero de seguimiento
def find_order(db: Session, order_id: str):
    clean_id = order_id.replace("#", "").strip().lower()

    return db.query(OrderDB).filter(
        or_(
            func.lower(OrderDB.id) == clean_id,
            func.lower(func.replace(OrderDB.id, "#", "")) == clean_id,
            func.lower(
                func.replace(OrderDB.tracking_number, "#", "")
            ) == clean_id
        )
    ).first()


# Obtener el perfil del repartidor autenticado
def obtener_repartidor(usuario: dict, db: Session):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=403,
            detail="Esta cuenta no tiene un perfil de repartidor autorizado"
        )

    return driver


# 1. Consultar pedidos activos (solo administrador)
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    return db.query(OrderDB).filter(
        OrderDB.status != "entregado"
    ).all()


# 2. Consultar todos los pedidos (solo administrador)
@router.get("/", response_model=List[OrderResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    return db.query(OrderDB).all()


# 3. Consultar historial de entregas (solo administrador)
@router.get("/completed", response_model=List[OrderResponse])
def get_completed_orders(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    return db.query(OrderDB).filter(
        OrderDB.status == "entregado"
    ).all()


# 4. Consultar pedidos activos del repartidor autenticado
@router.get("/my", response_model=List[OrderResponse])
def get_my_orders(
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = obtener_repartidor(usuario, db)

    return db.query(OrderDB).filter(
        OrderDB.driver_id == driver.driver_id,
        OrderDB.status != "entregado"
    ).all()


# 5. Consultar pedidos disponibles para los repartidores
@router.get("/available", response_model=List[OrderResponse])
def get_available_orders(
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    obtener_repartidor(usuario, db)

    return db.query(OrderDB).filter(
        OrderDB.driver_id.is_(None),
        OrderDB.status == "pendiente"
    ).all()


# 6. Registrar un nuevo pedido (solo administrador)
@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    new_order = OrderDB(
        id=f"ord-{uuid4().hex[:10]}",
        tracking_number=order.tracking_number,
        client_name=order.client_name,
        address=order.address,
        colony=order.colony,
        estimated_time=order.estimated_time,
        latitude=order.latitude,
        longitude=order.longitude,
        status="pendiente"
    )

    db.add(new_order)

    try:
        db.commit()
        db.refresh(new_order)

    except Exception:
        db.rollback()
        raise

    return new_order


# 7. Asignar un pedido a un repartidor (solo administrador)
@router.patch("/{order_id}/assign", response_model=OrderResponse)
def assign_order(
    order_id: str,
    assignment: OrderAssign,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    order = find_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if order.status == "entregado":
        raise HTTPException(
            status_code=400,
            detail="El pedido ya fue entregado"
        )

    driver = db.query(DriverDB).filter(
        DriverDB.driver_id == assignment.driver_id
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Repartidor no encontrado"
        )

    order.driver_id = driver.driver_id
    order.status = "en_transito"

    db.commit()
    db.refresh(order)

    return order


# 8. Tomar un pedido disponible como repartidor
@router.post("/{order_id}/claim", response_model=OrderResponse)
def claim_order(
    order_id: str,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = obtener_repartidor(usuario, db)

    order = find_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    # Actualizacion atomica para evitar que dos repartidores
    # puedan tomar el mismo pedido.
    updated = db.query(OrderDB).filter(
        OrderDB.id == order.id,
        OrderDB.driver_id.is_(None),
        OrderDB.status == "pendiente"
    ).update(
        {
            OrderDB.driver_id: driver.driver_id,
            OrderDB.status: "en_transito"
        },
        synchronize_session=False
    )

    if updated == 0:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Este pedido ya fue tomado por otro repartidor"
        )

    db.commit()
    db.refresh(order)

    return order


# 9. Completar pedido y registrar evidencia
# Solamente el repartidor asignado puede completar el pedido
@router.post("/{order_id}/complete")
def complete_order(
    order_id: str,
    proof: ProofSubmission,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = obtener_repartidor(usuario, db)

    order = find_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if order.driver_id != driver.driver_id:
        raise HTTPException(
            status_code=403,
            detail="Este pedido no esta asignado a tu cuenta"
        )

    if order.status == "entregado":
        raise HTTPException(
            status_code=400,
            detail="Este pedido ya fue entregado"
        )

    # Convertir imagenes Base64 a bytes
    def decodificar_imagen(valor: str):
        if valor.startswith("data:") and "," in valor:
            valor = valor.split(",", 1)[1]

        try:
            contenido = base64.b64decode(valor, validate=True)

        except (binascii.Error, ValueError):
            raise HTTPException(
                status_code=400,
                detail="Formato de imagen invalido"
            )

        if not contenido:
            raise HTTPException(
                status_code=400,
                detail="La imagen esta vacia"
            )

        if len(contenido) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="La imagen supera los 5 MB"
            )

        return contenido

    foto = decodificar_imagen(proof.photo_base64)
    firma = decodificar_imagen(proof.signature_base64)

    try:
        # Subir fotografia a Supabase Storage
        ruta_foto = subir_evidencia(
            contenido=foto,
            extension="jpg",
            tipo_contenido="image/jpeg",
            order_id=order.id,
            carpeta="fotografias"
        )

        # Subir firma a Supabase Storage
        ruta_firma = subir_evidencia(
            contenido=firma,
            extension="png",
            tipo_contenido="image/png",
            order_id=order.id,
            carpeta="firmas"
        )

        # Guardar las rutas en PostgreSQL
        order.photo_path = ruta_foto
        order.signature = ruta_firma
        order.proof_timestamp = proof.timestamp
        order.status = "entregado"

        # Actualizar entregas del repartidor
        driver.completed_deliveries = (
            driver.completed_deliveries or 0
        ) + 1

        db.commit()
        db.refresh(order)

        return {
            "success": True,
            "message": "Pedido completado correctamente",
            "order_id": order.id,
            "photo_path": order.photo_path,
            "signature": order.signature,
            "proof_timestamp": order.proof_timestamp
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        print(f"Error al guardar evidencia: {repr(e)}")

        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar la evidencia de entrega"
        )


# 10. Consultar evidencias de una entrega
# Administrador o repartidor asignado
@router.get("/{order_id}/evidence")
def get_order_evidence(
    order_id: str,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    order = find_order(db, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    admin_id = os.getenv("ADMIN_USER_ID")

    if usuario.get("id") != admin_id:
        driver = obtener_repartidor(usuario, db)

        if order.driver_id != driver.driver_id:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para consultar estas evidencias"
            )

    if order.status != "entregado":
        raise HTTPException(
            status_code=400,
            detail="El pedido todavia no ha sido entregado"
        )

    if not order.photo_path or not order.signature:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron evidencias de entrega"
        )

    try:
        # Generar enlaces temporales de Supabase
        foto_url = obtener_url_temporal(order.photo_path)
        firma_url = obtener_url_temporal(order.signature)

        return {
            "order_id": order.id,
            "tracking_number": order.tracking_number,
            "client_name": order.client_name,
            "photo_url": foto_url,
            "signature_url": firma_url,
            "proof_timestamp": order.proof_timestamp
        }

    except Exception as e:
        print(f"Error al consultar evidencias: {repr(e)}")

        raise HTTPException(
            status_code=500,
            detail="No se pudieron consultar las evidencias"
        )
