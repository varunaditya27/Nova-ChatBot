"""Firebase configuration and initialization."""
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP

from app.utils.config import settings

# Re-export SERVER_TIMESTAMP for easier access
__all__ = ["get_firestore_client", "SERVER_TIMESTAMP"]

# Initialize Firebase Admin SDK
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": settings.firebase_project_id,
    "private_key_id": settings.firebase_private_key_id,
    "private_key": settings.firebase_private_key.replace('\\n', '\n'),
    "client_email": settings.firebase_client_email,
    "client_id": settings.firebase_client_id,
    "auth_uri": settings.firebase_auth_uri,
    "token_uri": settings.firebase_token_uri,
    "auth_provider_x509_cert_url": settings.firebase_auth_provider_cert_url,
    "client_x509_cert_url": settings.firebase_client_cert_url,
})

# Initialize Firebase app
firebase_app = firebase_admin.initialize_app(cred)

def get_firestore_client() -> firestore.Client:
    """Get a Firestore client instance.
    
    Returns:
        firestore.Client: Initialized Firestore client
    """
    return firestore.client()
