
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


# Informacion publica para consultar el seguimiento de un pedido
class DriverLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: Optional[float] = Field(default=None, ge=0, le=10000)


class DriverLocationResponse(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderTrackingResponse(BaseModel):
    tracking_number: str
    status: str
    estimated_time: str
    proof_timestamp: Optional[datetime] = None
    current_location: Optional[DriverLocationResponse] = None


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


# Registro del Firebase Installation ID de un dispositivo
class FCMTokenRegister(BaseModel):
    firebase_installation_id: str = Field(min_length=10)
    platform: str = Field(pattern="^(android|ios)$")


# Respuesta del registro del dispositivo
class FCMTokenResponse(BaseModel):
    message: str
    platform: str
