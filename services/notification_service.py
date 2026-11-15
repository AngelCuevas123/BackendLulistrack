
from typing import Optional

from firebase_admin import messaging
from sqlalchemy.orm import Session

from models import DriverDeviceDB


def enviar_notificacion_repartidor(
    db: Session,
    driver_id: str,
    titulo: str,
    cuerpo: str,
    datos: Optional[dict] = None
):
    """
    Envía una notificación push a todos los dispositivos
    activos de un repartidor mediante Firebase Installation IDs.
    """

    dispositivos = db.query(DriverDeviceDB).filter(
        DriverDeviceDB.driver_id == driver_id,
        DriverDeviceDB.is_active.is_(True)
    ).all()

    if not dispositivos:
        return {
            "success": True,
            "message": "El repartidor no tiene dispositivos activos",
            "sent": 0,
            "failed": 0
        }

    fids = [
        dispositivo.firebase_installation_id
        for dispositivo in dispositivos
    ]

    # Firebase requiere que los valores del campo data sean strings.
    datos_fcm = {
        str(clave): str(valor)
        for clave, valor in (datos or {}).items()
    }

    enviados = 0
    fallidos = 0
    fids_invalidos = []

    # Firebase permite un máximo de 500 FIDs por envío.
    for inicio in range(0, len(fids), 500):
        lote = fids[inicio:inicio + 500]

        mensaje = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=cuerpo
            ),
            data=datos_fcm,
            fids=lote
        )

        respuesta = messaging.send_each_for_multicast(mensaje)

        enviados += respuesta.success_count
        fallidos += respuesta.failure_count

        # Identificar FIDs que Firebase confirma como no registrados.
        for fid, resultado in zip(lote, respuesta.responses):
            if isinstance(
                resultado.exception,
                messaging.UnregisteredError
            ):
                fids_invalidos.append(fid)

    # Desactivar únicamente los FIDs que Firebase confirma como inválidos.
    if fids_invalidos:
        db.query(DriverDeviceDB).filter(
            DriverDeviceDB.firebase_installation_id.in_(fids_invalidos)
        ).update(
            {DriverDeviceDB.is_active: False},
            synchronize_session=False
        )

        db.commit()

    return {
        "success": True,
        "message": "Proceso de envío finalizado",
        "sent": enviados,
        "failed": fallidos,
        "invalid_fids": len(fids_invalidos)
    }
