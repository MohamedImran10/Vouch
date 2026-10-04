"""
Provider Management Routes
Handles provider profile CRUD operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
from datetime import datetime

from app.models import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    MessageResponse
)
from app.auth import get_current_user, get_user_id_from_token, check_resource_owner
from app.services import firebase_service

router = APIRouter(prefix="/api/providers", tags=["Providers"])

@router.get("", response_model=List[ProviderResponse])
async def list_providers(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    List all providers with optional filtering

    - Filter by category
    - Pagination support
    """
    try:
        providers = firebase_service.list_providers(category=category, limit=limit)

        return [
            ProviderResponse(
                id=p["id"],
                user_id=p.get("user_id", ""),
                name=p["name"],
                category=p["category"],
                description=p.get("description"),
                phone=p.get("phone"),
                rating=p.get("rating", 0.0),
                review_count=p.get("review_count", 0),
                vouch_count=p.get("vouch_count", 0),
                avatar_url=p.get("avatar_url"),
                services=p.get("services", []),
                created_at=p.get("created_at", ""),
                updated_at=p.get("updated_at", "")
            )
            for p in providers
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new provider profile

    Requires: JWT token
    """
    try:
        user_id = get_user_id_from_token(current_user)

        # Create provider
        provider_id = firebase_service.create_provider({
            "user_id": user_id,
            "name": provider_data.name,
            "category": provider_data.category.lower(),
            "description": provider_data.description,
            "phone": provider_data.phone,
            "avatar_url": provider_data.avatar_url,
            "services": provider_data.services,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Get created provider
        provider = firebase_service.get_provider_details(provider_id)

        return ProviderResponse(
            id=provider["id"],
            user_id=provider["user_id"],
            name=provider["name"],
            category=provider["category"],
            description=provider.get("description"),
            phone=provider.get("phone"),
            rating=provider.get("rating", 0.0),
            review_count=provider.get("review_count", 0),
            vouch_count=provider.get("vouch_count", 0),
            avatar_url=provider.get("avatar_url"),
            services=provider.get("services", []),
            created_at=provider.get("created_at", ""),
            updated_at=provider.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create provider: {str(e)}"
        )


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str):
    """
    Get provider details by ID (public endpoint)
    """
    try:
        provider = firebase_service.get_provider_details(provider_id)

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        return ProviderResponse(
            id=provider["id"],
            user_id=provider.get("user_id", ""),
            name=provider["name"],
            category=provider["category"],
            description=provider.get("description"),
            phone=provider.get("phone"),
            rating=provider.get("rating", 0.0),
            review_count=provider.get("review_count", 0),
            vouch_count=provider.get("vouch_count", 0),
            avatar_url=provider.get("avatar_url"),
            services=provider.get("services", []),
            created_at=provider.get("created_at", ""),
            updated_at=provider.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider: {str(e)}"
        )


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    updates: ProviderUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update provider profile (only owner can update)

    Requires: JWT token
    """
    try:
        # Get provider
        provider = firebase_service.get_provider_details(provider_id)

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        # Check ownership
        check_resource_owner(provider["user_id"], current_user)

        # Prepare updates (only non-None values)
        update_data = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.category is not None:
            update_data["category"] = updates.category.lower()
        if updates.description is not None:
            update_data["description"] = updates.description
        if updates.phone is not None:
            update_data["phone"] = updates.phone
        if updates.avatar_url is not None:
            update_data["avatar_url"] = updates.avatar_url
        if updates.services is not None:
            update_data["services"] = updates.services

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update provider
        success = firebase_service.update_provider(provider_id, update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update provider"
            )

        # Return updated provider
        updated_provider = firebase_service.get_provider_details(provider_id)

        return ProviderResponse(
            id=updated_provider["id"],
            user_id=updated_provider["user_id"],
            name=updated_provider["name"],
            category=updated_provider["category"],
            description=updated_provider.get("description"),
            phone=updated_provider.get("phone"),
            rating=updated_provider.get("rating", 0.0),
            review_count=updated_provider.get("review_count", 0),
            vouch_count=updated_provider.get("vouch_count", 0),
            avatar_url=updated_provider.get("avatar_url"),
            services=updated_provider.get("services", []),
            created_at=updated_provider.get("created_at", ""),
            updated_at=updated_provider.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update provider: {str(e)}"
        )


@router.delete("/{provider_id}", response_model=MessageResponse)
async def delete_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete provider profile (only owner can delete)

    Requires: JWT token
    """
    try:
        # Get provider
        provider = firebase_service.get_provider_details(provider_id)

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        # Check ownership
        check_resource_owner(provider["user_id"], current_user)

        # Delete provider
        success = firebase_service.delete_provider(provider_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete provider"
            )

        return MessageResponse(
            message="Provider deleted successfully",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete provider: {str(e)}"
        )


@router.get("/{provider_id}/reviews")
async def get_provider_reviews(provider_id: str):
    """
    Get all reviews for a provider
    """
    try:
        reviews = firebase_service.get_provider_reviews(provider_id)

        return {
            "provider_id": provider_id,
            "reviews": reviews,
            "count": len(reviews)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reviews: {str(e)}"
        )


@router.get("/{provider_id}/vouches")
async def get_provider_vouches(provider_id: str):
    """
    Get all vouches for a provider
    """
    try:
        # This will be implemented when we enhance vouches
        return {
            "provider_id": provider_id,
            "vouches": [],
            "count": 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vouches: {str(e)}"
        )
