"""
Matching Service - The "Tinder Mechanic"
Handles geospatial queries and job-provider matching
"""
from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_SetSRID, ST_MakePoint
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models.job import Job, JobStatus, JobAssignment
from app.models.provider import Provider, ProviderStatus
from app.models.location import Location
from app.schemas.job import JobCardResponse
from app.config import settings

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service for matching jobs with nearby providers using PostGIS
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.default_radius_m = settings.DEFAULT_SEARCH_RADIUS_KM * 1000  # Convert to meters
    
    async def get_nearby_jobs_for_provider(
        self,
        provider_id: int,
        latitude: float,
        longitude: float,
        radius_km: Optional[float] = None,
        limit: int = 20
    ) -> List[JobCardResponse]:
        """
        Get nearby pending jobs for a provider (Tinder-style card stack)
        
        Args:
            provider_id: Provider's ID
            latitude: Provider's current latitude
            longitude: Provider's current longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of jobs to return
            
        Returns:
            List of job cards sorted by distance
        """
        try:
            # Get provider to check their job types
            provider = await self.db.get(Provider, provider_id)
            if not provider:
                return []
            
            radius_m = (radius_km or settings.DEFAULT_SEARCH_RADIUS_KM) * 1000
            
            # Create point from provider's location
            provider_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)
            
            # Build query for nearby pending jobs
            query = (
                select(
                    Job,
                    Location,
                    (func.ST_Distance(
                        Location.coordinates,
                        provider_point.cast(type_=Location.coordinates.type)
                    ) / 1000).label("distance_km")
                )
                .join(Location, Job.location_id == Location.id)
                .where(
                    and_(
                        Job.status == JobStatus.PENDING,
                        Job.expires_at > datetime.utcnow(),
                        Job.job_type.in_(provider.job_types),  # Match provider's skills
                        func.ST_DWithin(
                            Location.coordinates,
                            provider_point.cast(type_=Location.coordinates.type),
                            radius_m
                        )
                    )
                )
                .order_by(text("distance_km"))
                .limit(limit)
            )
            
            result = await self.db.execute(query)
            rows = result.all()
            
            # Convert to JobCardResponse
            job_cards = []
            for job, location, distance_km in rows:
                # Calculate time until expiry
                time_until_expiry = job.expires_at - datetime.utcnow()
                expires_in_minutes = int(time_until_expiry.total_seconds() / 60)
                
                # Get first image URL if available
                image_url = None
                if job.images:
                    image_url = job.images[0].image_url
                
                job_card = JobCardResponse(
                    id=job.id,
                    title=job.title,
                    job_type=job.job_type,
                    final_price=job.final_price,
                    distance_km=round(distance_km, 2),
                    expires_in_minutes=max(0, expires_in_minutes),
                    severity=job.severity,
                    estimated_square_footage=job.estimated_square_footage,
                    location_city=location.city,
                    location_state=location.state,
                    image_url=image_url
                )
                job_cards.append(job_card)
            
            logger.info(f"Found {len(job_cards)} nearby jobs for provider {provider_id}")
            return job_cards
            
        except Exception as e:
            logger.error(f"Error finding nearby jobs: {e}")
            return []
    
    async def accept_job(
        self,
        job_id: int,
        provider_id: int
    ) -> bool:
        """
        Provider accepts a job (swipe right) - First-to-claim logic
        Uses atomic transaction to ensure only one provider gets the job
        
        Args:
            job_id: Job ID
            provider_id: Provider ID
            
        Returns:
            True if successfully accepted, False if job already taken or not available
        """
        try:
            # Get job with row-level lock (FOR UPDATE)
            query = select(Job).where(Job.id == job_id).with_for_update()
            result = await self.db.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
            
            # Check if job is still available
            if job.status != JobStatus.PENDING:
                logger.warning(f"Job {job_id} already assigned or not pending")
                return False
            
            # Check if not expired
            if job.expires_at <= datetime.utcnow():
                logger.warning(f"Job {job_id} has expired")
                job.status = JobStatus.EXPIRED
                await self.db.commit()
                return False
            
            # Create assignment
            assignment = JobAssignment(
                job_id=job_id,
                provider_id=provider_id,
                accepted_at=datetime.utcnow()
            )
            
            # Update job status
            job.status = JobStatus.ASSIGNED
            
            self.db.add(assignment)
            await self.db.commit()
            
            logger.info(f"Provider {provider_id} accepted job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error accepting job: {e}")
            await self.db.rollback()
            return False
    
    async def find_available_providers(
        self,
        job_id: int,
        radius_km: Optional[float] = None
    ) -> int:
        """
        Find number of available providers near a job location
        Used for calculating surge pricing
        
        Args:
            job_id: Job ID
            radius_km: Search radius
            
        Returns:
            Count of available providers
        """
        try:
            # Get job location
            query = select(Job, Location).join(Location).where(Job.id == job_id)
            result = await self.db.execute(query)
            row = result.one_or_none()
            
            if not row:
                return 0
            
            job, location = row
            
            # Extract coordinates from location
            # Note: This requires raw SQL to extract lat/lon from Geography type
            coord_query = text("""
                SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat
                FROM locations
                WHERE id = :location_id
            """)
            coord_result = await self.db.execute(coord_query, {"location_id": location.id})
            coords = coord_result.one()
            
            radius_m = (radius_km or settings.DEFAULT_SEARCH_RADIUS_KM) * 1000
            point = func.ST_SetSRID(func.ST_MakePoint(coords.lon, coords.lat), 4326)
            
            # Count available providers
            query = (
                select(func.count(Provider.id))
                .where(
                    and_(
                        Provider.is_available == True,
                        Provider.status == ProviderStatus.VERIFIED,
                        Provider.current_location.isnot(None),
                        job.job_type.in_(Provider.job_types),
                        func.ST_DWithin(
                            Provider.current_location,
                            point.cast(type_=Provider.current_location.type),
                            radius_m
                        )
                    )
                )
            )
            
            result = await self.db.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"Error counting providers: {e}")
            return 0
    
    async def broadcast_job_to_providers(
        self,
        job_id: int
    ) -> List[int]:
        """
        Get list of provider IDs to broadcast job notification to
        
        Args:
            job_id: Job ID
            
        Returns:
            List of provider IDs
        """
        try:
            # Get job and location
            query = select(Job, Location).join(Location).where(Job.id == job_id)
            result = await self.db.execute(query)
            row = result.one_or_none()
            
            if not row:
                return []
            
            job, location = row
            
            # Get location coordinates
            coord_query = text("""
                SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat
                FROM locations
                WHERE id = :location_id
            """)
            coord_result = await self.db.execute(coord_query, {"location_id": location.id})
            coords = coord_result.one()
            
            point = func.ST_SetSRID(func.ST_MakePoint(coords.lon, coords.lat), 4326)
            radius_m = settings.DEFAULT_SEARCH_RADIUS_KM * 1000
            
            # Find matching providers
            query = (
                select(Provider.id)
                .where(
                    and_(
                        Provider.is_available == True,
                        Provider.status == ProviderStatus.VERIFIED,
                        Provider.current_location.isnot(None),
                        job.job_type.in_(Provider.job_types),
                        func.ST_DWithin(
                            Provider.current_location,
                            point.cast(type_=Provider.current_location.type),
                            radius_m
                        )
                    )
                )
            )
            
            result = await self.db.execute(query)
            provider_ids = [row[0] for row in result.all()]
            
            logger.info(f"Broadcasting job {job_id} to {len(provider_ids)} providers")
            return provider_ids
            
        except Exception as e:
            logger.error(f"Error broadcasting job: {e}")
            return []


def get_matching_service(db: AsyncSession) -> MatchingService:
    """Get MatchingService instance"""
    return MatchingService(db)
