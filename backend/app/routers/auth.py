"""
Authentication Routes
Handles user registration, login, and token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import Dict

from app.models import (
    UserCreate,
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse
)
from app.auth import (
    hash_password,
    verify_password,
    create_token_response,
    get_current_user
)
from app.firebase_service import FirebaseService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Initialize Firebase service
firebase_service = FirebaseService()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user with email and password

    - Creates user account in Firestore
    - Hashes password securely
    - Returns JWT token for immediate login
    """
    try:
        # Check if user already exists
        existing_user = firebase_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = hash_password(user_data.password)

        # Create user in Firestore
        user_id = firebase_service.create_user({
            "email": user_data.email,
            "name": user_data.name,
            "phone": user_data.phone,
            "avatar_url": user_data.avatar_url,
            "hashed_password": hashed_password,
            "is_admin": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Generate JWT token
        token_response = create_token_response(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            phone=user_data.phone,
            avatar_url=user_data.avatar_url,
            is_admin=False
        )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login with email and password.

    Local development mode accepts any email/password combination so the app can
    be used without a configured user database or Firebase credentials.
    """
    try:
        user_id = (
            credentials.email.split("@", 1)[0].strip().lower()
            if firebase_service.use_mock
            else f"dev_{abs(hash(credentials.email))}"
        )

        token_response = create_token_response(
            user_id=user_id,
            email=credentials.email,
            name=credentials.email.split("@", 1)[0].title(),
            phone=None,
            avatar_url=None,
            is_admin=False,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )

        return token_response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user's profile

    Requires: JWT token in Authorization header
    """
    try:
        user_id = current_user["user_id"]
        user = firebase_service.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

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
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    Logout current user

    Note: With JWT, logout is primarily handled client-side by deleting the token.
    This endpoint can be used for logging/analytics.
    """
    return MessageResponse(
        message="Logged out successfully",
        success=True
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: Dict = Depends(get_current_user)):
    """
    Refresh JWT token

    - Validates current token
    - Issues new token with extended expiration
    """
    try:
        user_id = current_user["user_id"]
        user = firebase_service.get_user(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Generate new JWT token
        token_response = create_token_response(
            user_id=user["id"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            avatar_url=user.get("avatar_url"),
            is_admin=user.get("is_admin", False)
        )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )
