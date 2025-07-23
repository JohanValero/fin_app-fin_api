# file: /api/routes/pubsub_chatbot.py

import json
import base64

from typing import Dict, Optional, Tuple, Any, List, Union
from flask import Blueprint, request, jsonify
from api.config import logger
from api.services import WhatsAppService, StorageService, AIServices
from api.models import WhatsAppMedia, WhatsAppMessage

pubsub_chatbot: Blueprint = Blueprint('pubsub_chatbot', __name__)

def process_media(media_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa archivos multimedia utilizando servicios de IA según el tipo de medio.
    
    Args:
        media_data: Datos del archivo multimedia
        
    Returns:
        Dict[str, Any]: Diccionario con los resultados del procesamiento
    """
    # Verificar que los datos esenciales estén presentes
    if not media_data:
        logger.warning("No se proporcionaron datos de media para procesar")
        return {
            "success": False,
            "message": "Datos de media faltantes"
        }
        
    media_id: str = media_data.get('media_id', '')
    if not media_id:
        logger.warning("ID de media no encontrado en los datos proporcionados")
        return {
            "success": False,
            "message": "ID de media no encontrado"
        }
        
    media_type: str = media_data.get('media_type', '')
    storage_path: str = media_data.get('storage_path', '')
    
    # Buscar el registro en Firestore
    whatsapp_media: Optional[WhatsAppMedia] = WhatsAppMedia.get_by_id(media_id)
    
    if not whatsapp_media:
        logger.warning(f"No se encontró registro para el media_id: {media_id}")
        return {
            "success": False,
            "message": "Registro de media no encontrado"
        }
    
    # Valores predeterminados para el resultado
    ocr_text: str = ""
    description: str = ""
    transcription: str = ""
    
    # Recuperar el archivo de Cloud Storage si existe un storage_path
    if storage_path:
        try:
            # Extraer la ruta real del archivo sin el prefijo gs://
            bucket_name: str = ""
            object_path: str = ""
            
            if storage_path.startswith("gs://"):
                # Quitar el prefijo gs:// y dividir por la primera barra después del nombre del bucket
                parts: List[str] = storage_path[5:].split("/", 1)
                if len(parts) == 2:
                    bucket_name, object_path = parts
            
            if bucket_name and object_path:
                # Obtener los bytes del archivo
                success: bool
                file_bytes: Optional[bytes]
                success, file_bytes = StorageService.download_file(bucket_name, object_path)
                
                if success and file_bytes:
                    # Procesar según el tipo de medio
                    if media_type == 'image':
                        # Procesar imagen con OCR
                        ocr_text = AIServices.extract_image_ocr(file_bytes)
                        description = f"Imagen procesada con OCR - {len(ocr_text)} caracteres extraídos"
                    
                    elif media_type == 'document':
                        # Procesar documento (podría usar OCR o procesamiento de documentos)
                        ocr_text = AIServices.extract_image_ocr(file_bytes)
                        description = f"Documento procesado - {len(ocr_text)} caracteres extraídos"
                    
                    elif media_type == 'audio':
                        # Implementar transcripción de audio cuando se active la funcionalidad
                        transcription = "Funcionalidad de transcripción de audio en desarrollo"
                    
                    elif media_type == 'video':
                        # Implementar procesamiento de video cuando se active la funcionalidad
                        transcription = "Funcionalidad de transcripción de video en desarrollo"
                        description = "Análisis de video en desarrollo"
                else:
                    logger.error(f"No se pudo descargar el archivo desde Cloud Storage: {storage_path}")
            else:
                logger.error(f"Formato de ruta de storage inválido: {storage_path}")
        except Exception as e:
            logger.error(f"Error al procesar el archivo multimedia: {str(e)}")
    
    # Actualizar el registro con los resultados del procesamiento
    whatsapp_media.mark_as_processed(ocr_text=ocr_text, description=description, transcription=transcription)
    
    logger.info(f"Procesamiento de IA completado para media_id: {media_id}")
    
    return {
        "success": True,
        "media_id": media_id,
        "ocr_text": ocr_text,
        "description": description,
        "transcription": transcription
    }

def process_ocr_request(context_id: str, client_phone: str, phone_business_id: str) -> Optional[str]:
    """
    Procesa una solicitud de OCR para un mensaje referenciado.
    
    Args:
        context_id: ID del mensaje referenciado
        client_phone: Número de teléfono del cliente
        phone_business_id: ID del número de teléfono de WhatsApp Business
        
    Returns:
        Optional[str]: Mensaje de respuesta o None si no se puede procesar
    """
    try:
        # Obtener el mensaje referenciado
        referenced_message: Optional[WhatsAppMessage] = WhatsAppMessage.get_by_id(context_id)
        
        if not referenced_message:
            logger.warning(f"No se encontró el mensaje referenciado con ID: {context_id}")
            response_message: str = "No se pudo encontrar el mensaje referenciado."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Obtener el valor del mensaje
        message_value: Dict[str, Any] = referenced_message.value
        
        if not message_value:
            logger.warning(f"El mensaje referenciado no tiene valor: {context_id}")
            response_message: str = "El mensaje referenciado no contiene datos válidos."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Extraer los mensajes del valor (primero verificar si estamos en la estructura correcta)
        referenced_message_data: Dict[str, Any] = {}
        message_type: str = ""
        
        # Verificar si el valor ya es un mensaje individual o es una estructura completa
        if 'type' in message_value:
            # El valor ya es un mensaje individual
            referenced_message_data = message_value
            message_type = message_value.get('type', '')
        else:
            # Extraer los mensajes del valor en estructura completa
            messages: List[Dict[str, Any]] = message_value.get('messages', [])
            
            if not messages:
                logger.warning(f"No hay mensajes en el valor: {context_id}")
                response_message: str = "El mensaje referenciado está vacío."
                WhatsAppService.send_message(client_phone, response_message, phone_business_id)
                return response_message
            
            # Obtener el primer mensaje
            referenced_message_data = messages[0]
            message_type = referenced_message_data.get('type', '')
        
        # Verificar si el mensaje es una imagen o documento
        media_id: str = ""
        media_type: str = ""
        
        if message_type == 'image':
            media_id = referenced_message_data.get('image', {}).get('id', '')
            media_type = 'image'
        elif message_type == 'document':
            media_id = referenced_message_data.get('document', {}).get('id', '')
            media_type = 'document'
        else:
            logger.warning(f"El mensaje referenciado no es una imagen o documento: {message_type}")
            response_message: str = "Solo se puede extraer texto de imágenes o documentos."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        if not media_id:
            logger.warning(f"No se encontró ID del medio en el mensaje referenciado")
            response_message: str = "No se pudo identificar el archivo multimedia en el mensaje referenciado."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Buscar el registro de media
        whatsapp_media: Optional[WhatsAppMedia] = WhatsAppMedia.get_by_id(media_id)
        
        if not whatsapp_media:
            logger.warning(f"No se encontró registro para el media_id: {media_id}")
            
            # Intentar descargar el archivo de WhatsApp si no existe en nuestra base de datos
            media_bytes: Optional[bytes] = WhatsAppService.download_whatsapp_media(media_id)
            
            if not media_bytes:
                logger.error(f"No se pudo descargar el archivo multimedia: {media_id}")
                response_message: str = "No se pudo descargar el archivo multimedia para procesamiento OCR."
                WhatsAppService.send_message(client_phone, response_message, phone_business_id)
                return response_message
            
            # Procesar el OCR directamente desde los bytes descargados
            ocr_text: str = AIServices.extract_image_ocr(media_bytes)
            
            response_message: str = "Texto extraído del archivo:\n\n" + (ocr_text or "No se detectó texto en el archivo.")
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Verificar si ya tiene OCR procesado
        if whatsapp_media.ocr_text:
            response_message: str = "Texto extraído del archivo:\n\n" + whatsapp_media.ocr_text
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Si no tiene OCR procesado, procesar el archivo
        storage_path: Optional[str] = whatsapp_media.storage_path
        
        if not storage_path:
            logger.warning(f"El registro de media no tiene ruta de almacenamiento: {media_id}")
            response_message: str = "No se puede procesar el archivo multimedia porque no está almacenado."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Extraer la ruta real del archivo sin el prefijo gs://
        bucket_name: str = ""
        object_path: str = ""
        
        if storage_path.startswith("gs://"):
            # Quitar el prefijo gs:// y dividir por la primera barra después del nombre del bucket
            parts: List[str] = storage_path[5:].split("/", 1)
            if len(parts) == 2:
                bucket_name, object_path = parts
        
        if not (bucket_name and object_path):
            logger.error(f"Formato de ruta de storage inválido: {storage_path}")
            response_message: str = "La ruta de almacenamiento del archivo es inválida."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Obtener los bytes del archivo
        success: bool
        file_bytes: Optional[bytes]
        success, file_bytes = StorageService.download_file(bucket_name, object_path)
        
        if not (success and file_bytes):
            logger.error(f"No se pudo descargar el archivo desde Cloud Storage: {storage_path}")
            response_message: str = "No se pudo acceder al archivo multimedia almacenado."
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
            return response_message
        
        # Procesar el OCR
        ocr_text: str = AIServices.extract_image_ocr(file_bytes)
        
        # Actualizar el registro con el texto OCR
        whatsapp_media.mark_as_processed(ocr_text=ocr_text)
        
        response_message: str = "Texto extraído del archivo:\n\n" + (ocr_text or "No se detectó texto en el archivo.")
        WhatsAppService.send_message(client_phone, response_message, phone_business_id)
        return response_message
        
    except Exception as e:
        logger.error(f"Error al procesar solicitud OCR: {str(e)}")
        response_message: str = "Ocurrió un error al procesar la solicitud de OCR."
        WhatsAppService.send_message(client_phone, response_message, phone_business_id)
        return response_message

@pubsub_chatbot.route('/', methods=['POST'])
def handle_pubsub_message() -> Tuple[Any, int]:
    """
    Maneja los mensajes recibidos desde Pub/Sub para procesar archivos multimedia.
    
    Returns:
        Tuple[Any, int]: Respuesta JSON y código de estado HTTP
    """
    envelope: Dict[str, Any] = request.get_json()
    
    if not envelope:
        return jsonify({"status": "error", "message": "No Pub/Sub message received"}), 400
    if not isinstance(envelope, dict) or 'message' not in envelope:
        return jsonify({"status": "error", "message": "Invalid Pub/Sub message format"}), 400
    
    pubsub_message: Dict[str, Any] = envelope['message']
    if 'data' not in pubsub_message:
        return jsonify({"status": "error", "message": "No data in message"}), 400
        
    try:
        # Decodificar y cargar los datos
        encoded_data: str = pubsub_message['data']
        str_json: str = base64.b64decode(encoded_data).decode('utf-8')
        logger.info(f"PUBSUB - Mensaje recibido: \n\n{str_json}\n\n")

        """Standart implementation:
        {
            "message": {
                "id": "",
                "from": "",
                "type": "",
                "caption": "", // Text or caption
                "media_id": ""
            },
            "phone_business_id": "",
            "value": {
                "messaging_product": "",
                "metadata": {
                    "display_phone_number": "",
                    "phone_number_id": ""
                },
                "contacts": [
                    {
                        "profile": {
                            "name": ""
                        },
                        "wa_id": ""
                    }
                ],
                "messages": [
                    {
                        "context": { // Optional
                            "from": "",
                            "id": "" // old Message_id
                        },
                        "from": "CLIENT PHONE",
                        "id": "MESSAGE ID",
                        "timestamp": "",
                        "text | voice | image | etc": {},
                        "type": ""
                    }
                ]
            }
        }
        """
        data: Dict[str, Any] = json.loads(str_json)

        # Extraer datos siguiendo la estructura estándar
        whatsapp_value: Dict[str, Any] = data.get('value', {})
        whatsapp_messages: List[Dict[str, Any]] = whatsapp_value.get('messages', [])
        
        if not whatsapp_messages:
            logger.warning("No hay mensajes en la carga útil de PubSub")
            return jsonify({"status": "error", "message": "No messages found in payload"}), 400
            
        # Obtener el primer mensaje
        whatsapp_message : Dict[str, Any] = whatsapp_messages[0]
        
        # Extraer información básica del mensaje
        message_id: str = whatsapp_message.get('id', '')
        client_phone: str = whatsapp_message.get('from', '')
        message_type: str = whatsapp_message.get('type', '')
        
        # Extraer texto o caption según el tipo de mensaje
        message_text: Optional[str] = None
        media_id: Optional[str] = None
        caption: Optional[str] = None
        
        if message_type == 'text':
            message_text = whatsapp_message.get('text', {}).get('body', '')
        elif message_type == 'image':
            media_id = whatsapp_message.get('image', {}).get('id', '')
            caption = whatsapp_message.get('image', {}).get('caption', '')
        elif message_type == 'document':
            media_id = whatsapp_message.get('document', {}).get('id', '')
            caption = whatsapp_message.get('document', {}).get('caption', '')
        elif message_type == 'video':
            media_id = whatsapp_message.get('video', {}).get('id', '')
            caption = whatsapp_message.get('video', {}).get('caption', '')
        elif message_type == 'audio':
            media_id = whatsapp_message.get('audio', {}).get('id', '')
            caption = whatsapp_message.get('audio', {}).get('caption', '')
            
        # Extraer datos de contexto si existe
        context_data: Optional[Dict[str, Any]] = whatsapp_message.get('context')
        
        # Obtener ID del teléfono de negocios
        metadata: Dict[str, Any] = whatsapp_value.get('metadata', {})
        phone_business_id: str = metadata.get('phone_number_id', '') or data.get('phone_business_id', '')
        
        # Construir información de media si existe
        media_data: Dict[str, Any] = {}
        if media_id:
            media_data = data.get('media', {})
            if not media_data:
                # Si no hay datos de media en el mensaje de PubSub, crear una estructura básica
                media_data = {
                    'media_id': media_id,
                    'media_type': message_type
                }

        # Verificar si es una solicitud de OCR con referencia a un mensaje anterior
        if (message_type == 'text' and 
            message_text and 
            message_text.lower() == 'ocr' and 
            context_data and 
            context_data.get('id')):
            
            context_id: str = context_data.get('id')
            logger.info(f"Procesando solicitud OCR para mensaje referenciado: {context_id}")
            
            # Procesar la solicitud OCR
            process_ocr_request(context_id, client_phone, phone_business_id)
            return jsonify({"status": "ok"}), 200
            
        # Verificar si hay media para procesar
        media_processing_result: Dict[str, Any] = {}
        if media_id:
            logger.info(f"Procesando archivo multimedia: {media_id}")
            
            # Si ya tenemos datos de media desde la estructura WhatsApp
            if media_data and 'media_id' in media_data:
                media_processing_result = process_media(media_data)
            else:
                # Crear estructura de datos básica para el procesamiento
                basic_media_data: Dict[str, Any] = {
                    'media_id': media_id,
                    'media_type': message_type
                }
                media_processing_result = process_media(basic_media_data)
            
            # Construir mensaje de respuesta incluyendo detalles del procesamiento
            response_message: str = f"Se ha recibido tu mensaje: {caption or ''}\n\n"
            
            if media_processing_result.get('success', False):
                media_type_for_response: str = message_type
                
                if media_type_for_response == 'image':
                    response_message += "Análisis de la imagen:\n"
                    if media_processing_result.get('ocr_text'):
                        # Truncar texto OCR si es muy largo
                        ocr_text: str = media_processing_result.get('ocr_text', '')
                        truncated_text: str = ocr_text[:100] + "..." if len(ocr_text) > 100 else ocr_text
                        response_message += f"- Texto detectado: {truncated_text}\n"
                    if media_processing_result.get('description'):
                        response_message += f"- Descripción: {media_processing_result.get('description')}\n"
                
                elif media_type_for_response == 'document':
                    response_message += "Análisis del documento:\n"
                    if media_processing_result.get('ocr_text'):
                        # Truncar texto OCR si es muy largo
                        ocr_text: str = media_processing_result.get('ocr_text', '')
                        truncated_text: str = ocr_text[:100] + "..." if len(ocr_text) > 100 else ocr_text
                        response_message += f"- Texto extraído: {truncated_text}\n"
                
                elif media_type_for_response in ['audio', 'video']:
                    response_message += f"Análisis del {media_type_for_response}:\n"
                    if media_processing_result.get('transcription'):
                        response_message += f"- Transcripción: {media_processing_result.get('transcription')}\n"
                    if media_processing_result.get('description') and media_type_for_response == 'video':
                        response_message += f"- Descripción: {media_processing_result.get('description')}\n"
            else:
                # Error en el procesamiento del media
                response_message += f"No se pudo procesar el archivo multimedia. {media_processing_result.get('message', '')}"
        else:
            # Respuesta estándar si no hay multimedia
            response_message: str = f"Se ha recibido tu mensaje: {message_text or caption or ''}"
        
        # Enviar respuesta al usuario
        if client_phone and phone_business_id:
            WhatsAppService.send_message(client_phone, response_message, phone_business_id)
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error procesando mensaje: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500