# file: /api/models/WhatsAppDevice.py

from datetime import datetime
from typing import Dict, Optional, Any
from api.services.firestore_service import FirestoreService
import json

from api.config import COLLECTION_WHATSAPP_DEVICES, logger

# Define flow states as constants
class FlowState:
    INITIAL = "INITIAL"
    AWAITING_EMAIL = "AWAITING_EMAIL"
    AWAITING_NAME = "AWAITING_NAME"
    AWAITING_PIN = "AWAITING_PIN"
    AUTHENTICATED = "AUTHENTICATED"
    GENERAL_INTERACTION = "GENERAL_INTERACTION"

class WhatsAppDevice:
    def __init__(self, phone_number: str = None, user_id: str = None, 
                 last_active: datetime = None, flow_state: str = None, 
                 context: Dict[str, Any] = None
    ):
        self.phone_number = phone_number
        self.user_id = user_id
        self.last_active = last_active or datetime.now()
        self.flow_state = flow_state or FlowState.INITIAL
        self.context = context or {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WhatsAppDevice':
        """Create a WhatsAppDevice object from a dictionary."""
        context_data = data.get('context', {})
        # Handle context conversion from string if stored that way
        if isinstance(context_data, str):
            try:
                context_data = json.loads(context_data)
            except json.JSONDecodeError:
                context_data = {}
                logger.error(f"Failed to parse context data: {data.get('context')}")
        
        return cls(
            phone_number=data.get('phoneNumber'),
            user_id=data.get('userId'),
            last_active=data.get('lastActive'),
            flow_state=data.get('flowState', FlowState.INITIAL),
            context=context_data
        )
    
    def to_dict(self) -> Dict:
        """Convert the object to a format for storing in Firestore."""
        return {
            'userId': self.user_id,
            'phoneNumber': self.phone_number,
            'lastActive': self.last_active,
            'flowState': self.flow_state,
            'context': self.context
        }
    
    @classmethod
    def get_by_phone_number(cls, phone_number: str) -> Optional['WhatsAppDevice']:
        """Get a device by its phone number."""
        data = FirestoreService.get_document(COLLECTION_WHATSAPP_DEVICES, phone_number)
        if data:
            return cls.from_dict(data)
        return None
    
    def save(self) -> 'WhatsAppDevice':
        """Save or update the device in Firestore."""
        data = self.to_dict()
        FirestoreService.create_document(COLLECTION_WHATSAPP_DEVICES, self.phone_number, data)
        return self
    
    def update_last_active(self) -> 'WhatsAppDevice':
        """Update the last time the device was active."""
        self.last_active = datetime.now()
        return self.save()
    
    def update_flow_state(self, new_state: str) -> 'WhatsAppDevice':
        """Update the flow state of the conversation."""
        self.flow_state = new_state
        return self.save()
    
    def update_context(self, updates: Dict[str, Any]) -> 'WhatsAppDevice':
        """Update the context with new key-value pairs."""
        self.context.update(updates)
        return self.save()
    
    def clear_context(self) -> 'WhatsAppDevice':
        """Clear the context data."""
        self.context = {}
        return self.save()
    
    def set_user_id(self, user_id: str) -> 'WhatsAppDevice':
        """Set the user ID after authentication."""
        self.user_id = user_id
        return self.save()
    
    def is_authenticated(self) -> bool:
        """Check if the device is associated with an authenticated user."""
        return self.user_id is not None and self.flow_state == FlowState.AUTHENTICATED