from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.job import JobType, JobStatus, SeverityLevel


class JobImageResponse(BaseModel):
    id: int
    image_url: str
    image_type: Optional[str]
    analysis_results: Optional[Dict[str, Any]]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Schema for creating a new job"""
    location_id: int
    title: str
    description: Optional[str] = None
    job_type: Optional[JobType] = None  # Can be auto-determined by LLM
    # User can optionally upload images which will be processed separately


class JobResponse(BaseModel):
    id: int
    user_id: int
    location_id: int
    job_type: JobType
    title: str
    description: Optional[str]
    estimated_square_footage: Optional[float]
    severity: Optional[SeverityLevel]
    ai_confidence: Optional[float]
    estimated_price: float
    surge_multiplier: float
    final_price: float
    status: JobStatus
    expires_at: datetime
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime
    images: List[JobImageResponse] = []
    
    class Config:
        from_attributes = True


class JobCardResponse(BaseModel):
    """Simplified job card for provider's Tinder-style feed"""
    id: int
    title: str
    job_type: JobType
    final_price: float
    distance_km: float
    expires_in_minutes: int
    severity: Optional[SeverityLevel]
    estimated_square_footage: Optional[float]
    location_city: str
    location_state: str
    image_url: Optional[str]  # First image if available
    
    class Config:
        from_attributes = True


class JobAcceptRequest(BaseModel):
    """Provider accepts a job"""
    job_id: int


class JobCompleteRequest(BaseModel):
    """Mark job as completed"""
    job_id: int


class JobImageAnalysis(BaseModel):
    """AI analysis from uploaded image"""
    estimated_square_footage: float
    severity: SeverityLevel
    confidence: float
    detected_objects: List[str]
    metadata: Dict[str, Any]
