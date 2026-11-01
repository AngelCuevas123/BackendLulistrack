from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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
        from_attributes = True

class ProofSubmission(BaseModel):
    photo_path: str
    signature: str
    timestamp: datetime

class DriverResponse(BaseModel):
    driver_id: str
    name: str
    vehicle: str
    completed_deliveries: int
    average_time: str

    class Config:
        from_attributes = True
        