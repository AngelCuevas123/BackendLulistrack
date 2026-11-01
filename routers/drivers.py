
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4

from database import get_db
from models import DriverDB
from schemas import DriverCreate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


# 1. Consultar todos los repartidores
@router.get("/", response_model=List[DriverResponse])
def get_all_drivers(db: Session = Depends(get_db)):
    return db.query(DriverDB).all()


# 2. Consultar perfil de un repartidor
@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver_profile(
    driver_id: str,
    db: Session = Depends(get_db)
):
    driver = db.query(DriverDB).filter(
        DriverDB.driver_id == driver_id
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="Repartidor no encontrado"
        )

    return driver


# 3. Registrar un nuevo repartidor
@router.post("/", response_model=DriverResponse, status_code=201)
def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db)
):
    new_driver = DriverDB(
        driver_id=f"drv-{uuid4().hex[:8]}",
        name=driver.name,
        vehicle=driver.vehicle,
        completed_deliveries=0,
        average_time=driver.average_time
    )

    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)

    return new_driver

