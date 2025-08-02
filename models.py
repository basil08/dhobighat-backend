from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime, timedelta
from typing import Optional, Annotated
from bson import ObjectId


def validate_object_id(v: str) -> ObjectId:
    """Validate and convert string to ObjectId"""
    if not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return ObjectId(v)


# User Models
class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")

    model_config = {
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com"
            }
        }
    }


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User's password (will be hashed)")

    model_config = {
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }
    }


class UserResponse(UserBase):
    id: Annotated[str, Field(alias="_id")] = Field(..., description="MongoDB ObjectId")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    updated_at: datetime = Field(..., description="Timestamp when user was last updated")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }
    }

    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "password": "securepassword123"
            }
        }
    }


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "_id": "507f1f77bcf86cd799439011",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "created_at": "2024-01-15T10:30:00",
                    "updated_at": "2024-01-15T10:30:00"
                }
            }
        }
    }


class TokenData(BaseModel):
    user_id: Optional[str] = None


# Existing Clothing Item Models
class ClothingItemBase(BaseModel):
    name: str = Field(..., description="Name of the clothing item")
    clothingItemType: str = Field(..., description="Type of clothing item (e.g., shirt, pants, socks, jacket)")
    image: str = Field(..., description="URL or base64 encoded image of the clothing item")
    last_cleaned: datetime = Field(..., description="Timestamp when the item was last cleaned")
    cleaning_interval_seconds: int = Field(..., description="Time interval between cleanings in seconds")
    is_archived: bool = Field(default=False, description="Whether the clothing item is archived")

    model_config = {
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "name": "Blue T-Shirt",
                "clothingItemType": "shirt",
                "image": "https://example.com/image.jpg",
                "last_cleaned": "2024-01-15T10:30:00",
                "cleaning_interval_seconds": 604800,  # 7 days in seconds
                "is_archived": False
            }
        }
    }


class ClothingItemCreate(ClothingItemBase):
    pass


class ClothingItemResponse(ClothingItemBase):
    id: Annotated[str, Field(alias="_id")] = Field(..., description="MongoDB ObjectId")
    next_cleaning_date: datetime = Field(..., description="Calculated next cleaning date")

    model_config = {
        "populate_by_name": True,
        "json_encoders": {ObjectId: str},
        "json_schema_extra": {
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "name": "Blue T-Shirt",
                "clothingItemType": "shirt",
                "image": "https://example.com/image.jpg",
                "last_cleaned": "2024-01-15T10:30:00",
                "cleaning_interval_seconds": 604800,
                "next_cleaning_date": "2024-01-22T10:30:00",
                "is_archived": False
            }
        }
    }

    @field_validator('id', mode='before')
    @classmethod
    def validate_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    @field_validator('clothingItemType', mode='before')
    @classmethod
    def validate_clothing_item_type(cls, v):
        # Handle case where the field might be missing or have a different name
        if v is None:
            raise ValueError("clothingItemType is required")
        return v 