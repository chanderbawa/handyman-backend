"""
LLM Integration for parsing vague user requests
Uses OpenAI GPT-4 to parse natural language into structured job tickets
"""
import openai
from typing import List, Dict
import json
import logging

from app.config import settings
from app.models.job import JobType

logger = logging.getLogger(__name__)


class JobParser:
    """
    LLM-based parser for converting vague user requests into structured job tickets
    """
    
    def __init__(self):
        """Initialize OpenAI client"""
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
    
    async def parse_job_request(self, user_input: str) -> List[Dict[str, any]]:
        """
        Parse a user's natural language request into one or more job tickets
        
        Example:
            Input: "My back gate is broken and I need the leaves raked"
            Output: [
                {"job_type": "carpentry", "title": "Fix broken back gate", "description": "..."},
                {"job_type": "landscaping", "title": "Rake leaves", "description": "..."}
            ]
        
        Args:
            user_input: Natural language description from user
            
        Returns:
            List of job ticket dictionaries
        """
        try:
            system_prompt = """You are a helpful assistant that parses home service requests.
Given a user's description, extract individual job tasks and classify them.

Classify each task into one of these categories:
- snow_removal: Snow plowing, shoveling, ice removal
- lawn_care: Mowing, leaf raking, hedge trimming, landscaping
- handyman: General repairs, furniture assembly, minor fixes
- plumbing: Pipe repairs, drain issues, faucet installation
- electrical: Wiring, outlet installation, light fixtures
- carpentry: Door repair, fence work, deck maintenance
- other: Tasks that don't fit other categories

Return a JSON array of job objects with these fields:
- job_type: category from above
- title: short descriptive title (max 100 chars)
- description: detailed description of the task
- priority: "high", "medium", or "low"

If the request is vague, make reasonable assumptions and note them in the description.
"""
            
            user_prompt = f"Parse this service request: {user_input}"
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for more consistent parsing
            )
            
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Extract jobs array from response
            jobs = parsed_data.get("jobs", [parsed_data]) if "jobs" in parsed_data else [parsed_data]
            
            # Validate and normalize job types
            validated_jobs = []
            for job in jobs:
                job_type_str = job.get("job_type", "other").lower()
                
                # Map to JobType enum
                try:
                    job_type = JobType(job_type_str)
                except ValueError:
                    job_type = JobType.OTHER
                
                validated_jobs.append({
                    "job_type": job_type,
                    "title": job.get("title", "Service Request"),
                    "description": job.get("description", user_input),
                    "priority": job.get("priority", "medium")
                })
            
            logger.info(f"Parsed {len(validated_jobs)} jobs from user input")
            return validated_jobs
            
        except Exception as e:
            logger.error(f"Error parsing job request: {e}")
            # Fallback: return a single generic job
            return [{
                "job_type": JobType.OTHER,
                "title": "Service Request",
                "description": user_input,
                "priority": "medium"
            }]
    
    async def enhance_job_description(self, job_type: JobType, brief_description: str) -> str:
        """
        Use LLM to enhance a brief job description with relevant details
        
        Args:
            job_type: Type of job
            brief_description: Short description from user
            
        Returns:
            Enhanced description with additional context
        """
        try:
            prompt = f"""Given this {job_type.value} job: "{brief_description}"

Enhance the description by:
1. Adding relevant details a service provider would need
2. Suggesting what to look for or prepare
3. Keeping it concise (2-3 sentences)

Return only the enhanced description, no additional commentary."""
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=150
            )
            
            enhanced = response.choices[0].message.content.strip()
            return enhanced
            
        except Exception as e:
            logger.error(f"Error enhancing description: {e}")
            return brief_description


# Singleton instance
_job_parser = None

def get_job_parser() -> JobParser:
    """Get or create JobParser singleton"""
    global _job_parser
    if _job_parser is None:
        _job_parser = JobParser()
    return _job_parser
