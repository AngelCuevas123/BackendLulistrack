
import os
import httpx

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Configuracion de Supabase
SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "https://dzlvdtfzobeaayiutjik.supabase.co"
).rstrip("/")

SUPABASE_API_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

security = HTTPBearer()


# Verificar que el usuario tenga una sesion valida
def obtener_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar las credenciales de Supabase"
        )

    token = credentials.credentials

    try:
        respuesta = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_API_KEY
            },
            timeout=15.0
        )

        if respuesta.status_code != 200:
            print(
                "ERROR SUPABASE AUTH:",
                respuesta.status_code,
                respuesta.text[:300]
            )

            raise HTTPException(
                status_code=401,
                detail="Sesion invalida o expirada"
            )

        usuario = respuesta.json()

        if not usuario.get("id"):
            raise HTTPException(
                status_code=401,
                detail="Supabase no devolvio un usuario valido"
            )

        return usuario

    except httpx.RequestError as error:
        print("ERROR DE CONEXION CON SUPABASE:", str(error))

        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con Supabase Auth"
        )

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Supabase devolvio una respuesta invalida"
        )


# Verificar que el usuario sea administrador
def verificar_administrador(
    usuario: dict = Depends(obtener_usuario_actual)
):
    admin_ids = set()

    ids_configurados = os.getenv("ADMIN_USER_IDS", "")

    admin_ids.update(
        identificador.strip()
        for identificador in ids_configurados.split(",")
        if identificador.strip()
    )

    admin_id_actual = os.getenv("ADMIN_USER_ID", "").strip()

    if admin_id_actual:
        admin_ids.add(admin_id_actual)

    if not admin_ids:
        raise HTTPException(
            status_code=500,
            detail="No hay administradores configurados"
        )

    usuario_id = usuario.get("id")

    if usuario_id not in admin_ids:
        print("ACCESO ADMINISTRATIVO DENEGADO:", usuario_id)

        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador"
        )

    print("ADMINISTRADOR AUTORIZADO:", usuario_id)

    return usuario
