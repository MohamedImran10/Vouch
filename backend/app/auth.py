"""
Authentication utilities for JWT-based email/password auth.
Handles token creation, validation, and user authentication.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))

# HTTP Bearer token scheme
security = HTTPBearer()


# ============================================================================
# Password Hashing
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Management
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of data to encode in token (should include user_id, email)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict:
    """
    Decode and verify a JWT access token

    Args:
        token: JWT token string

    Returns:
        Dictionary with decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict:
    """
    FastAPI dependency to get current authenticated user from JWT token

    Usage in route:
        @app.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user["user_id"]
            ...

    Args:
        credentials: HTTP Bearer credentials from request header

    Returns:
        Dictionary with user data from token

    Raises:
        HTTPException: If token is missing or invalid
    """
    token = credentials.credentials
    return decode_access_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[Dict]:
    """
    FastAPI dependency to get current user if authenticated, None otherwise
    Useful for endpoints that work with or without authentication

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        Dictionary with user data if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    FastAPI dependency to require admin role

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# ============================================================================
# Helper Functions
# ============================================================================

def create_token_response(user_id: str, email: str, name: str, **extra_data) -> dict:
    """
    Create a complete token response with user data

    Args:
        user_id: User ID
        email: User email
        name: User name
        **extra_data: Additional user data to include

    Returns:
        Dictionary with access_token and user data
    """
    created_at = extra_data.pop("created_at", datetime.utcnow().isoformat())
    updated_at = extra_data.pop("updated_at", created_at)

    token_data = {
        "user_id": user_id,
        "email": email,
        **extra_data
    }

    access_token = create_access_token(token_data)
    expires_in = ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert to seconds

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user_id,
            "email": email,
            "name": name,
            **extra_data,
            "created_at": created_at,
            "updated_at": updated_at,
        }
    }


def get_user_id_from_token(current_user: Dict) -> str:
    """
    Extract user ID from decoded token

    Args:
        current_user: Decoded token data from get_current_user

    Returns:
        User ID string
    """
    return current_user["user_id"]


def check_resource_owner(resource_user_id: str, current_user: Dict) -> bool:
    """
    Check if current user owns a resource

    Args:
        resource_user_id: User ID of resource owner
        current_user: Current authenticated user

    Returns:
        True if current user owns the resource or is admin

    Raises:
        HTTPException: If user doesn't own resource
    """
    user_id = get_user_id_from_token(current_user)
    is_admin = current_user.get("is_admin", False)

    if user_id != resource_user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )

    return True
