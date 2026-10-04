"""
Vouch Management Routes
Handles vouch CRUD operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
from datetime import datetime

from app.models import (
    VouchCreate,
    VouchUpdate,
    VouchResponse,
    MessageResponse
)
from app.auth import get_current_user, get_user_id_from_token, get_optional_user
from app.services import firebase_service, graph_engine

router = APIRouter(prefix="/api/vouches", tags=["Vouches"])

@router.post("", response_model=VouchResponse, status_code=status.HTTP_201_CREATED)
async def create_vouch(
    vouch_data: VouchCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new vouch (endorsement)

    Requires: JWT token
    Adds edge to graph and persists to Firebase
    """
    try:
        user_id = get_user_id_from_token(current_user)

        # Check if provider exists
        provider = firebase_service.get_provider_details(vouch_data.to_provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        # Create vouch
        timestamp = datetime.utcnow().isoformat()
        vouch_id = firebase_service.save_vouch({
            "from_user_id": user_id,
            "to_provider_id": vouch_data.to_provider_id,
            "category": vouch_data.category.lower(),
            "message": vouch_data.message,
            "rating": vouch_data.rating,
            "timestamp": timestamp,
            "created_at": timestamp
        })

        # Add to graph engine
        graph_engine.add_edge(
            from_user=user_id,
            to_provider=vouch_data.to_provider_id,
            category=vouch_data.category.lower(),
            timestamp=timestamp
        )

        return VouchResponse(
            id=vouch_id,
            from_user_id=user_id,
            to_provider_id=vouch_data.to_provider_id,
            category=vouch_data.category,
            message=vouch_data.message,
            rating=vouch_data.rating,
            timestamp=timestamp,
            created_at=timestamp
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vouch: {str(e)}"
        )


@router.get("", response_model=List[VouchResponse])
async def list_vouches(
    category: Optional[str] = Query(None, description="Filter by category"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    Read vouches with category/user filtering from Firebase.
    Updates in-memory adjacency via graph_engine.
    """
    try:
        results = firebase_service.load_vouches(category=category, user_id=user_id, limit=limit)
        # Sync to graph engine for real-time adjacency
        for v in results:
            graph_engine.add_edge(
                from_user=v.get("from_user_id", v.get("from_user", "")),
                to_provider=v.get("to_provider_id", v.get("to_provider", "")),
                category=v.get("category", "").lower(),
                timestamp=v.get("timestamp", "")
            )
        # Map to response schema
        responses = []
        for v in results:
            responses.append(VouchResponse(
                id=v.get("id", v.get("vouch_id", "")),
                from_user_id=v.get("from_user_id", v.get("from_user", "")),
                to_provider_id=v.get("to_provider_id", v.get("to_provider", "")),
                category=v.get("category", ""),
                message=v.get("message", ""),
                rating=v.get("rating"),
                timestamp=v.get("timestamp", ""),
                created_at=v.get("created_at", v.get("timestamp", ""))
            ))
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list vouches: {str(e)}")


@router.put("/{vouch_id}", response_model=VouchResponse)
async def update_vouch(
    vouch_id: str,
    vouch_data: VouchUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update an existing vouch (rating/note/provider category). Rebuilds graph edge."""
    try:
        user_id = get_user_id_from_token(current_user)
        # Fetch existing from Firebase
        existing = firebase_service.load_vouch_by_id(vouch_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Vouch not found")
        if existing.get("from_user_id") != user_id and existing.get("from_user") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this vouch")
        # Apply updates
        updated = {
            "id": vouch_id,
            "from_user_id": user_id,
            "to_provider_id": vouch_data.to_provider_id or existing.get("to_provider_id", existing.get("to_provider")),
            "category": (vouch_data.category or existing.get("category", "")).lower(),
            "message": vouch_data.message if vouch_data.message is not None else existing.get("message", ""),
            "rating": vouch_data.rating if vouch_data.rating is not None else existing.get("rating"),
            "timestamp": existing.get("timestamp", ""),
            "updated_at": __import__("datetime").datetime.utcnow().isoformat()
        }
        if not firebase_service.update_vouch(vouch_id, updated):
            raise HTTPException(status_code=404, detail="Vouch not found")
        # Update graph engine
        from_user = updated["from_user_id"]
        to_provider = updated["to_provider_id"]
        previous_provider = existing.get("to_provider_id", existing.get("to_provider"))
        if previous_provider:
            graph_engine.remove_edge(from_user, previous_provider)
        graph_engine.add_edge(
            from_user=from_user,
            to_provider=to_provider,
            category=updated["category"],
            timestamp=updated["timestamp"],
        )
        return VouchResponse(
            id=vouch_id,
            from_user_id=from_user,
            to_provider_id=to_provider,
            category=updated["category"],
            message=updated["message"],
            rating=updated.get("rating"),
            timestamp=updated["timestamp"],
            created_at=updated.get("updated_at", updated["timestamp"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vouch: {str(e)}")


@router.delete("/{vouch_id}", response_model=MessageResponse)
async def delete_vouch(
    vouch_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a vouch and remove edge from in-memory graph."""
    try:
        user_id = get_user_id_from_token(current_user)
        existing = firebase_service.load_vouch_by_id(vouch_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Vouch not found")
        if existing.get("from_user_id") != user_id and existing.get("from_user") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this vouch")
        # Remove from Firebase
        if not firebase_service.delete_vouch(vouch_id):
            raise HTTPException(status_code=404, detail="Vouch not found")
        # Remove from graph engine
        from_user = existing.get("from_user_id", existing.get("from_user"))
        to_provider = existing.get("to_provider_id", existing.get("to_provider"))
        if from_user and to_provider:
            graph_engine.remove_edge(from_user, to_provider)
        return MessageResponse(message="Vouch deleted successfully", success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vouch: {str(e)}")


# Legacy endpoint for backward compatibility
@router.post("/legacy", response_model=dict)
async def create_vouch_legacy(
    vouch_data: dict,
    current_user: Optional[Dict] = Depends(get_optional_user)
):
    """
    Legacy vouch endpoint for backward compatibility
    Works with or without authentication
    """
    try:
        from_user = vouch_data.get("from_user")
        to_provider = vouch_data.get("to_provider")
        category = vouch_data.get("category")
        timestamp = vouch_data.get("timestamp", datetime.utcnow().isoformat())

        if not all([from_user, to_provider, category]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_user, to_provider, and category are required"
            )

        # Add to graph
        graph_engine.add_edge(
            from_user=from_user,
            to_provider=to_provider,
            category=category.lower(),
            timestamp=timestamp
        )

        # Save to Firebase
        vouch_id = firebase_service.save_vouch({
            "from_user_id": from_user,
            "to_provider_id": to_provider,
            "category": category.lower(),
            "timestamp": timestamp,
            "created_at": timestamp
        })

        return {
            "status": "success",
            "vouch_id": vouch_id,
            "message": "Vouch added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vouch: {str(e)}"
        )
