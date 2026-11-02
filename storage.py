
import os
from uuid import uuid4

from supabase import create_client


# Conexion con Supabase Storage
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "evidencias-entrega")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltan las variables de Supabase en el entorno"
    )


# Crear cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Subir una evidencia al almacenamiento
def subir_evidencia(
    contenido: bytes,
    extension: str,
    tipo_contenido: str,
    order_id: str,
    carpeta: str
):
    nombre_archivo = f"{uuid4().hex}.{extension}"
    ruta = f"{order_id}/{carpeta}/{nombre_archivo}"

    supabase.storage.from_(BUCKET_NAME).upload(
        path=ruta,
        file=contenido,
        file_options={
            "content-type": tipo_contenido,
            "upsert": "true"
        }
    )

    return ruta


# Generar enlace temporal para consultar una evidencia
def obtener_url_temporal(ruta: str):
    resultado = supabase.storage.from_(BUCKET_NAME).create_signed_url(
        path=ruta,
        expires_in=3600
    )

    return resultado["signedURL"]

