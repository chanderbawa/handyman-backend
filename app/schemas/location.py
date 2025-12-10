from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LocationCreate(BaseModel):
    user_id: int
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    latitude: float = Field(default=0.0, ge=-90, le=90)
    longitude: float = Field(default=0.0, ge=-180, le=180)
    is_primary: bool = False
    nickname: Optional[str] = None


class LocationResponse(BaseModel):
    id: int
    user_id: int
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    zip_code: str
    country: str
    is_primary: bool
    nickname: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
