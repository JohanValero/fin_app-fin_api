# file: /api/routes/whatsapp_webhook.py

import json
import random
import string
import mimetypes

from typing import Dict, Optional
from flask import Blueprint, request, jsonify
from api.config import logger, VERIFY_TOKEN
from api.services import WhatsAppService, PubSubService, StorageService
from api.models import WhatsAppDevice, WhatsAppMessage, User, WhatsAppMedia, FlowState

whatsapp_webhook : Blueprint = Blueprint('whatsapp_webhook', __name__)

@whatsapp_webhook.route('/', methods=['GET'])
def verify():
    """
    Endpoint to verify the WhatsApp webhook (required by Meta).
    """
    mode : Optional[str] = request.args.get('hub.mode')
    token : Optional[str] = request.args.get('hub.verify_token')
    challenge : Optional[str] = request.args.get('hub.challenge')
    logger.info(f"Verifying webhook. Mode: {mode}, Token: {token}, Challenge: {challenge}")

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("Webhook verified")
            return challenge, 200
        else:
            logger.warning(f"Verification failed. Token: {token}")
            return jsonify({"success": False}), 403
    
    return jsonify({"success": False}), 400

def generate_pin(length=6) -> str:
    """Generate a random PIN of the specified length."""
    return ''.join(random.choices(string.digits, k=length))

def handle_initial_state(device : WhatsAppDevice, phone_number : str, phone_number_id : str, caption : Optional[str]) -> None:
    """Handle the initial state for a new user."""
    if caption.lower() in ["si", "sí", "yes", "registrar", "registrarme"]:
        device.update_flow_state(FlowState.AWAITING_EMAIL)
        WhatsAppService.send_message(phone_number, "Por favor, proporciona tu correo electrónico para registrarte.", phone_number_id)
    else:
        WhatsAppService.send_message(phone_number, "Estimado usuario, no te tenemos registrado en nuestra aplicación.\n¿Deseas registrarte? Responde 'Si' para continuar.", phone_number_id)

def handle_awaiting_email(device : WhatsAppDevice, phone_number : str, phone_number_id : str, caption : Optional[str]) -> None:
    """Handle the state where we're waiting for the user's email."""
    # Simple email validation
    if '@' in caption and '.' in caption:
        email = caption.strip().lower()
        device.update_context({"email": email})
        device.update_flow_state(FlowState.AWAITING_NAME)
        WhatsAppService.send_message(phone_number, f"Gracias. Ahora, por favor proporciónanos tu nombre completo.", phone_number_id)
    else:
        WhatsAppService.send_message(phone_number, "El correo electrónico proporcionado no parece válido. Por favor, ingresa un correo electrónico válido.", phone_number_id)

def handle_awaiting_name(device : WhatsAppDevice, phone_number : str, phone_number_id : str, caption : Optional[str]) -> None:
    """Handle the state where we're waiting for the user's name."""
    if len(caption.strip()) > 2:
        name : str = caption.strip()
        device.update_context({"name": name})
        
        # Generate a PIN and "send" it to email (just log it for now)
        pin : str = generate_pin()
        email : str = device.context.get("email", "unknown_email")
        logger.info(f"PIN {pin} generated for {email}")
        
        # Store the PIN in the device context
        device.update_context({"pin": pin})
        device.update_flow_state(FlowState.AWAITING_PIN)
        
        WhatsAppService.send_message(phone_number, f"Gracias, {name}. Hemos enviado un PIN de verificación a tu correo electrónico ({email}). Por favor, ingresa ese PIN para completar tu registro.",  phone_number_id)
    else:
        WhatsAppService.send_message(phone_number, "Por favor, proporciona un nombre válido para continuar.", phone_number_id)

def handle_awaiting_pin(device : WhatsAppDevice, phone_number : str, phone_number_id : str, caption : Optional[str]) -> None:
    """Handle the state where we're waiting for the user to enter the PIN."""
    expected_pin = device.context.get("pin")
    if caption.strip() == expected_pin:
        # Create the user
        user = User(name=device.context.get("name", ""), email=device.context.get("email", ""), pin=expected_pin)
        user.save()
        
        # Update the device with the user ID
        device.set_user_id(user.id)
        device.update_flow_state(FlowState.AUTHENTICATED)
        
        WhatsAppService.send_message(phone_number, f"¡Registro exitoso! Bienvenido, {user.name}. Ahora puedes utilizar nuestra aplicación.", phone_number_id)
    else:
        WhatsAppService.send_message(phone_number, "El PIN ingresado no es correcto. Por favor, verifica e inténtalo de nuevo.", phone_number_id)

def handle_authenticated(device : WhatsAppDevice, phone_number : str, phone_number_id : str, caption : Optional[str], message_data : Dict) -> None:
    """Handle interactions with an authenticated user."""
    user = User.get_by_id(device.user_id)
    if not user:
        # User no longer exists, reset device state
        device.update_flow_state(FlowState.INITIAL)
        device.user_id = None
        device.save()
        WhatsAppService.send_message(phone_number, "Parece que tu cuenta ya no existe. ¿Deseas registrarte nuevamente?", phone_number_id)
        return
    
    # Publish message to PubSub for further processing
    PubSubService.publish_message(message_data)

def upload_media(media_id : str, media_bytes : bytes, mime_type : str, message_type : str, user_id : str, phone_number : str, sha256 : str, media_metadata : Dict) -> Dict:
    logger.info(f"Archivo multimedia descargado exitosamente: {media_id}")
    
    # Usar el mime_type proporcionado por WhatsApp
    content_type = mime_type
    
    # Determinar extensión basada en el tipo MIME
    extension = mimetypes.guess_extension(content_type.split(';')[0].strip()) or ""
    if not extension:
        # Asignar extensiones predeterminadas si no se puede determinar
        if message_type == 'image':
            extension = '.jpg'
        elif message_type == 'audio':
            extension = '.ogg' if 'ogg' in content_type else '.mp3'
        elif message_type == 'video':
            extension = '.mp4'
        elif message_type == 'document':
            extension = '.pdf'
    
    # Crear nombre de archivo con extensión
    file_name = f"{message_type}_{media_id}{extension}"
    
    # Subir a Google Cloud Storage
    success, storage_path, _ = StorageService.upload_file(
        media_bytes, media_id, message_type, content_type
    )
    
    if success:
        # Crear el objeto WhatsAppMedia con metadata completa
        whatsapp_media = WhatsAppMedia(
            media_id=media_id,
            user_id=user_id,
            phone_number=phone_number,
            media_type=message_type,
            storage_path=storage_path,
            content_type=content_type,
            file_name=file_name,
            # Los campos de IA se llenarán en el procesamiento de PubSub
            ocr_text="",
            description="",
            transcription=""
        )
        
        # Guardar en Firestore
        whatsapp_media.save()
        
        logger.info(f"Archivo multimedia procesado y almacenado: {storage_path}")
        # Añadir información completa del media al mensaje para PubSub
        return {
            'media_id': media_id,
            'media_type': message_type,
            'storage_path': storage_path,
            'content_type': content_type,
            'file_name': file_name,
            'sha256': sha256,
            'metadata': media_metadata
        }
    else:
        logger.error(f"Error al subir archivo multimedia a GCS: {media_id}")

@whatsapp_webhook.route('/', methods=['POST'])
def webhook():
    """
    Process incoming WhatsApp messages and handle login flow.
    """
    data : Dict = request.json
    try:
        # Parse WhatsApp Cloud API structure
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            return jsonify({"success": True}), 200
        
        logger.info(f"Webhook received: {json.dumps(data)}")
            
        message = messages[0]
        message_id = message.get('id')
        phone_number = message.get('from')
        message_type = message.get('type')
        phone_number_id = value.get('metadata', {}).get('phone_number_id')

        # Extract message content
        caption = ""
        media_id = ""
        mime_type = ""
        sha256 = ""
        media_metadata = {}

        if message_type == 'text':
            caption = message.get('text', {}).get('body', '')
        elif message_type == 'image':
            caption = message.get('image', {}).get('caption', '')
            media_id = message.get('image', {}).get('id', '')
            mime_type = message.get('image', {}).get('mime_type', '')
            sha256 = message.get('image', {}).get('sha256', '')
            media_metadata = message.get('image', {})
        elif message_type == 'video':
            caption = message.get('video', {}).get('caption', '')
            media_id = message.get('video', {}).get('id', '')
            mime_type = message.get('video', {}).get('mime_type', '')
            sha256 = message.get('video', {}).get('sha256', '')
            media_metadata = message.get('video', {})
        elif message_type == 'audio':
            caption = message.get('audio', {}).get('caption', '')
            media_id = message.get('audio', {}).get('id', '')
            mime_type = message.get('audio', {}).get('mime_type', '')
            sha256 = message.get('audio', {}).get('sha256', '')
            media_metadata = message.get('audio', {})
        elif message_type == 'document':
            caption = message.get('document', {}).get('caption', '')
            media_id = message.get('document', {}).get('id', '')
            mime_type = message.get('document', {}).get('mime_type', '')
            sha256 = message.get('document', {}).get('sha256', '')
            media_metadata = message.get('document', {})
        else:
            caption = f"[{message_type} no soportado]"
        
        logger.info(f"Message received from {phone_number}: {caption} - Type: {message_type} - ID: {message_id}")
        
        # Get or create device
        device : WhatsAppDevice = WhatsAppDevice.get_by_phone_number(phone_number)
        if not device:
            device : WhatsAppDevice = WhatsAppDevice(phone_number=phone_number)
            device.save()
        
        # Update last active timestamp
        device.update_last_active()
        
        # Prepare message data for PubSub if needed
        message_data : Dict = {
            'message': {
                'id': message_id,
                'from': phone_number,
                'type': message_type,
                'caption': caption,
                'media_id': media_id
            },
            'value': value,
            'phone_business_id': phone_number_id
        }
        
        # Process media if present
        if media_id:
            # Add media processing here if needed
            media_bytes = WhatsAppService.download_whatsapp_media(media_id)
            
            if media_bytes:
                message_data['media'] = upload_media(media_id, media_bytes, mime_type, message_type, device.user_id, phone_number, sha256, media_metadata)
        
        # Save message to the database
        whatsapp_message : WhatsAppMessage = WhatsAppMessage.from_dict({
            "id": message_id,
            "value": value,
            "user_id": device.user_id
        })
        whatsapp_message.save()
        
        # Handle the message based on the current flow state
        if device.flow_state == FlowState.INITIAL:
            handle_initial_state(device, phone_number, phone_number_id, caption)
        elif device.flow_state == FlowState.AWAITING_EMAIL:
            handle_awaiting_email(device, phone_number, phone_number_id, caption)
        elif device.flow_state == FlowState.AWAITING_NAME:
            handle_awaiting_name(device, phone_number, phone_number_id, caption)
        elif device.flow_state == FlowState.AWAITING_PIN:
            handle_awaiting_pin(device, phone_number, phone_number_id, caption)
        elif device.flow_state == FlowState.AUTHENTICATED:
            handle_authenticated(device, phone_number, phone_number_id, caption, message_data)
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500