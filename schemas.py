"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- KYCVerification -> "kycverification" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class AuthUser(BaseModel):
    """
    Users collection schema
    Collection name: "authuser"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")
    wallet_address: Optional[str] = Field(None, description="Connected wallet address")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class KYCVerification(BaseModel):
    """
    KYC submissions
    Collection name: "kycverification"
    """
    user_id: str = Field(..., description="User id string")
    full_name: str = Field(..., description="Legal full name")
    country: str = Field(..., description="Country of residence")
    document_type: str = Field(..., description="Document type (e.g., Passport, ID Card)")
    document_number: str = Field(..., description="Document number")
    address: str = Field(..., description="Residential address")
    status: str = Field("pending", description="KYC status: pending | approved | rejected")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
