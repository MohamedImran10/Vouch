"""
Pydantic models for Vouch API
Defines request/response schemas and data validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ============================================================================
# User Models
# ============================================================================

class UserBase(BaseModel):
    """Base user fields"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User registration request"""
    password: str = Field(..., min_length=8, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        """Ensure password meets security requirements"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """User profile update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User profile response"""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ConnectionBase(BaseModel):
    """Base connection fields for a category-specific contact."""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)


class ConnectionCreate(ConnectionBase):
    """Create a connection entry."""
    pass


class ConnectionUpdate(BaseModel):
    """Update a connection entry."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)


class ConnectionResponse(ConnectionBase):
    """Connection response."""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Provider Models
# ============================================================================

class ProviderBase(BaseModel):
    """Base provider fields"""
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    services: List[str] = Field(default_factory=list)


class ProviderCreate(ProviderBase):
    """Provider creation request"""
    pass


class ProviderUpdate(BaseModel):
    """Provider update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    services: Optional[List[str]] = None


class ProviderResponse(ProviderBase):
    """Provider response"""
    id: str
    user_id: str  # Owner
    rating: float = 0.0
    review_count: int = 0
    vouch_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Vouch Models
# ============================================================================

class VouchBase(BaseModel):
    """Base vouch fields"""
    to_provider_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=50)
    message: Optional[str] = Field(None, max_length=500)
    rating: Optional[int] = Field(None, ge=1, le=5)


class VouchCreate(VouchBase):
    """Vouch creation request"""
    pass


class VouchUpdate(BaseModel):
    """Vouch update request"""
    to_provider_id: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    message: Optional[str] = Field(None, max_length=500)


    rating: Optional[int] = Field(None, ge=1, le=5)


class VouchResponse(VouchBase):
    """Vouch response"""
    id: str
    from_user_id: str
    timestamp: str
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Review Models
# ============================================================================

class ReviewBase(BaseModel):
    """Base review fields"""
    provider_id: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=1, max_length=1000)


class ReviewCreate(ReviewBase):
    """Review creation request"""
    pass


class ReviewUpdate(BaseModel):
    """Review update request"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=1, max_length=1000)


class ReviewResponse(ReviewBase):
    """Review response"""
    id: str
    user_id: str
    user_name: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Auth Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserResponse


# ============================================================================
# Category Models
# ============================================================================

class CategoryBase(BaseModel):
    """Base category fields"""
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = Field(..., min_length=1, max_length=10)
    description: Optional[str] = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    """Category creation request (admin only)"""
    pass


class CategoryUpdate(BaseModel):
    """Category update request (admin only)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, min_length=1, max_length=10)
    description: Optional[str] = Field(None, max_length=500)


class CategoryResponse(CategoryBase):
    """Category response"""
    pass


# ============================================================================
# Common Models
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
