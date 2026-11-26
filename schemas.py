
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0, le=10000)


# Datos necesarios para registrar un pedido
class OrderCreate(BaseModel):
    tracking_number: str
    client_name: str
    address: str
    colony: str
    estimated_time: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    items: List[OrderItemCreate] = Field(default_factory=list)


# Datos para asignar un repartidor
class OrderAssign(BaseModel):
    driver_id: str


class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    sku: str
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


# Respuesta de los pedidos
class OrderResponse(BaseModel):
    id: str
    tracking_number: str
    client_name: str
    address: str
    colony: str
    estimated_time: str
    status: str
    created_at: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    driver_id: Optional[str] = None
    photo_path: Optional[str] = None
    signature: Optional[str] = None
    proof_timestamp: Optional[datetime] = None
    items: List[OrderItemResponse] = Field(default_factory=list)

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


class InventoryProductCreate(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    unit: str = Field(default="pieza", min_length=1, max_length=30)
    stock_quantity: int = Field(default=0, ge=0, le=100000000)
    min_stock: int = Field(default=0, ge=0, le=100000000)
    unit_price: float = Field(default=0, ge=0, le=100000000)


class InventoryProductUpdate(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=2, max_length=40)
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    unit: Optional[str] = Field(default=None, min_length=1, max_length=30)
    stock_quantity: Optional[int] = Field(default=None, ge=0, le=100000000)
    min_stock: Optional[int] = Field(default=None, ge=0, le=100000000)
    unit_price: Optional[float] = Field(default=None, ge=0, le=100000000)
    is_active: Optional[bool] = None


class InventoryProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    description: Optional[str] = None
    unit: str
    stock_quantity: int
    min_stock: int
    unit_price: float
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Solicitud para calcular una ruta de un pedido asignado al repartidor.
class RoutePreviewRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    # Flutter puede enviar su GPS actual; si se omite, se usa la última
    # ubicación guardada del repartidor (máximo 5 minutos de antigüedad).
    origin_latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    origin_longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    preference: str = Field(
        default="recommended",
        pattern="^(recommended|fastest|shortest)$"
    )


class RouteStepResponse(BaseModel):
    instruction: str
    name: Optional[str] = None
    distance_meters: float
    duration_seconds: float
    type: Optional[int] = None


class RoutePreviewResponse(BaseModel):
    profile: str
    preference: str
    # GeoJSON: cada punto conserva el orden [longitud, latitud].
    geometry: List[List[float]]
    distance_meters: float
    duration_seconds: float
    distance_km: float
    duration_minutes: float
    estimated_arrival_at: datetime
    steps: List[RouteStepResponse] = Field(default_factory=list)

