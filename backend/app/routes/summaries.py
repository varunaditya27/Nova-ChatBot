from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from app.services.firebase_service import FirebaseService
from app.utils.models import SummaryCreate, SummaryResponse

router = APIRouter()


@router.post("/generate", response_model=SummaryResponse, status_code=201)
async def generate_summary(summary_data: SummaryCreate):
    """
    Generate a new summary for a set of messages.
    
    - **summary_text**: The summary text
    - **message_ids**: List of message IDs included in this summary
    - **metadata**: Optional additional data
    - **user_id**: ID of the user this summary is for
    """
    try:
        # Add the summary to Firestore
        summary_id = await FirebaseService.add_summary(
            user_id=summary_data.user_id,
            summary_text=summary_data.summary_text,
            message_ids=summary_data.message_ids,
            metadata=summary_data.metadata,
        )
        
        # Get the created summary to return
        created_summary = await FirebaseService.get_summary(summary_id)
        if not created_summary:
            raise HTTPException(status_code=500, detail="Failed to create summary")
            
        # Get all messages referenced in the summary
        messages = []
        for msg_id in summary_data.message_ids:
            msg = await FirebaseService.get_message(msg_id)
            if msg:
                messages.append(msg)
        
        return {
            **created_summary,
            "messages": messages
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[SummaryResponse])
async def get_summaries(
    user_id: str,
    limit: int = Query(10, gt=0, le=50, description="Number of summaries to return"),
):
    """
    Get summaries for a user, most recent first.
    
    - **user_id**: ID of the user to get summaries for
    - **limit**: Number of summaries to return (1-50, default 10)
    """
    try:
        summaries = await FirebaseService.get_summaries(
            user_id=user_id,
            limit=limit,
        )
        
        # For each summary, fetch its messages
        result = []
        for summary in summaries:
            messages = []
            for msg_id in summary.get("message_ids", []):
                msg = await FirebaseService.get_message(msg_id)
                if msg:
                    messages.append(msg)
            
            result.append({
                **summary,
                "messages": messages
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(summary_id: str):
    """
    Get a specific summary by ID.
    
    - **summary_id**: ID of the summary to retrieve
    """
    try:
        summary = await FirebaseService.get_summary(summary_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
            
        # Get all messages referenced in the summary
        messages = []
        for msg_id in summary.get("message_ids", []):
            msg = await FirebaseService.get_message(msg_id)
            if msg:
                messages.append(msg)
        
        return {
            **summary,
            "messages": messages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))