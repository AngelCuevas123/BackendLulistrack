
import os
import httpx

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List
from uuid import uuid4

from database import get_db
from models import DriverDB, DriverDeviceDB, DriverLocationDB
from schemas import (
    DriverCreate,
    DriverResponse,
    FCMTokenRegister,
    FCMTokenResponse,
    DriverLocationUpdate,
    DriverLocationResponse
)
from auth import obtener_usuario_actual, verificar_administrador


router = APIRouter(prefix="/drivers", tags=["Drivers"])


# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


# Crear usuario en Supabase Auth
def crear_usuario_supabase(driver: DriverCreate):

    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar las credenciales administrativas de Supabase"
        )

    try:
        respuesta = httpx.post(
            f"{SUPABASE_URL}/auth/v1/admin/users",
            headers={
                "apikey": SUPABASE_SECRET_KEY,
                "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "email": str(driver.email),
                "password": driver.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": driver.name
                }
            },
            timeout=20.0
        )

        if respuesta.status_code in (400, 409, 422):
            raise HTTPException(
                status_code=409,
                detail="No se pudo crear la cuenta. El correo podría estar registrado o los datos ser inválidos."
            )

        if respuesta.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail="Supabase no pudo crear la cuenta del repartidor"
            )

        datos = respuesta.json()
        usuario_id = datos.get("id")

        if not usuario_id:
            raise HTTPException(
                status_code=502,
                detail="Supabase no devolvió el identificador del usuario"
            )

        return usuario_id

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con Supabase"
        )

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Supabase devolvió una respuesta inválida"
        )


# Eliminar usuario de Supabase si falla el registro en PostgreSQL
def eliminar_usuario_supabase(usuario_id: str):

    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        return

    try:
        respuesta = httpx.delete(
            f"{SUPABASE_URL}/auth/v1/admin/users/{usuario_id}",
            headers={
                "apikey": SUPABASE_SECRET_KEY,
                "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"
            },
            timeout=20.0
        )

        if respuesta.status_code >= 400:
            print("No se pudo eliminar la cuenta de Supabase")

    except httpx.RequestError:
        print("No se pudo conectar con Supabase para eliminar la cuenta")


# 1. Consultar todos los repartidores (solo administrador)
@router.get("/", response_model=List[DriverResponse])
def get_all_drivers(
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    return db.query(DriverDB).all()


# 2. Consultar el perfil del repartidor autenticado
@router.get("/me", response_model=DriverResponse)
def get_my_driver_profile(
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="No existe un perfil de repartidor asociado a esta cuenta"
        )

    return driver



# 3. Actualizar la ubicación del repartidor autenticado
@router.put("/me/location", response_model=DriverLocationResponse)
def update_my_location(
    data: DriverLocationUpdate,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="No existe un perfil de repartidor asociado a esta cuenta"
        )

    location = db.query(DriverLocationDB).filter(
        DriverLocationDB.driver_id == driver.driver_id
    ).first()

    if location is None:
        location = DriverLocationDB(
            driver_id=driver.driver_id,
            latitude=data.latitude,
            longitude=data.longitude,
            accuracy=data.accuracy
        )
        db.add(location)
    else:
        location.latitude = data.latitude
        location.longitude = data.longitude
        location.accuracy = data.accuracy
        location.updated_at = func.now()

    db.commit()
    db.refresh(location)

    return location


# 4. Registrar o actualizar el FID del repartidor autenticado
@router.post("/me/fcm-token", response_model=FCMTokenResponse)
def register_fcm_token(
    data: FCMTokenRegister,
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="No existe un perfil de repartidor asociado a esta cuenta"
        )

    try:
        device = db.query(DriverDeviceDB).filter(
            DriverDeviceDB.firebase_installation_id
            == data.firebase_installation_id
        ).first()

        if device:
            device.driver_id = driver.driver_id
            device.platform = data.platform
            device.is_active = True
        else:
            device = DriverDeviceDB(
                driver_id=driver.driver_id,
                firebase_installation_id=data.firebase_installation_id,
                platform=data.platform,
                is_active=True
            )
            db.add(device)

        db.commit()

        return FCMTokenResponse(
            message="Firebase Installation ID registrado correctamente",
            platform=data.platform
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el identificador del dispositivo"
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al registrar el dispositivo"
        )


# 4. Desactivar el FID al cerrar sesión
@router.delete("/me/fcm-token", response_model=FCMTokenResponse)
def unregister_fcm_token(
    firebase_installation_id: str = Query(..., min_length=10),
    usuario: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    driver = db.query(DriverDB).filter(
        DriverDB.auth_user_id == usuario["id"]
    ).first()

    if not driver:
        raise HTTPException(
            status_code=404,
            detail="No existe un perfil de repartidor asociado a esta cuenta"
        )

    device = db.query(DriverDeviceDB).filter(
        DriverDeviceDB.firebase_installation_id
        == firebase_installation_id,
        DriverDeviceDB.driver_id == driver.driver_id
    ).first()

    if not device:
        return FCMTokenResponse(
            message="El dispositivo no está registrado para este repartidor",
            platform="unknown"
        )

    device.is_active = False
    db.commit()

    return FCMTokenResponse(
        message="Dispositivo desactivado correctamente",
        platform=device.platform
    )


# 5. Consultar perfil por ID (solo administrador)
@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver_profile(
    driver_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
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


# 6. Registrar un nuevo repartidor (solo administrador)
@router.post("/", response_model=DriverResponse, status_code=201)
def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):

    # Crear cuenta de acceso en Supabase Auth
    usuario_id = crear_usuario_supabase(driver)

    # Crear perfil del repartidor en PostgreSQL
    nuevo_repartidor = DriverDB(
        driver_id=f"drv-{uuid4().hex[:8]}",
        auth_user_id=usuario_id,
        name=driver.name,
        vehicle=driver.vehicle,
        completed_deliveries=0,
        average_time="Sin datos"
    )

    try:
        db.add(nuevo_repartidor)
        db.commit()
        db.refresh(nuevo_repartidor)

    except IntegrityError:
        db.rollback()
        eliminar_usuario_supabase(usuario_id)

        raise HTTPException(
            status_code=409,
            detail="No se pudo guardar el perfil del repartidor"
        )

    except Exception:
        db.rollback()
        eliminar_usuario_supabase(usuario_id)

        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al registrar el repartidor"
        )

    return nuevo_repartidor
