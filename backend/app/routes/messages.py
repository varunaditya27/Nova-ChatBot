from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from app.services.firebase_service import FirebaseService
from app.services.topic_service import topic_service
from app.utils.models import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
    MessageRole,
)
from app.utils.cache_manager import cache_manager

router = APIRouter()
logger = logging.getLogger(__name__)

async def analyze_message_topic(message_id: str, content: str, user_id: str):
    """
    Background task to analyze and assign a topic to a message.
    
    Args:
        message_id: ID of the message to analyze
        content: Text content of the message
        user_id: ID of the user who sent the message
    """
    try:
        # Initialize topic service if needed
        await topic_service.initialize()
        
        # Analyze the message and assign a topic
        topic_id = await topic_service.analyze_message_topic(
            message_id=message_id,
            content=content,
            user_id=user_id,
            threshold=0.3  # Adjust threshold as needed
        )
        
        if topic_id:
            logger.info(f"Assigned topic {topic_id} to message {message_id}")
            
            # Update any topic-related caches
            await cache_manager.invalidate_by_prefix(f"topics:{user_id}")
            
            # Invalidate the user's recent messages cache
            cache_key = cache_manager.get_cache_key("recent_messages", user_id=user_id)
            await cache_manager.delete(cache_key)
            
    except Exception as e:
        logger.error(f"Error in background topic analysis: {str(e)}")
        logger.exception("Full traceback:")

@router.post("/", response_model=MessageResponse, status_code=201)
async def create_message(
    message: MessageCreate,
    background_tasks: BackgroundTasks,
):
    """
    Create a new message and trigger topic analysis in the background.
    
    - **content**: Message content
    - **user_id**: ID of the user sending the message
    - **role**: 'user' or 'assistant' (default: 'user')
    - **quoted_message_id**: Optional ID of a message being quoted
    - **metadata**: Additional metadata as a JSON object
    """
    try:
        # Add message to Firestore without topic_id initially
        message_data = message.dict(exclude_unset=True)
        message_id = await FirebaseService.add_message(
            user_id=message.user_id,
            content=message.content,
            role=message.role,
            quoted_message_id=message.quoted_message_id,
            metadata=message.metadata
        )
        
        # Only analyze topics for user messages (not assistant responses)
        if message.role == "user":
            # Start background task for topic analysis
            background_tasks.add_task(
                analyze_message_topic,
                message_id=message_id,
                content=message.content,
                user_id=message.user_id
            )
        
        # Get the created message to return (with any topic_id if set)
        created_message = await FirebaseService.get_message(message_id)
        if not created_message:
            raise HTTPException(status_code=500, detail="Failed to retrieve created message")
            
        # If there's a quoted message, fetch it
        if created_message.get("quoted_message_id"):
            quoted_message = await FirebaseService.get_message(created_message["quoted_message_id"])
            if quoted_message:
                created_message["quoted_message"] = quoted_message
        
        # Invalidate any relevant caches
        if message.role == "user":
            cache_key = cache_manager.get_cache_key("recent_messages", user_id=message.user_id)
            await cache_manager.delete(cache_key)
            
        return created_message
        
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[MessageResponse])
async def get_messages(
    user_id: str,
    limit: int = Query(50, gt=0, le=100, description="Number of messages to return"),
    start_after: Optional[str] = Query(None, description="Message ID to start after for pagination"),
):
    """
    Get messages for a user, most recent first.
    
    - **user_id**: ID of the user to get messages for
    - **limit**: Number of messages to return (1-100, default 50)
    - **start_after**: Message ID to start after for pagination
    """
    try:
        messages = await FirebaseService.get_messages(
            user_id=user_id,
            limit=limit,
            start_after=start_after,
        )
        
        # Get all quoted messages in a batch
        quoted_message_ids = [
            msg["quoted_message_id"] 
            for msg in messages 
            if msg.get("quoted_message_id")
        ]
        
        quoted_messages = {}
        for msg_id in quoted_message_ids:
            quoted_msg = await FirebaseService.get_message(msg_id)
            if quoted_msg:
                quoted_messages[msg_id] = quoted_msg
        
        # Attach quoted messages to their parent messages
        for msg in messages:
            if msg.get("quoted_message_id") and msg["quoted_message_id"] in quoted_messages:
                msg["quoted_message"] = quoted_messages[msg["quoted_message_id"]]
        
        return messages
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    """
    Get a specific message by ID.
    
    - **message_id**: ID of the message to retrieve
    """
    try:
        message = await FirebaseService.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
            
        # If there's a quoted message, fetch it
        if message.get("quoted_message_id"):
            quoted_message = await FirebaseService.get_message(message["quoted_message_id"])
            if quoted_message:
                message["quoted_message"] = quoted_message
                
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TopicResponse(BaseModel):
    topic_id: str
    message_count: int
    last_updated: str
    keywords: List[str] = []
    messages: List[Dict[str, Any]]

@router.get("/topics/{user_id}", response_model=List[TopicResponse])
async def get_user_topics(user_id: str):
    """
    Get all topics for a user with their associated messages and metadata.
    
    This endpoint is cached to improve performance. The cache is automatically
    invalidated when new messages are added to topics.
    
    - **user_id**: ID of the user to get topics for
    """
    try:
        # Initialize topic service if needed
        await topic_service.initialize()
        
        # Get topics with metadata from the topic service (uses caching)
        topics = await topic_service.get_user_topics(user_id=user_id)
        
        # For each topic, get the most recent messages
        for topic in topics:
            topic_id = topic["id"]
            
            # Get messages for this topic (uses caching)
            messages = await topic_service.get_topic_messages(
                user_id=user_id,
                topic_id=topic_id,
                limit=5  # Only get the 5 most recent messages per topic
            )
            
            # Add messages to the topic
            topic["messages"] = messages
            
            # Ensure we have the latest message count
            topic["message_count"] = len(messages)
            
            # Update last_updated from the most recent message if available
            if messages:
                topic["last_updated"] = max(
                    msg.get("timestamp", "") for msg in messages
                )
        
        # Sort topics by last_updated (newest first)
        topics.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        
        return topics
        
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving topics. Please try again later."
        )