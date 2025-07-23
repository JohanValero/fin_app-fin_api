# api.services.cloud_storage_service.py

import mimetypes
from datetime import datetime
from typing import Optional, Tuple
from google.cloud import storage
from google.cloud.storage.bucket import Bucket
from google.cloud.storage.blob import Blob
from api.config import logger, GOOGLE_CLOUD_PROJECT, CLOUD_STORAGE_BUCKET

# Inicializar el cliente de Storage
storage_client: storage.Client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
bucket_name: str = CLOUD_STORAGE_BUCKET

# Asegurarse de que existe un bucket para el proyecto
try:
    bucket: Bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        logger.warning(f"El bucket {bucket_name} no existe. Creando...")
        bucket: Bucket = storage_client.create_bucket(bucket_name)
        logger.info(f"Bucket {bucket_name} creado exitosamente.")
    else:
        logger.info(f"Usando bucket existente: {bucket_name}")
except Exception as e:
    logger.error(f"Error al inicializar el bucket de storage: {str(e)}")

class StorageService:
    @staticmethod
    def upload_file(file_bytes: bytes, media_id: str, media_type: str, content_type: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Sube un archivo al bucket de Google Cloud Storage.
        
        Args:
            file_bytes: Bytes del archivo a subir
            media_id: ID del medio
            media_type: Tipo de medio (image, audio, video, document)
            content_type: Tipo MIME del archivo proporcionado por WhatsApp
            
        Returns:
            Tuple[bool, str, str]: Tupla de (éxito, ruta de almacenamiento, tipo de contenido)
        """
        try:
            if not bucket_name:
                logger.error("No se ha configurado CLOUD_STORAGE_BUCKET")
                return False, "", ""
            
            # Usar el content_type proporcionado por WhatsApp o asignar uno predeterminado
            if not content_type:
                content_type = "application/octet-stream"
                
                # Asignar tipo de contenido predeterminado basado en el tipo de media
                if media_type == "image":
                    content_type = "image/jpeg"
                elif media_type == "audio":
                    content_type = "audio/ogg"
                elif media_type == "video":
                    content_type = "video/mp4"
                elif media_type == "document":
                    content_type = "application/pdf"
            
            # Para tipos MIME con parámetros adicionales (como codecs), extraer solo el tipo base
            base_content_type: str = content_type.split(';')[0].strip()
            
            # Determinar extensión basada en el tipo de contenido
            extension: str = mimetypes.guess_extension(base_content_type) or ""
            if not extension and media_type == "image":
                extension = ".jpg"
            elif not extension and media_type == "audio":
                extension = ".ogg" if "ogg" in content_type else ".mp3"
            elif not extension and media_type == "video":
                extension = ".mp4"
            elif not extension and media_type == "document":
                extension = ".pdf"
            
            # Generar fecha para organización de archivos
            current_date: str = datetime.now().strftime("%Y/%m/%d")
            
            # Construir la ruta del archivo en GCS
            storage_path: str = f"whatsapp_media/{media_type}/{current_date}/{media_id}{extension}"
            
            # Obtener el bucket
            bucket: Bucket = storage_client.bucket(bucket_name)
            
            # Crear el objeto blob
            blob: Blob = bucket.blob(storage_path)
            
            # Establecer el tipo de contenido
            blob.content_type = content_type
            
            # Subir el archivo
            blob.upload_from_string(file_bytes, content_type=content_type)
            
            logger.info(f"Archivo subido exitosamente a: gs://{bucket_name}/{storage_path}")
            return True, f"gs://{bucket_name}/{storage_path}", content_type
        except Exception as e:
            logger.error(f"Error al subir archivo a GCS: {str(e)}")
            return False, "", ""
    
    @staticmethod
    def download_file(bucket_name: str, object_path: str) -> Tuple[bool, Optional[bytes]]:
        """
        Descarga un archivo desde Google Cloud Storage.
        
        Args:
            bucket_name: Nombre del bucket
            object_path: Ruta del objeto dentro del bucket
            
        Returns:
            Tuple[bool, Optional[bytes]]: Tupla de (éxito, contenido del archivo en bytes)
        """
        try:
            # Obtener el bucket
            bucket: Bucket = storage_client.bucket(bucket_name)
            
            # Obtener el blob
            blob: Blob = bucket.blob(object_path)
            
            # Verificar si el blob existe
            if not blob.exists():
                logger.error(f"El archivo no existe en GCS: gs://{bucket_name}/{object_path}")
                return False, None
            
            # Descargar el archivo
            file_bytes: bytes = blob.download_as_bytes()
            
            logger.info(f"Archivo descargado exitosamente desde: gs://{bucket_name}/{object_path}")
            return True, file_bytes
        except Exception as e:
            logger.error(f"Error al descargar archivo desde GCS: {str(e)}")
            return False, None
    
    @staticmethod
    def get_public_url(storage_path: str) -> str:
        """
        Obtiene la URL pública para acceder al archivo.
        
        Args:
            storage_path: Ruta de storage del archivo
            
        Returns:
            str: URL pública del archivo
        """
        if not storage_path.startswith("gs://"):
            return ""
        
        # Extraer el bucket y el nombre del objeto
        parts: list[str] = storage_path[5:].split("/", 1)
        if len(parts) != 2:
            return ""
        
        bucket_name, object_name = parts
        
        # Devolver la URL pública
        return f"https://storage.googleapis.com/{bucket_name}/{object_name}"