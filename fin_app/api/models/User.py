# file: /api/models/User.py

import datetime as dt
from typing import Dict, Optional
from uuid import UUID, uuid4

from api.services.firestore_service import FirestoreService
from api.config import COLLECTION_USERS

class User:
    def __init__(self, id: str = None, name: str = None, email: str = None, pin: str = None, created_at: dt.datetime = None):
        self.id = id
        self.name = name
        self.email = email
        self.pin = pin
        self.created_at = created_at or dt.datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Crear un objeto User desde un diccionario de Firestore."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            email=data.get('email'),
            pin=data.get('pin'),
            created_at=data.get('createdAt')
        )
    
    def to_dict(self) -> Dict:
        """Convertir el objeto a formato para guardar en Firestore."""
        return {
            'name': self.name,
            'email': self.email,
            'pin': self.pin,
            'createdAt': self.created_at
        }
    
    @classmethod
    def get_by_id(cls, user_id: str) -> Optional['User']:
        """Obtener un usuario por su ID."""
        data : Dict = FirestoreService.get_document(COLLECTION_USERS, user_id)
        if data:
            return cls.from_dict(data)
        return None
    
    def save(self) -> 'User':
        """Guardar o actualizar el usuario en Firestore."""
        data = self.to_dict()
        
        if self.id:
            # Actualizar usuario existente
            updated_data = FirestoreService.update_document(COLLECTION_USERS, self.id, data)
            if updated_data:
                return self.from_dict(updated_data)
        else:
            # Crear nuevo usuario
            new_id : UUID = str(uuid4())
            user_data : Dict = FirestoreService.create_document(COLLECTION_USERS, new_id, data)
            self.id : UUID = new_id
            return self
        
        return self
    
    def verify_pin(self, pin : str) -> bool:
        """Verificar si el PIN proporcionado coincide con el del usuario."""
        return self.pin == pin