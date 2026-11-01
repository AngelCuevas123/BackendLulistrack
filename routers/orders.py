
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from typing import List
from uuid import uuid4

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
            OrderDB.id == order_id,
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

    # Evitar contar dos veces una entrega
    if order.status == "entregado":
        raise HTTPException(400, "Este pedido ya fue entregado")

    order.status = "entregado"
    order.photo_path = proof.photo_path
    order.signature = proof.signature
    order.proof_timestamp = proof.timestamp

    # Actualizar las entregas del repartidor
    if order.driver_id:
        driver = db.query(DriverDB).filter(
            DriverDB.driver_id == order.driver_id
        ).first()

        if driver:
            driver.completed_deliveries += 1

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "message": "Pedido completado correctamente",
        "order_id": order.id
    }

