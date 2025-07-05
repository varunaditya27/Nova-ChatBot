from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.firebase_service import FirebaseService
from app.utils.models import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
    MessageRole,
)

router = APIRouter()


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_message(message: MessageCreate):
    """
    Create a new message.
    
    - **content**: Message content (required)
    - **role**: Sender role (user/assistant/system, defaults to user)
    - **quoted_message_id**: Optional ID of a message being quoted
    - **metadata**: Optional additional data
    """
    try:
        # Add the message to Firestore
        message_id = await FirebaseService.add_message(
            user_id=message.user_id,
            content=message.content,
            role=message.role,
            quoted_message_id=message.quoted_message_id,
            metadata=message.metadata,
        )
        
        # Get the created message to return
        created_message = await FirebaseService.get_message(message_id)
        if not created_message:
            raise HTTPException(status_code=500, detail="Failed to create message")
            
        # If there's a quoted message, fetch it
        quoted_message = None
        if created_message.get("quoted_message_id"):
            quoted_message = await FirebaseService.get_message(created_message["quoted_message_id"])
        
        return {
            **created_message,
            "quoted_message": quoted_message
        }
        
    except Exception as e:
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