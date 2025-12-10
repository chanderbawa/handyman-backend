from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from app.models.provider import ProviderStatus


class ProviderCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    phone: str
    job_types: List[str]  # ["snow_removal", "lawn_care"]
    hourly_rate: Optional[float] = None


class ProviderResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str
    status: ProviderStatus
    is_available: bool
    job_types: List[str]
    average_rating: float
    total_jobs: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProviderLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ProviderAvailabilityUpdate(BaseModel):
    is_available: bool


class AuthResponseWithProvider(BaseModel):
    access_token: str
    token_type: str
    user: ProviderResponse
