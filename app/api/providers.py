"""
Provider Routes - Provider-specific functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List
import logging

from app.database import get_db
from app.models.provider import Provider, ProviderVerification
from app.schemas.provider import ProviderLocationUpdate, ProviderAvailabilityUpdate
from app.schemas.job import JobCardResponse
from app.services.matching_service import get_matching_service
from app.ai import get_ocr_processor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/nearby-jobs/{provider_id}", response_model=List[JobCardResponse])
async def get_nearby_jobs(
    provider_id: int,
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Get nearby jobs for provider (Tinder-style card stack)
    
    Returns jobs sorted by distance, filtered by:
    - Provider's skills/job_types
    - Distance (within radius)
    - Status (pending only)
    - Not expired
    """
    matching_service = get_matching_service(db)
    
    job_cards = await matching_service.get_nearby_jobs_for_provider(
        provider_id=provider_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit
    )
    
    return job_cards


@router.post("/{provider_id}/location", status_code=status.HTTP_200_OK)
async def update_provider_location(
    provider_id: int,
    location: ProviderLocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update provider's current location"""
    provider = await db.get(Provider, provider_id)
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    # Update location using raw SQL (PostGIS)
    update_query = text("""
        UPDATE providers
        SET current_location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        WHERE id = :provider_id
    """)
    
    await db.execute(
        update_query,
        {
            "lon": location.longitude,
            "lat": location.latitude,
            "provider_id": provider_id
        }
    )
    await db.commit()
    
    return {"message": "Location updated successfully"}


@router.post("/{provider_id}/availability", status_code=status.HTTP_200_OK)
async def update_availability(
    provider_id: int,
    availability: ProviderAvailabilityUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update provider's availability status"""
    provider = await db.get(Provider, provider_id)
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    provider.is_available = availability.is_available
    await db.commit()
    
    return {"message": "Availability updated successfully"}


@router.post("/{provider_id}/verification/upload", status_code=status.HTTP_201_CREATED)
async def upload_verification_document(
    provider_id: int,
    document_type: str = Form(...),  # "id", "license", "insurance", "certification"
    document: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload verification document for OCR processing
    
    The system will:
    1. Save the document
    2. Extract text using OCR
    3. Parse relevant information
    4. Store for admin review
    """
    try:
        # Verify provider exists
        provider = await db.get(Provider, provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found"
            )
        
        # Save document (in production, upload to S3)
        document_path = f"/tmp/verification_{provider_id}_{document_type}.jpg"
        with open(document_path, "wb") as f:
            f.write(await document.read())
        
        # Process with OCR
        ocr_processor = get_ocr_processor()
        extracted_data = await ocr_processor.process_document(
            document_path,
            document_type
        )
        
        # Create verification record
        verification = ProviderVerification(
            provider_id=provider_id,
            document_type=document_type,
            document_url=document_path,  # In production: S3 URL
            extracted_data=extracted_data,
            is_verified=False  # Requires admin approval
        )
        
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        
        return {
            "message": "Document uploaded successfully",
            "verification_id": verification.id,
            "extracted_data": extracted_data
        }
        
    except Exception as e:
        logger.error(f"Error uploading verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{provider_id}/verifications")
async def get_provider_verifications(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all verification documents for a provider"""
    query = select(ProviderVerification).where(
        ProviderVerification.provider_id == provider_id
    )
    result = await db.execute(query)
    verifications = result.scalars().all()
    
    return list(verifications)
