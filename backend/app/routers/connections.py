"""
Connection Management Routes
Handles category-based connection CRUD operations.
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from app.models import ConnectionCreate, ConnectionUpdate, ConnectionResponse, MessageResponse
from app.firebase_service import FirebaseService

router = APIRouter(prefix="/api/connections", tags=["Connections"])
firebase_service = FirebaseService()


@router.get("", response_model=List[ConnectionResponse])
async def list_connections(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
):
    """List category connections with optional filtering."""
    try:
        connections = firebase_service.list_connections(category=category, limit=limit)

        return [
            ConnectionResponse(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                email=item.get("email"),
                phone=item.get("phone"),
                description=item.get("description"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
            )
            for item in connections
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list connections: {str(e)}",
        )


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(connection_data: ConnectionCreate):
    """Create a category-based connection."""
    try:
        now = datetime.utcnow().isoformat()
        payload = {
            "name": connection_data.name,
            "category": connection_data.category.lower(),
            "email": connection_data.email,
            "phone": connection_data.phone,
            "description": connection_data.description,
            "created_at": now,
            "updated_at": now,
        }

        connection_id = firebase_service.create_connection(payload)
        created = firebase_service.get_connection(connection_id)

        return ConnectionResponse(
            id=created["id"],
            name=created["name"],
            category=created["category"],
            email=created.get("email"),
            phone=created.get("phone"),
            description=created.get("description"),
            created_at=created.get("created_at"),
            updated_at=created.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connection: {str(e)}",
        )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: str):
    """Get a connection by ID."""
    try:
        connection = firebase_service.get_connection(connection_id)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        return ConnectionResponse(
            id=connection["id"],
            name=connection["name"],
            category=connection["category"],
            email=connection.get("email"),
            phone=connection.get("phone"),
            description=connection.get("description"),
            created_at=connection.get("created_at"),
            updated_at=connection.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection: {str(e)}",
        )


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(connection_id: str, updates: ConnectionUpdate):
    """Update a connection entry."""
    try:
        existing = firebase_service.get_connection(connection_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        update_data = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.category is not None:
            update_data["category"] = updates.category.lower()
        if updates.email is not None:
            update_data["email"] = str(updates.email)
        if updates.phone is not None:
            update_data["phone"] = updates.phone
        if updates.description is not None:
            update_data["description"] = updates.description

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        success = firebase_service.update_connection(connection_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update connection",
            )

        updated = firebase_service.get_connection(connection_id)
        return ConnectionResponse(
            id=updated["id"],
            name=updated["name"],
            category=updated["category"],
            email=updated.get("email"),
            phone=updated.get("phone"),
            description=updated.get("description"),
            created_at=updated.get("created_at"),
            updated_at=updated.get("updated_at"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update connection: {str(e)}",
        )


@router.delete("/{connection_id}", response_model=MessageResponse)
async def delete_connection(connection_id: str):
    """Delete a connection entry."""
    try:
        existing = firebase_service.get_connection(connection_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found",
            )

        success = firebase_service.delete_connection(connection_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete connection",
            )

        return MessageResponse(message="Connection deleted successfully", success=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete connection: {str(e)}",
        )
