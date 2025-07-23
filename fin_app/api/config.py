# file: /api/config.py

import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

import os

# Canales válidos
VALID_CHANNELS = ['whatsapp']

# Configuración del servidor
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '5000'))

COLLECTION_USERS = os.getenv('COLLECTION_USERS', 'users')
COLLECTION_WHATSAPP_DEVICES = os.getenv('COLLECTION_WHATSAPP_DEVICES', 'whatsapp_devices')
COLLECTION_WHATSAPP_MESSAGES = os.getenv('COLLECTION_WHATSAPP_MESSAGES', 'whatsapp_messages')
COLLECTION_WHATSAPP_MEDIA = os.getenv("COLLECTION_WHATSAPP_MEDIA", "whatsapp_media")

WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

GOOGLE_CLOUD_PROJECT : str = os.getenv('GOOGLE_CLOUD_PROJECT', 'default_project_id')
CLOUD_STORAGE_BUCKET : str = os.getenv('CLOUD_STORAGE_BUCKET', 'default_gcs_bucket')
PUBSUB_TOPIC : str = os.getenv('PUBSUB_TOPIC', 'default_pubsub_topic')

# Configuración de paginación
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

logger.info(f"Host: {HOST}")
logger.info(f"Puerto: {PORT}")
logger.info(f"Canales válidos: {VALID_CHANNELS}")
logger.info(f"Token de acceso de WhatsApp: {WHATSAPP_ACCESS_TOKEN}")
logger.info(f"Token de verificación: {VERIFY_TOKEN}")
logger.info(f"Nombre de la colección de usuarios: {COLLECTION_USERS}")
logger.info(f"Nombre de la colección de dispositivos de WhatsApp: {COLLECTION_WHATSAPP_DEVICES}")
logger.info(f"Nombre de la colección de mensajes de WhatsApp: {COLLECTION_WHATSAPP_MESSAGES}")
logger.info(f"Tamaño de página por defecto: {DEFAULT_PAGE_SIZE}")
logger.info(f"Tamaño máximo de página: {MAX_PAGE_SIZE}")
logger.info(f"Proyecto de Google Cloud: {GOOGLE_CLOUD_PROJECT}")
logger.info(f"Tema de Pub/Sub: {PUBSUB_TOPIC}")
logger.info("Configuración de paginación cargada correctamente.")