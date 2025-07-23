# file: /api/services/whatsapp_service.py

import requests

from typing import Dict, Optional
from api.config import logger, WHATSAPP_ACCESS_TOKEN

class WhatsAppService:
    @staticmethod
    def send_message(to : str, msg : str, phone_bussines_id : str) -> bool:
        """
        Envía un mensaje de WhatsApp al número proporcionado.
        """
        headers : Dict[str, str] = {'Content-Type': 'application/json', 'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}'}
        
        data : Dict = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": msg
            }
        }
        
        try:
            response : requests.Response = requests.post(f"https://graph.facebook.com/v22.0/{phone_bussines_id}/messages", headers=headers, json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            return False

    @staticmethod
    def download_whatsapp_media(media_id : str) -> Optional[bytes]:
        """
        Descarga un archivo multimedia de WhatsApp usando la API de Graph.
        
        Args:
            media_id: ID del archivo multimedia.
            
        Returns:
            Los bytes del archivo multimedia o None si ocurrió un error.
        """
        try:
            headers : Dict[str, str] = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
            url : str = f"https://graph.facebook.com/v17.0/{media_id}"

            response: requests.Response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Error al obtener la URL del archivo multimedia: {response.text}")
                return None
            
            json_response : Dict = response.json()
            media_url : str = json_response.get("url")
            if not media_url:
                logger.error("No se pudo obtener la URL de descarga del archivo multimedia")
                return None
            
            download_response : requests.Response = requests.get(media_url, headers=headers)
            if download_response.status_code != 200:
                logger.error(f"Error al descargar el archivo multimedia: {download_response.text}")
                return None
            
            return download_response.content
        except Exception as e:
            logger.error(f"Error durante la descarga del archivo multimedia: {str(e)}")
            return None
