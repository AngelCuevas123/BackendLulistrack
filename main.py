
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models

from routers import orders, drivers


# Crear las tablas si todavia no existen
Base.metadata.create_all(bind=engine)


# Configuracion principal de FastAPI
app = FastAPI(
    title="Lulistrack API",
    description="Backend oficial para la gestion de entregas y rutas de Lulistrack",
    version="1.0.0"
)


# Configuracion CORS para React y Vercel
origins = os.getenv(
    "CORS_ORIGINS",
    "https://lulistrack-dashboard.vercel.app,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Registrar los routers
app.include_router(orders.router)
app.include_router(drivers.router)


# Ruta principal
@app.get("/")
def root():
    return {
        "message": "Servidor de Lulistrack corriendo al 100%"
    }


# Comprobar el estado del servidor
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Lulistrack API funcionando correctamente"
    }

