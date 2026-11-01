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

# Base de datos en memoria temporal con múltiples pedidos para un flujo dinámico completo
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
    },
    {
        "id": "ord-002",
        "tracking_number": "#LT-987654",
        "client_name": "Carlos Mendoza",
        "address": "Av. Benito Juárez #405",
        "colony": "Centro",
        "estimated_time": "11:45 AM",
        "status": "en_transito",
        "latitude": 20.6767,
        "longitude": -103.347
    },
    {
        "id": "ord-003",
        "tracking_number": "#LT-112233",
        "client_name": "Ana Sofía Rivas",
        "address": "Blvd. Marcelino García #88",
        "colony": "Lomas del Valle",
        "estimated_time": "01:15 PM",
        "status": "en_transito",
        "latitude": 20.6800,
        "longitude": -103.350
    },
    {
        "id": "ord-history-1",
        "tracking_number": "#LT-543200",
        "client_name": "Carlos Slim",
        "address": "Av. Insurgentes #100",
        "colony": "Roma Norte",
        "estimated_time": "09:00 AM",
        "status": "entregado",
        "latitude": 20.6700,
        "longitude": -103.340
    }
]

# 1. Endpoint para entregas activas (Filtra las entregadas)
@router.get("/active", response_model=List[OrderResponse])
def get_active_orders():
    return [o for o in fake_orders_db if o["status"] != "entregado"]

# 2. Endpoint general que también filtra las entregadas (Para la lista en vivo)
@router.get("/", response_model=List[OrderResponse])
def get_all_orders():
    return [o for o in fake_orders_db if o["status"] != "entregado"]

# 3. Endpoint exclusivo para el Historial (Devuelve únicamente los ya entregados)
@router.get("/completed", response_model=List[OrderResponse])
def get_completed_orders():
    return [o for o in fake_orders_db if o["status"] == "entregado"]

# 4. Endpoint para completar la entrega con actualización de estatus blindada y manejo de fotos
@router.post("/{order_id}/complete")
def complete_order(order_id: str, proof: ProofSubmission):
    print(f"Recibida evidencia para la orden {order_id} a las {proof.timestamp}")
    print(f"Ruta de foto: {proof.photo_path}")
    
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
        "message": f"Orden {order_id} completada, movida al historial y filtrada correctamente.",
        "order_id": order_id
    }
