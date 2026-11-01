from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderResponse(BaseModel):
    id: str
    tracking_number: str
    client_name: str
    address: str
    colony: str
    estimated_time: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        orm_mode = True

class ProofSubmission(BaseModel):
    photo_path: str
    signature: str
    timestamp: datetime

# Base de datos en memoria temporal
fake_orders_db = [
    {
        "id": "ord-001",
        "tracking_number": "#LT-543210",
        "client_name": "Maria Oliveira",
        "address": "Calle del Agua #214",
        "colony": "Cueramayo",
        "estimated_time": "10:22 AM",
        "status": "en_transito",
        "latitude": 20.6736,
        "longitude": -103.344
    }
]

# 1. Endpoint para entregas activas (Filtra las entregadas)
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders():
    return [o for o in fake_orders_db if o["status"] != "entregado"]

# 2. Endpoint general que TAMBIÉN filtra las entregadas (Para que la lista en vivo no muestre pasados)
@router.get("/", response_model=List[OrderResponse])
def get_all_orders():
    return [o for o in fake_orders_db if o["status"] != "entregado"]

# 3. Endpoint para completar la entrega con actualización de estatus blindada
@router.post("/{order_id}/complete")
def complete_order(order_id: str, proof: ProofSubmission):
    print(f"Recibida evidencia para la orden {order_id} a las {proof.timestamp}")
    
    clean_id = order_id.replace('#', '').strip().lower()
    updated = False
    
    for order in fake_orders_db:
        db_id = order["id"].replace('#', '').strip().lower()
        db_track = order["tracking_number"].replace('#', '').strip().lower()
        
        if clean_id == db_id or clean_id == db_track:
            order["status"] = "entregado"
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en memoria")
    
    return {
        "success": True,
        "message": f"Orden {order_id} completada y filtrada correctamente.",
        "order_id": order_id
    }
