"""
Job Service - Handles job creation with AI integration
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.models.job import Job, JobImage, JobStatus
from app.models.location import Location
from app.schemas.job import JobCreate, JobImageAnalysis
from app.ai import ImageAnalyzer, JobParser, DynamicPricingAgent
from app.services.matching_service import MatchingService
from app.config import settings

logger = logging.getLogger(__name__)


class JobService:
    """
    Service for creating and managing jobs with AI integration
    """
    
    def __init__(
        self,
        db: AsyncSession,
        image_analyzer: ImageAnalyzer,
        job_parser: JobParser,
        pricing_agent: DynamicPricingAgent
    ):
        self.db = db
        self.image_analyzer = image_analyzer
        self.job_parser = job_parser
        self.pricing_agent = pricing_agent
    
    async def create_job_from_text(
        self,
        user_id: int,
        location_id: int,
        description: str,
        image_paths: Optional[List[str]] = None
    ) -> List[Job]:
        """
        Create one or more jobs from a text description
        Uses LLM to parse vague requests into specific job tickets
        
        Args:
            user_id: User ID
            location_id: Location ID
            description: Natural language description
            image_paths: Optional list of image paths for CV analysis
            
        Returns:
            List of created Job objects
        """
        try:
            # Parse description with LLM
            parsed_jobs = await self.job_parser.parse_job_request(description)
            
            # Get location for pricing
            location = await self.db.get(Location, location_id)
            if not location:
                raise ValueError(f"Location {location_id} not found")
            
            # Extract coordinates
            coord_query = text("""
                SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat
                FROM locations
                WHERE id = :location_id
            """)
            coord_result = await self.db.execute(coord_query, {"location_id": location_id})
            coords = coord_result.one()
            
            created_jobs = []
            
            for parsed_job in parsed_jobs:
                # Process images if provided
                cv_analysis = None
                if image_paths:
                    cv_analysis = await self.image_analyzer.analyze_image(
                        image_paths[0],  # Use first image
                        parsed_job["job_type"]
                    )
                
                # Get number of available providers for pricing
                matching_service = MatchingService(self.db)
                # We'll estimate provider count as 10 for now since job doesn't exist yet
                provider_count = 10
                
                # Calculate pricing
                pricing = await self.pricing_agent.calculate_price(
                    job_type=parsed_job["job_type"],
                    estimated_sqft=cv_analysis.get("estimated_square_footage") if cv_analysis else None,
                    severity=cv_analysis.get("severity") if cv_analysis else None,
                    latitude=coords.lat,
                    longitude=coords.lon,
                    provider_count=provider_count
                )
                
                # Create job
                job = Job(
                    user_id=user_id,
                    location_id=location_id,
                    job_type=parsed_job["job_type"],
                    title=parsed_job["title"],
                    description=parsed_job["description"],
                    estimated_square_footage=cv_analysis.get("estimated_square_footage") if cv_analysis else None,
                    severity=cv_analysis.get("severity") if cv_analysis else None,
                    ai_confidence=cv_analysis.get("confidence") if cv_analysis else None,
                    estimated_price=pricing["base_price"],
                    surge_multiplier=pricing["demand_multiplier"],
                    final_price=pricing["final_price"],
                    status=JobStatus.PENDING,
                    expires_at=datetime.utcnow() + timedelta(minutes=settings.JOB_EXPIRY_MINUTES),
                    extra_data={
                        "weather_multiplier": pricing["weather_multiplier"],
                        "severity_multiplier": pricing["severity_multiplier"]
                    }
                )
                
                self.db.add(job)
                await self.db.flush()  # Get job ID
                
                # Add images
                if image_paths:
                    for img_path in image_paths:
                        job_image = JobImage(
                            job_id=job.id,
                            image_url=img_path,
                            analysis_results=cv_analysis
                        )
                        self.db.add(job_image)
                
                created_jobs.append(job)
            
            await self.db.commit()
            
            # Refresh to load relationships
            for job in created_jobs:
                await self.db.refresh(job)
            
            logger.info(f"Created {len(created_jobs)} jobs from description")
            return created_jobs
            
        except Exception as e:
            logger.error(f"Error creating jobs: {e}")
            await self.db.rollback()
            raise
    
    async def create_job_with_images(
        self,
        user_id: int,
        location_id: int,
        title: str,
        job_type: str,
        image_paths: List[str],
        description: Optional[str] = None
    ) -> Job:
        """
        Create a job with image analysis (for when user specifies job type)
        
        Args:
            user_id: User ID
            location_id: Location ID
            title: Job title
            job_type: Job type
            image_paths: List of image paths
            description: Optional description
            
        Returns:
            Created Job object
        """
        try:
            from app.models.job import JobType
            job_type_enum = JobType(job_type)
            
            # Analyze first image
            cv_analysis = await self.image_analyzer.analyze_image(
                image_paths[0],
                job_type_enum
            )
            
            # Get location coordinates
            location = await self.db.get(Location, location_id)
            coord_query = text("""
                SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat
                FROM locations
                WHERE id = :location_id
            """)
            coord_result = await self.db.execute(coord_query, {"location_id": location_id})
            coords = coord_result.one()
            
            # Count available providers
            matching_service = MatchingService(self.db)
            provider_count = 10  # Placeholder
            
            # Calculate pricing
            pricing = await self.pricing_agent.calculate_price(
                job_type=job_type_enum,
                estimated_sqft=cv_analysis["estimated_square_footage"],
                severity=cv_analysis["severity"],
                latitude=coords.lat,
                longitude=coords.lon,
                provider_count=provider_count
            )
            
            # Enhance description with LLM if needed
            if not description:
                description = await self.job_parser.enhance_job_description(
                    job_type_enum,
                    title
                )
            
            # Create job
            job = Job(
                user_id=user_id,
                location_id=location_id,
                job_type=job_type_enum,
                title=title,
                description=description,
                estimated_square_footage=cv_analysis["estimated_square_footage"],
                severity=cv_analysis["severity"],
                ai_confidence=cv_analysis["confidence"],
                estimated_price=pricing["base_price"],
                surge_multiplier=pricing["demand_multiplier"],
                final_price=pricing["final_price"],
                status=JobStatus.PENDING,
                expires_at=datetime.utcnow() + timedelta(minutes=settings.JOB_EXPIRY_MINUTES),
                extra_data=cv_analysis.get("metadata", {})
            )
            
            self.db.add(job)
            await self.db.flush()
            
            # Add images
            for img_path in image_paths:
                job_image = JobImage(
                    job_id=job.id,
                    image_url=img_path,
                    analysis_results=cv_analysis
                )
                self.db.add(job_image)
            
            await self.db.commit()
            await self.db.refresh(job)
            
            logger.info(f"Created job {job.id} with image analysis")
            return job
            
        except Exception as e:
            logger.error(f"Error creating job with images: {e}")
            await self.db.rollback()
            raise
    
    async def get_user_jobs(self, user_id: int) -> List[Job]:
        """Get all jobs for a user"""
        query = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_job_by_id(self, job_id: int) -> Optional[Job]:
        """Get a job by ID"""
        return await self.db.get(Job, job_id)


def get_job_service(
    db: AsyncSession,
    image_analyzer: ImageAnalyzer,
    job_parser: JobParser,
    pricing_agent: DynamicPricingAgent
) -> JobService:
    """Get JobService instance"""
    return JobService(db, image_analyzer, job_parser, pricing_agent)
