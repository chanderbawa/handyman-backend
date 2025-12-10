"""
Location Routes - User location/property management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List

from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationResponse

router = APIRouter()


@router.post("/create", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new location for a user"""
    # Extract user_id from location_data instead of separate parameter
    user_id = location_data.user_id
    # Create location with PostGIS point
    create_query = text("""
        INSERT INTO locations (
            user_id, address_line1, address_line2, city, state, zip_code, country,
            coordinates, is_primary, nickname, created_at
        )
        VALUES (
            :user_id, :address_line1, :address_line2, :city, :state, :zip_code, :country,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
            :is_primary, :nickname, NOW()
        )
        RETURNING id
    """)
    
    result = await db.execute(
        create_query,
        {
            "user_id": user_id,
            "address_line1": location_data.address_line1,
            "address_line2": location_data.address_line2,
            "city": location_data.city,
            "state": location_data.state,
            "zip_code": location_data.zip_code,
            "country": location_data.country,
            "lon": location_data.longitude,
            "lat": location_data.latitude,
            "is_primary": location_data.is_primary,
            "nickname": location_data.nickname
        }
    )
    
    location_id = result.scalar_one()
    await db.commit()
    
    # Fetch the created location
    location = await db.get(Location, location_id)
    
    return location


@router.get("/user/{user_id}", response_model=List[LocationResponse])
async def get_user_locations(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all locations for a user"""
    query = select(Location).where(Location.user_id == user_id)
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return list(locations)


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific location"""
    location = await db.get(Location, location_id)
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    return location
