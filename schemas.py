
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Datos necesarios para registrar un pedido
class OrderCreate(BaseModel):
    tracking_number: str
    client_name: str
    address: str
    colony: str
    estimated_time: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# Datos para asignar un repartidor
class OrderAssign(BaseModel):
    driver_id: str


# Respuesta de los pedidos
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
    driver_id: Optional[str] = None
    photo_path: Optional[str] = None
    signature: Optional[str] = None
    proof_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# Evidencia de entrega
class ProofSubmission(BaseModel):
    photo_base64: str
    signature_base64: str
    timestamp: datetime


# Datos para registrar un repartidor
class DriverCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    vehicle: str = Field(min_length=2, max_length=50)


# Respuesta del perfil del repartidor
class DriverResponse(BaseModel):
    driver_id: str
    auth_user_id: Optional[str] = None
    name: str
    vehicle: str
    completed_deliveries: int
    average_time: str

    class Config:
        from_attributes = True

