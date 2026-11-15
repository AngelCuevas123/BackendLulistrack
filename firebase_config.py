
import os
import firebase_admin

from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv()

_firebase_app = None


def inicializar_firebase():
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    ruta_credenciales = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if not ruta_credenciales:
        raise RuntimeError(
            "No se configuró FIREBASE_CREDENTIALS_PATH"
        )

    if not os.path.isfile(ruta_credenciales):
        raise FileNotFoundError(
            "No se encontró el archivo de credenciales de Firebase"
        )

    credencial = credentials.Certificate(ruta_credenciales)

    _firebase_app = firebase_admin.initialize_app(credencial)

    return _firebase_app
