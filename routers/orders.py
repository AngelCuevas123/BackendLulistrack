from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

# Esquema Pydantic para la respuesta de entregas activas
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

# Esquema para recibir la evidencia de entrega (Foto y Firma)
class ProofSubmission(BaseModel):
    photo_path: str
    signature: str
    timestamp: datetime

# Base de datos en memoria temporal (permite actualizar estados en tiempo real)
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

# 1. Endpoint para obtener entregas activas (Filtra las que ya fueron entregadas)
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders():
    # Devuelve únicamente los pedidos cuyo estado NO sea "entregado"
    return [order for order in fake_orders_db if order["status"] != "entregado"]

# 2. Endpoint para completar la entrega con foto, firma y actualización de estado
@router.post("/{order_id}/complete")
def complete_order(order_id: str, proof: ProofSubmission):
    print(f"Recibida evidencia para la orden {order_id} a las {proof.timestamp}")
    print(f"Ruta de foto: {proof.photo_path}")
    
    # Buscamos el pedido en la lista y actualizamos su estado a "entregado"
    updated = False
    clean_id = order_id.replace('#', '').strip()
    
    for order in fake_orders_db:
        if order["id"] == clean_id or clean_id in order["tracking_number"] or order["id"] == order_id:
            order["status"] = "entregado"
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en memoria")
    
    return {
        "success": True,
        "message": f"Orden {order_id} completada, estado actualizado y evidencia registrada.",
        "order_id": order_id
    }
