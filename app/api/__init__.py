from fastapi import APIRouter

from app.api import auth, jobs, providers, locations

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])

__all__ = ["api_router"]
