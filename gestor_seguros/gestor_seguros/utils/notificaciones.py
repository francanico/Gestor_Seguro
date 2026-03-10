# gestor_seguros/utils/notificaciones.py
import logging

logger = logging.getLogger(__name__)

def enviar_notificacion_base(cliente, mensaje, canal='EMAIL'):
    """
    Función base para envío de notificaciones.
    Canales soportados futuro: 'EMAIL', 'WHATSAPP'
    """
    logger.info(f"PRE-ENVÍO: Notificación para {cliente.nombre_completo} vía {canal}: {mensaje}")
    # Aquí se integrará en el futuro el envío real vía SendGrid o Twilio
    return True

def notificar_renovacion_proxima(poliza):
    mensaje = f"Hola {poliza.cliente.nombre_completo}, su póliza {poliza.numero_poliza} vence el {poliza.fecha_fin_vigencia}. ¿Desea renovarla?"
    return enviar_notificacion_base(poliza.cliente, mensaje)
