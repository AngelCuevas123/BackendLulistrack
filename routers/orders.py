
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from typing import List
from uuid import uuid4
import base64
import binascii

from storage import subir_evidencia
from database import get_db
from models import OrderDB, DriverDB
from schemas import (
    OrderCreate,
    OrderResponse,
    OrderAssign,
    ProofSubmission
)

router = APIRouter(prefix="/orders", tags=["Orders"])


# Buscar pedido por ID o numero de seguimiento
def find_order(db: Session, order_id: str):
    clean_id = order_id.replace("#", "").strip().lower()

    return db.query(OrderDB).filter(
        or_(
            func.lower(OrderDB.id) == clean_id,
            func.lower(func.replace(OrderDB.id, "#", "")) == clean_id,
            func.lower(func.replace(OrderDB.tracking_number, "#", "")) == clean_id
        )
    ).first()


# 1. Consultar pedidos activos
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders(db: Session = Depends(get_db)):
    return db.query(OrderDB).filter(
        OrderDB.status != "entregado"
    ).all()


# 2. Consultar todos los pedidos activos
@router.get("/", response_model=List[OrderResponse])
def get_all_orders(db: Session = Depends(get_db)):
    return db.query(OrderDB).filter(
        OrderDB.status != "entregado"
    ).all()


# 3. Consultar historial de entregas
@router.get("/completed", response_model=List[OrderResponse])
def get_completed_orders(db: Session = Depends(get_db)):
    return db.query(OrderDB).filter(
        OrderDB.status == "entregado"
    ).all()


# 4. Registrar un nuevo pedido
@router.post("/", response_model=OrderResponse, status_code=201)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El numero de seguimiento ya existe"
        )

    return new_order


# 5. Asignar un pedido a un repartidor
@router.patch("/{order_id}/assign", response_model=OrderResponse)
def assign_order(
    order_id: str,
    assignment: OrderAssign,
    db: Session = Depends(get_db)
):
    order = find_order(db, order_id)

    if not order:
        raise HTTPException(404, "Pedido no encontrado")

    if order.status == "entregado":
        raise HTTPException(400, "El pedido ya fue entregado")

    driver = db.query(DriverDB).filter(
        DriverDB.driver_id == assignment.driver_id
    ).first()

    if not driver:
        raise HTTPException(404, "Repartidor no encontrado")

    order.driver_id = driver.driver_id
    order.status = "en_transito"

    db.commit()
    db.refresh(order)

    return order


# 6. Completar pedido y registrar evidencia
@router.post("/{order_id}/complete")
def complete_order(
    order_id: str,
    proof: ProofSubmission,
    db: Session = Depends(get_db)
):
    order = find_order(db, order_id)

    if not order:
        raise HTTPException(404, "Pedido no encontrado")

    if order.status == "entregado":
        raise HTTPException(400, "Este pedido ya fue entregado")

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
            raise HTTPException(400, "La imagen esta vacia")

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
        if order.driver_id:
            driver = db.query(DriverDB).filter(
                DriverDB.driver_id == order.driver_id
            ).first()

            if driver:
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

