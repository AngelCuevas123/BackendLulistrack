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

# 1. Endpoint para obtener entregas activas
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders():
    return [
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

# 2. Endpoint para completar la entrega con foto y firma 
@router.post("/{order_id}/complete")
def complete_order(order_id: str, proof: ProofSubmission):
    print(f"Recibida evidencia para la orden {order_id} a las {proof.timestamp}")
    print(f"Ruta de foto: {proof.photo_path}")
    
    return {
        "success": True,
        "message": f"Orden {order_id} completada y registrada exitosamente.",
        "order_id": order_id
    }
