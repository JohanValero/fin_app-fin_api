# file: /api/services/firestore_service.py

import firebase_admin

from firebase_admin import firestore

from google.cloud.firestore_v1.client import Client
from google.cloud.firestore_v1.document import DocumentReference, DocumentSnapshot

from typing import Dict, Optional

from api.config import logger

app = firebase_admin.initialize_app()
db : Client = firestore.client()

def get_firestore_client() -> Client:
    """Obtener el cliente de Firestore."""
    return db

class FirestoreService:
    @staticmethod
    def get_document(collection : str, doc_id : str) -> Optional[Dict]:
        doc_ref : DocumentReference = db.collection(collection).document(doc_id)
        doc : DocumentSnapshot = doc_ref.get()
        
        if not doc.exists:
            return None
        
        return {"id": doc.id, **doc.to_dict()}
    
    @staticmethod
    def exists(collection : str, doc_id : str) -> bool:
        doc_ref : DocumentReference = db.collection(collection).document(doc_id)
        return doc_ref.get().exists
    
    @staticmethod
    def create_document(collection : str, doc_id : str, data : Dict) -> Dict:
        doc_ref : DocumentReference = db.collection(collection).document(doc_id)
        doc_ref.set(data)

        return {"id": doc_id, **data}
    
    @staticmethod
    def update_document(collection : str, doc_id : str, data : Dict) -> Optional[Dict]:
        doc_ref : DocumentReference = db.collection(collection).document(doc_id)
        doc : DocumentSnapshot = doc_ref.get()
        
        if not doc.exists:
            return None
        
        doc_ref.update(data)
        updated_doc : DocumentSnapshot = doc_ref.get()
        return {"id": doc_id, **updated_doc.to_dict()}
    
    @staticmethod
    def delete_document(collection: str, doc_id: str) -> bool:
        doc_ref : DocumentReference = db.collection(collection).document(doc_id)
        doc : DocumentSnapshot = doc_ref.get()

        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True