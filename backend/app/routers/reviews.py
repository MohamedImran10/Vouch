"""
Review Management Routes
Handles review CRUD operations and ratings
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
from datetime import datetime

from app.models import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    MessageResponse
)
from app.auth import get_current_user, get_user_id_from_token, check_resource_owner
from app.firebase_service import FirebaseService

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# Initialize Firebase service
firebase_service = FirebaseService()


@router.get("", response_model=List[ReviewResponse])
async def list_reviews(
    provider_id: Optional[str] = Query(None, description="Filter by provider"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """
    List reviews with optional filtering

    - Filter by provider
    - Filter by user
    - Pagination support
    """
    try:
        # For now, return provider reviews if provider_id is specified
        if provider_id:
            reviews = firebase_service.get_provider_reviews(provider_id)
        else:
            reviews = []

        # Enhance with user names
        enhanced_reviews = []
        for review in reviews[:limit]:
            user = firebase_service.get_user(review.get("user_id", ""))
            enhanced_reviews.append(
                ReviewResponse(
                    id=review["id"],
                    user_id=review["user_id"],
                    provider_id=review["provider_id"],
                    rating=review["rating"],
                    comment=review["comment"],
                    user_name=user.get("name") if user else None,
                    created_at=review.get("created_at", ""),
                    updated_at=review.get("updated_at", "")
                )
            )

        return enhanced_reviews

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reviews: {str(e)}"
        )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new review for a provider

    Requires: JWT token
    """
    try:
        user_id = get_user_id_from_token(current_user)

        # Check if provider exists
        provider = firebase_service.get_provider_details(review_data.provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )

        # Check if user already reviewed this provider
        existing_reviews = firebase_service.get_provider_reviews(review_data.provider_id)
        for review in existing_reviews:
            if review.get("user_id") == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already reviewed this provider. Use PUT to update your review."
                )

        # Create review
        review_id = firebase_service.create_review({
            "user_id": user_id,
            "provider_id": review_data.provider_id,
            "rating": review_data.rating,
            "comment": review_data.comment,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Get created review
        review = firebase_service.get_review(review_id)
        user = firebase_service.get_user(user_id)

        return ReviewResponse(
            id=review["id"],
            user_id=review["user_id"],
            provider_id=review["provider_id"],
            rating=review["rating"],
            comment=review["comment"],
            user_name=user.get("name") if user else None,
            created_at=review.get("created_at", ""),
            updated_at=review.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}"
        )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str):
    """
    Get review details by ID
    """
    try:
        review = firebase_service.get_review(review_id)

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        # Get user name
        user = firebase_service.get_user(review["user_id"])

        return ReviewResponse(
            id=review["id"],
            user_id=review["user_id"],
            provider_id=review["provider_id"],
            rating=review["rating"],
            comment=review["comment"],
            user_name=user.get("name") if user else None,
            created_at=review.get("created_at", ""),
            updated_at=review.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review: {str(e)}"
        )


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    updates: ReviewUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update a review (only owner can update)

    Requires: JWT token
    """
    try:
        # Get review
        review = firebase_service.get_review(review_id)

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        # Check ownership
        check_resource_owner(review["user_id"], current_user)

        # Prepare updates (only non-None values)
        update_data = {}
        if updates.rating is not None:
            update_data["rating"] = updates.rating
        if updates.comment is not None:
            update_data["comment"] = updates.comment

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update review
        success = firebase_service.update_review(review_id, update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update review"
            )

        # Return updated review
        updated_review = firebase_service.get_review(review_id)
        user = firebase_service.get_user(updated_review["user_id"])

        return ReviewResponse(
            id=updated_review["id"],
            user_id=updated_review["user_id"],
            provider_id=updated_review["provider_id"],
            rating=updated_review["rating"],
            comment=updated_review["comment"],
            user_name=user.get("name") if user else None,
            created_at=updated_review.get("created_at", ""),
            updated_at=updated_review.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update review: {str(e)}"
        )


@router.delete("/{review_id}", response_model=MessageResponse)
async def delete_review(
    review_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a review (only owner can delete)

    Requires: JWT token
    """
    try:
        # Get review
        review = firebase_service.get_review(review_id)

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        # Check ownership
        check_resource_owner(review["user_id"], current_user)

        # Delete review
        success = firebase_service.delete_review(review_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete review"
            )

        return MessageResponse(
            message="Review deleted successfully",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete review: {str(e)}"
        )
