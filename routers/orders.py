from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

import database
import models
import schemas

router = APIRouter(prefix="/orders", tags=["Orders"])

# 1. Endpoint GET para obtener las entregas activas desde Supabase (filtrando las ya entregadas)
@router.get("/active", response_model=List[schemas.OrderResponse])
def get_active_orders(db: Session = Depends(database.get_db)):
    try:
        active_orders = db.query(models.OrderDB).filter(models.OrderDB.status != "entregado").all()
        return active_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint GET general para todos los pedidos
@router.get("/", response_model=List[schemas.OrderResponse])
def get_orders(db: Session = Depends(database.get_db)):
    orders = db.query(models.OrderDB).all()
    return orders

# 3. Endpoint POST para registrar un nuevo pedido
@router.post("/", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: schemas.OrderResponse, db: Session = Depends(database.get_db)):
    existing = db.query(models.OrderDB).filter(models.OrderDB.tracking_number == order_data.tracking_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="El número de rastreo ya existe")

    new_order = models.OrderDB(
        id=order_data.id,
        tracking_number=order_data.tracking_number,
        client_name=order_data.client_name,
        address=order_data.address,
        colony=order_data.colony,
        estimated_time=order_data.estimated_time,
        status=order_data.status,
        latitude=order_data.latitude,
        longitude=order_data.longitude
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

# 4. Endpoint para completar la entrega (¡Al final para evitar conflictos de rutas!)
@router.post("/{order_id}/complete")
def complete_order(order_id: str, proof: schemas.ProofSubmission, db: Session = Depends(database.get_db)):
    clean_id = order_id.replace('#', '').strip()
    
    order = db.query(models.OrderDB).filter(models.OrderDB.id == clean_id).first()
    if not order:
        order = db.query(models.OrderDB).filter(models.OrderDB.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    order.status = "entregado"
    db.commit()
    
    print(f"Recibida evidencia para la orden {order_id} a las {proof.timestamp}")
    
    return {
        "success": True,
        "message": f"Orden {order_id} completada y registrada en Supabase.",
        "order_id": order_id
    }
