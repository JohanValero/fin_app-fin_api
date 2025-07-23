# file: /api/models/WhatsAppMessage.py

from typing import Dict, Optional
from api.services.firestore_service import FirestoreService
from uuid import UUID
from api.config import COLLECTION_WHATSAPP_MESSAGES

class WhatsAppMessage:
    def __init__(self, id : Optional[str] = None, user_id : Optional[str] = None, value : Optional[Dict] = None):
        self.id : Optional[str] = id
        self.user_id : Optional[str] = user_id
        self.value : Optional[Dict] = value
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WhatsAppMessage':
        """Crear un objeto WhatsAppMessage desde un diccionario."""
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            value=data.get('value')
        )
    
    def to_dict(self) -> Dict:
        """Convertir el objeto a formato para guardar en Firestore."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'value': self.value
        }
    
    @classmethod
    def get_by_id(cls, message_id: str) -> Optional['WhatsAppMessage']:
        """Obtener un mensaje por su ID."""
        data = FirestoreService.get_document(COLLECTION_WHATSAPP_MESSAGES, message_id)
        if data:
            return cls.from_dict(data)
        return None
    
    def create(self) -> 'WhatsAppMessage':
        """Guardar el mensaje en Firestore."""
        data : Dict = self.to_dict()

        new_data : Dict = FirestoreService.create_document(COLLECTION_WHATSAPP_MESSAGES, self.id, data)
        if new_data:
            self.id : UUID = new_data.get('id')
            return self.from_dict(new_data)
        
        return self

    def update(self) -> 'WhatsAppMessage':
        """Actualizar el mensaje en Firestore."""
        data : Dict = self.to_dict()
        new_data : Dict = FirestoreService.update_document(COLLECTION_WHATSAPP_MESSAGES, self.id, data)
        return self.from_dict(new_data)

    def save(self) -> 'WhatsAppMessage':
        """Guardar o actualizar el mensaje en Firestore."""
        data : Dict = self.to_dict()

        new_data : Dict = FirestoreService.create_document(COLLECTION_WHATSAPP_MESSAGES, self.id, data)
        if new_data:
            self.id : UUID = new_data.get('id')
            return self.from_dict(new_data)
        
        return self
    
    def update_status(self, status: str) -> 'WhatsAppMessage':
        """Actualizar el estado del mensaje."""
        self.status = status
        return self.save()