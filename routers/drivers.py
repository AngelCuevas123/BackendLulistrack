from fastapi import APIRouter, HTTPException
from schemas import DriverResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver_profile(driver_id: str):
    # Aquí puedes realizar la consulta real a tu base de datos PostgreSQL usando SQLAlchemy.
    # Por ahora devolvemos datos mock compatibles con tu UserModel de Flutter:
    return {
        "driver_id": driver_id,
        "name": "Juan Ángel Cuevas",
        "vehicle": "Motocicleta de Reparto #04",
        "completed_deliveries": 38,
        "average_time": "12 min"
    }
