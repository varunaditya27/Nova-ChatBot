"""Firebase configuration and initialization."""
import os
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import SERVER_TIMESTAMP
from pydantic import BaseSettings, Field

# Re-export SERVER_TIMESTAMP for easier access
__all__ = ["get_firestore_client", "SERVER_TIMESTAMP", "FirebaseConfig"]

class FirebaseConfig(BaseSettings):
    """Firebase configuration settings."""
    project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    private_key_id: str = Field(..., env="FIREBASE_PRIVATE_KEY_ID")
    private_key: str = Field(..., env="FIREBASE_PRIVATE_KEY")
    client_email: str = Field(..., env="FIREBASE_CLIENT_EMAIL")
    client_id: str = Field(..., env="FIREBASE_CLIENT_ID")
    auth_uri: str = Field("https://accounts.google.com/o/oauth2/auth", env="FIREBASE_AUTH_URI")
    token_uri: str = Field("https://oauth2.googleapis.com/token", env="FIREBASE_TOKEN_URI")
    auth_provider_cert_url: str = Field(
        "https://www.googleapis.com/oauth2/v1/certs",
        env="FIREBASE_AUTH_PROVIDER_CERT_URL"
    )
    client_cert_url: str = Field(
        f"https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
        env="FIREBASE_CLIENT_CERT_URL"
    )

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

def get_firebase_credentials() -> credentials.Certificate:
    """Initialize and return Firebase credentials."""
    config = FirebaseConfig()
    return {
        "type": "service_account",
        "project_id": config.project_id,
        "private_key_id": config.private_key_id,
        "private_key": config.private_key.replace('\\n', '\n'),
        "client_email": config.client_email,
        "client_id": config.client_id,
        "auth_uri": config.auth_uri,
        "token_uri": config.token_uri,
        "auth_provider_x509_cert_url": config.auth_provider_cert_url,
        "client_x509_cert_url": config.client_cert_url,
    }

# Initialize Firebase app
firebase_app = firebase_admin.initialize_app(credentials.Certificate(get_firebase_credentials()))

def get_firestore_client() -> firestore.Client:
    """Get a Firestore client instance.
    
    Returns:
        firestore.Client: Initialized Firestore client
    """
    return firestore.client()
