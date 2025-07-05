import logging
from typing import Dict, Any, Optional, List

from firebase_admin import firestore

from app.firebase.config import get_firestore_client, SERVER_TIMESTAMP

# Configure logging
logger = logging.getLogger(__name__)

# Get Firestore client
db = get_firestore_client()

# Collection names
MESSAGES_COLLECTION = "messages"
SUMMARIES_COLLECTION = "summaries"
USERS_COLLECTION = "users"

class FirebaseService:
    """Service for handling Firebase Firestore operations."""
    
    @staticmethod
    async def add_message(
        user_id: str,
        content: str,
        role: str = "user",
        quoted_message_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new message to Firestore.
        
        Args:
            user_id: ID of the user sending the message
            content: Message content
            role: 'user' or 'assistant'
            quoted_message_id: Optional ID of the message being quoted
            metadata: Additional metadata to store with the message
            
        Returns:
            str: The ID of the created message
        """
        message_data = {
            "user_id": user_id,
            "content": content,
            "role": role,
            "timestamp": SERVER_TIMESTAMP,
            "quoted_message_id": quoted_message_id,
            "metadata": metadata or {}
        }
        
        try:
            doc_ref = db.collection(MESSAGES_COLLECTION).document()
            doc_ref.set(message_data)
            logger.info(f"Message added with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise
    
    @staticmethod
    async def get_messages(
        user_id: str,
        limit: int = 50,
        start_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve messages for a user.
        
        Args:
            user_id: ID of the user to get messages for
            limit: Maximum number of messages to return
            start_after: Message ID to start after for pagination
            
        Returns:
            List of message dictionaries
        """
        try:
            query = (
                db.collection(MESSAGES_COLLECTION)
                .where("user_id", "==", user_id)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            if start_after:
                start_doc = db.collection(MESSAGES_COLLECTION).document(start_after).get()
                if start_doc.exists:
                    query = query.start_after(start_doc)
            
            messages = []
            for doc in query.stream():
                message = doc.to_dict()
                message["id"] = doc.id
                # Convert Firestore timestamp to ISO format
                if "timestamp" in message and hasattr(message["timestamp"], "isoformat"):
                    message["timestamp"] = message["timestamp"].isoformat()
                messages.append(message)
                
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving messages: {str(e)}")
            raise
    
    @staticmethod
    async def get_message(message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID."""
        try:
            doc = db.collection(MESSAGES_COLLECTION).document(message_id).get()
            if doc.exists:
                message = doc.to_dict()
                message["id"] = doc.id
                return message
            return None
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {str(e)}")
            raise
    
    @staticmethod
    async def add_summary(
        user_id: str,
        summary_text: str,
        message_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new summary to Firestore.
        
        Args:
            user_id: ID of the user the summary is for
            summary_text: The summary text
            message_ids: List of message IDs included in this summary
            metadata: Additional metadata
            
        Returns:
            str: The ID of the created summary
        """
        summary_data = {
            "user_id": user_id,
            "summary_text": summary_text,
            "message_ids": message_ids,
            "timestamp": SERVER_TIMESTAMP,
            "metadata": metadata or {}
        }
        
        try:
            doc_ref = db.collection(SUMMARIES_COLLECTION).document()
            doc_ref.set(summary_data)
            logger.info(f"Summary added with ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding summary: {str(e)}")
            raise
    
    @staticmethod
    async def get_summaries(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summaries for a user."""
        try:
            query = (
                db.collection(SUMMARIES_COLLECTION)
                .where("user_id", "==", user_id)
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            summaries = []
            for doc in query.stream():
                summary = doc.to_dict()
                summary["id"] = doc.id
                if "timestamp" in summary and hasattr(summary["timestamp"], "isoformat"):
                    summary["timestamp"] = summary["timestamp"].isoformat()
                summaries.append(summary)
                
            return summaries
            
        except Exception as e:
            logger.error(f"Error retrieving summaries: {str(e)}")
            raise