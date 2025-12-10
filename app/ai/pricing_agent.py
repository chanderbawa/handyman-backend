"""
Dynamic Pricing Agent
Adjusts pricing based on:
- Estimated work size (from CV)
- Real-time weather conditions
- Local supply/demand (surge pricing)
"""
import httpx
import logging
from typing import Dict, Optional
from datetime import datetime
import math

from app.config import settings
from app.models.job import JobType, SeverityLevel

logger = logging.getLogger(__name__)


class DynamicPricingAgent:
    """
    AI agent for dynamic pricing based on multiple factors
    """
    
    def __init__(self):
        """Initialize pricing agent with base rates"""
        # Base price per square foot for different job types
        self.base_rates = {
            JobType.SNOW_REMOVAL: 0.20,      # $0.20 per sq ft
            JobType.LAWN_CARE: 0.15,         # $0.15 per sq ft
            JobType.HANDYMAN: 50.0,          # $50 base + hourly
            JobType.PLUMBING: 75.0,          # $75 base + hourly
            JobType.ELECTRICAL: 85.0,        # $85 base + hourly
            JobType.CARPENTRY: 60.0,         # $60 base + hourly
            JobType.OTHER: 50.0,             # $50 base
        }
        
        # Severity multipliers
        self.severity_multipliers = {
            SeverityLevel.LIGHT: 1.0,
            SeverityLevel.MODERATE: 1.3,
            SeverityLevel.HEAVY: 1.7,
            SeverityLevel.SEVERE: 2.2,
        }
        
        # Minimum prices
        self.minimum_prices = {
            JobType.SNOW_REMOVAL: 40.0,
            JobType.LAWN_CARE: 35.0,
            JobType.HANDYMAN: 50.0,
            JobType.PLUMBING: 75.0,
            JobType.ELECTRICAL: 85.0,
            JobType.CARPENTRY: 60.0,
            JobType.OTHER: 40.0,
        }
    
    async def calculate_price(
        self,
        job_type: JobType,
        estimated_sqft: Optional[float] = None,
        severity: Optional[SeverityLevel] = None,
        latitude: float = None,
        longitude: float = None,
        provider_count: int = 10  # Number of available providers nearby
    ) -> Dict[str, float]:
        """
        Calculate dynamic price for a job
        
        Args:
            job_type: Type of job
            estimated_sqft: Estimated square footage (from CV)
            severity: Severity level (from CV)
            latitude: Job location latitude
            longitude: Job location longitude
            provider_count: Number of available providers in area
            
        Returns:
            Dictionary with price breakdown
        """
        # Calculate base price
        base_price = self._calculate_base_price(job_type, estimated_sqft)
        
        # Apply severity multiplier
        severity_mult = self.severity_multipliers.get(severity, 1.0) if severity else 1.0
        price_after_severity = base_price * severity_mult
        
        # Get weather multiplier
        weather_mult = await self._get_weather_multiplier(latitude, longitude, job_type)
        
        # Get supply/demand multiplier (surge pricing)
        demand_mult = self._calculate_demand_multiplier(provider_count)
        
        # Calculate final price
        total_multiplier = severity_mult * weather_mult * demand_mult
        final_price = price_after_severity * weather_mult * demand_mult
        
        # Apply minimum price
        min_price = self.minimum_prices.get(job_type, 40.0)
        final_price = max(final_price, min_price)
        
        # Round to 2 decimal places
        final_price = round(final_price, 2)
        
        return {
            "base_price": round(base_price, 2),
            "severity_multiplier": round(severity_mult, 2),
            "weather_multiplier": round(weather_mult, 2),
            "demand_multiplier": round(demand_mult, 2),
            "total_multiplier": round(total_multiplier, 2),
            "final_price": final_price
        }
    
    def _calculate_base_price(
        self,
        job_type: JobType,
        estimated_sqft: Optional[float]
    ) -> float:
        """Calculate base price before multipliers"""
        base_rate = self.base_rates.get(job_type, 50.0)
        
        if estimated_sqft and job_type in [JobType.SNOW_REMOVAL, JobType.LAWN_CARE]:
            # Area-based pricing
            return base_rate * estimated_sqft
        else:
            # Flat base rate for service jobs
            return base_rate
    
    async def _get_weather_multiplier(
        self,
        latitude: Optional[float],
        longitude: Optional[float],
        job_type: JobType
    ) -> float:
        """
        Get weather-based multiplier using real-time weather API
        Heavy snow = higher prices for snow removal
        """
        if not latitude or not longitude or not settings.WEATHER_API_KEY:
            return 1.0
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.WEATHER_API_URL,
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": settings.WEATHER_API_KEY,
                        "units": "imperial"
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._analyze_weather_impact(data, job_type)
                
        except Exception as e:
            logger.warning(f"Weather API error: {e}")
        
        return 1.0
    
    def _analyze_weather_impact(self, weather_data: Dict, job_type: JobType) -> float:
        """Analyze weather data and return pricing multiplier"""
        weather = weather_data.get("weather", [{}])[0]
        main = weather_data.get("main", {})
        
        weather_condition = weather.get("main", "").lower()
        temperature = main.get("temp", 50)
        
        if job_type == JobType.SNOW_REMOVAL:
            # Heavy snow conditions increase price
            if "snow" in weather_condition:
                return 1.5
            elif temperature < 32:  # Freezing
                return 1.3
        
        elif job_type == JobType.LAWN_CARE:
            # Rain makes lawn care harder
            if "rain" in weather_condition:
                return 1.2
        
        return 1.0
    
    def _calculate_demand_multiplier(self, provider_count: int) -> float:
        """
        Calculate surge pricing based on supply/demand
        Fewer providers = higher prices (up to 2x)
        """
        # Optimal provider count is 10+
        if provider_count >= 10:
            return 1.0
        elif provider_count >= 5:
            return 1.2
        elif provider_count >= 3:
            return 1.5
        elif provider_count >= 1:
            return 1.8
        else:
            # No providers available - max surge
            return settings.SURGE_MULTIPLIER_MAX


# Singleton instance
_pricing_agent = None

def get_pricing_agent() -> DynamicPricingAgent:
    """Get or create DynamicPricingAgent singleton"""
    global _pricing_agent
    if _pricing_agent is None:
        _pricing_agent = DynamicPricingAgent()
    return _pricing_agent
