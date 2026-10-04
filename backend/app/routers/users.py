"""
User Management Routes
Handles user profile CRUD operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List

from app.models import UserUpdate, UserResponse, MessageResponse
from app.auth import get_current_user, get_user_id_from_token, check_resource_owner
from app.firebase_service import FirebaseService

router = APIRouter(prefix="/api/users", tags=["Users"])

# Initialize Firebase service
firebase_service = FirebaseService()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: str):
    """
    Get user profile by ID (public endpoint)
    """
    try:
        user = firebase_service.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Don't return sensitive data
        return UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            avatar_url=user.get("avatar_url"),
            created_at=user.get("created_at", ""),
            updated_at=user.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_profile(
    user_id: str,
    updates: UserUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update user profile (only owner can update)

    Requires: JWT token
    """
    try:
        # Check ownership
        check_resource_owner(user_id, current_user)

        # Prepare updates (only non-None values)
        update_data = {}
        if updates.name is not None:
            update_data["name"] = updates.name
        if updates.phone is not None:
            update_data["phone"] = updates.phone
        if updates.avatar_url is not None:
            update_data["avatar_url"] = updates.avatar_url

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update user
        success = firebase_service.update_user(user_id, update_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Return updated user
        user = firebase_service.get_user(user_id)
        return UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            avatar_url=user.get("avatar_url"),
            created_at=user.get("created_at", ""),
            updated_at=user.get("updated_at", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user_account(
    user_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete user account (only owner can delete)

    Requires: JWT token
    Note: This is a soft delete in production. Consider archiving instead.
    """
    try:
        # Check ownership
        check_resource_owner(user_id, current_user)

        # Delete user
        success = firebase_service.delete_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return MessageResponse(
            message="User account deleted successfully",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/{user_id}/vouches")
async def get_user_vouches(user_id: str):
    """
    Get all vouches made by a user
    """
    try:
        # This will be implemented when we enhance the vouch system
        # For now, return empty list
        return {
            "user_id": user_id,
            "vouches": [],
            "count": 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user vouches: {str(e)}"
        )


@router.get("/{user_id}/reviews")
async def get_user_reviews(user_id: str):
    """
    Get all reviews written by a user
    """
    try:
        # This will query reviews collection filtered by user_id
        # For now, return empty list
        return {
            "user_id": user_id,
            "reviews": [],
            "count": 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user reviews: {str(e)}"
        )
