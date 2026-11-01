from fastapi import FastAPI
from database import engine, Base
from routers import orders, drivers

# Crea las tablas en PostgreSQL automáticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Lulistrack API",
    description="Backend oficial para la gestión de entregas y rutas de Lulistrack",
    version="1.0.0"
)

# Registrar los módulos o routers
app.include_router(orders.router)
app.include_router(drivers.router)

@app.get("/")
def root():
    return {"message": "¡Servidor de Lulistrack corriendo al 100%!"}
