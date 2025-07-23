# api.models.WhatsAppMedia.py

from datetime import datetime
from typing import Dict, Optional, Any
from api.services.firestore_service import FirestoreService
from api.config import logger

# Constante para la colección en Firestore
COLLECTION_WHATSAPP_MEDIA = "whatsapp_media"

class WhatsAppMedia:
    def __init__(self, media_id: str = None, user_id: Optional[str] = None, 
                 phone_number: Optional[str] = None, media_type: str = None, 
                 storage_path: Optional[str] = None, content_type: Optional[str] = None,
                 file_name: Optional[str] = None, ocr_text: Optional[str] = None, 
                 description: Optional[str] = None, transcription: Optional[str] = None,
                 created_at: datetime = None, sha256: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Inicializa un objeto WhatsAppMedia para representar un archivo multimedia.
        
        Args:
            media_id: ID del medio proporcionado por WhatsApp
            user_id: ID del usuario asociado al medio
            phone_number: Número de teléfono que envió el medio
            media_type: Tipo de medio (image, audio, video, document)
            storage_path: Ruta en Google Cloud Storage
            content_type: Tipo MIME del archivo
            file_name: Nombre del archivo
            ocr_text: Texto extraído mediante OCR (para imágenes y documentos)
            description: Descripción generada por IA del contenido
            transcription: Transcripción de audio a texto (para audio y video)
            created_at: Fecha y hora de creación
            sha256: Hash SHA-256 del archivo proporcionado por WhatsApp
            metadata: Metadatos adicionales proporcionados por WhatsApp
        """
        self.media_id = media_id
        self.user_id = user_id
        self.phone_number = phone_number
        self.media_type = media_type
        self.storage_path = storage_path
        self.content_type = content_type
        self.file_name = file_name
        self.ocr_text = ocr_text
        self.description = description
        self.transcription = transcription
        self.created_at = created_at or datetime.now()
        self.processed = False
        self.sha256 = sha256
        self.metadata = metadata or {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WhatsAppMedia':
        """Crear un objeto WhatsAppMedia desde un diccionario."""
        return cls(
            media_id=data.get('id') or data.get('media_id'),
            user_id=data.get('user_id'),
            phone_number=data.get('phone_number'),
            media_type=data.get('media_type'),
            storage_path=data.get('storage_path'),
            content_type=data.get('content_type'),
            file_name=data.get('file_name'),
            ocr_text=data.get('ocr_text'),
            description=data.get('description'),
            transcription=data.get('transcription'),
            created_at=data.get('created_at'),
            sha256=data.get('sha256'),
            metadata=data.get('metadata')
        )
    
    def to_dict(self) -> Dict:
        """Convertir el objeto a formato para guardar en Firestore."""
        return {
            'media_id': self.media_id,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'media_type': self.media_type,
            'storage_path': self.storage_path,
            'content_type': self.content_type,
            'file_name': self.file_name,
            'ocr_text': self.ocr_text,
            'description': self.description,
            'transcription': self.transcription,
            'created_at': self.created_at,
            'processed': self.processed,
            'sha256': self.sha256,
            'metadata': self.metadata
        }
    
    @classmethod
    def get_by_id(cls, media_id: str) -> Optional['WhatsAppMedia']:
        """Obtener un registro multimedia por su ID."""
        data = FirestoreService.get_document(COLLECTION_WHATSAPP_MEDIA, media_id)
        if data:
            return cls.from_dict(data)
        return None
    
    def save(self) -> 'WhatsAppMedia':
        """Guardar o actualizar el registro multimedia en Firestore."""
        data = self.to_dict()
        FirestoreService.create_document(COLLECTION_WHATSAPP_MEDIA, self.media_id, data)
        return self
    
    def mark_as_processed(self, ocr_text=None, description=None, transcription=None) -> 'WhatsAppMedia':
        """Marcar el medio como procesado y actualizar metadatos."""
        if ocr_text:
            self.ocr_text = ocr_text
        if description:
            self.description = description
        if transcription:
            self.transcription = transcription
        
        self.processed = True
        return self.save()