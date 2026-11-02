
import os
import httpx

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from uuid import uuid4

from database import get_db
from models import DriverDB
from schemas import DriverCreate, DriverResponse
from auth import obtener_usuario_actual, verificar_administrador


router = APIRouter(prefix="/drivers", tags=["Drivers"])


# Configuracion de Supabase
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
                detail="No se pudo crear la cuenta. El correo podria estar registrado o los datos ser invalidos."
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
                detail="Supabase no devolvio el identificador del usuario"
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
            detail="Supabase devolvio una respuesta invalida"
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


# 3. Consultar perfil por ID (solo administrador)
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


# 4. Registrar un nuevo repartidor (solo administrador)
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
            detail="Ocurrio un error al registrar el repartidor"
        )

    return nuevo_repartidor

