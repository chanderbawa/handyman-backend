"""
Job Routes - Core job creation and management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.database import get_db
from app.schemas.job import JobCreate, JobResponse, JobAcceptRequest
from app.services.job_service import JobService, get_job_service
from app.services.matching_service import MatchingService, get_matching_service
from app.ai import get_image_analyzer, get_job_parser, get_pricing_agent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=List[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_job(
    location_id: int = Form(...),
    description: str = Form(...),
    user_id: int = Form(...),  # In production, extract from JWT token
    images: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Create one or more jobs from a text description
    
    The LLM will parse the description and create appropriate job tickets.
    If images are provided, computer vision will analyze them for pricing.
    
    Example:
        POST /jobs/create
        Form data:
        - location_id: 1
        - description: "My driveway needs snow removal and the fence gate is broken"
        - user_id: 123
        - images: [file1.jpg, file2.jpg]
    """
    try:
        # Save uploaded images (in production, upload to S3)
        image_paths = []
        if images:
            for i, image in enumerate(images):
                # For MVP, save locally. In production, upload to S3
                image_path = f"/tmp/job_image_{user_id}_{i}.jpg"
                with open(image_path, "wb") as f:
                    f.write(await image.read())
                image_paths.append(image_path)
        
        # Get AI services
        image_analyzer = get_image_analyzer()
        job_parser = get_job_parser()
        pricing_agent = get_pricing_agent()
        
        # Create job service
        job_service = get_job_service(db, image_analyzer, job_parser, pricing_agent)
        
        # Create jobs
        jobs = await job_service.create_job_from_text(
            user_id=user_id,
            location_id=location_id,
            description=description,
            image_paths=image_paths if image_paths else None
        )
        
        # TODO: Broadcast to nearby providers via WebSocket
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user/{user_id}", response_model=List[JobResponse])
async def get_user_jobs(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all jobs for a user"""
    image_analyzer = get_image_analyzer()
    job_parser = get_job_parser()
    pricing_agent = get_pricing_agent()
    
    job_service = get_job_service(db, image_analyzer, job_parser, pricing_agent)
    jobs = await job_service.get_user_jobs(user_id)
    
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific job by ID"""
    image_analyzer = get_image_analyzer()
    job_parser = get_job_parser()
    pricing_agent = get_pricing_agent()
    
    job_service = get_job_service(db, image_analyzer, job_parser, pricing_agent)
    job = await job_service.get_job_by_id(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.post("/accept", status_code=status.HTTP_200_OK)
async def accept_job(
    request: JobAcceptRequest,
    provider_id: int = Form(...),  # In production, extract from JWT
    db: AsyncSession = Depends(get_db)
):
    """
    Provider accepts a job (swipes right)
    
    First-to-claim logic: Only the first provider to accept gets the job.
    Uses atomic transaction to prevent race conditions.
    """
    matching_service = get_matching_service(db)
    
    success = await matching_service.accept_job(
        job_id=request.job_id,
        provider_id=provider_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job already taken or not available"
        )
    
    # TODO: Notify user via WebSocket
    
    return {"message": "Job accepted successfully", "job_id": request.job_id}
