from app.ai.computer_vision import ImageAnalyzer
from app.ai.llm_parser import JobParser
from app.ai.pricing_agent import DynamicPricingAgent
from app.ai.ocr_processor import OCRProcessor

# Singleton instances
_image_analyzer = None
_job_parser = None
_pricing_agent = None
_ocr_processor = None


def get_image_analyzer() -> ImageAnalyzer:
    """Get or create ImageAnalyzer singleton"""
    global _image_analyzer
    if _image_analyzer is None:
        _image_analyzer = ImageAnalyzer()
    return _image_analyzer


def get_job_parser() -> JobParser:
    """Get or create JobParser singleton"""
    global _job_parser
    if _job_parser is None:
        _job_parser = JobParser()
    return _job_parser


def get_pricing_agent() -> DynamicPricingAgent:
    """Get or create DynamicPricingAgent singleton"""
    global _pricing_agent
    if _pricing_agent is None:
        _pricing_agent = DynamicPricingAgent()
    return _pricing_agent


def get_ocr_processor() -> OCRProcessor:
    """Get or create OCRProcessor singleton"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor


__all__ = [
    "ImageAnalyzer",
    "JobParser",
    "DynamicPricingAgent",
    "OCRProcessor",
    "get_image_analyzer",
    "get_job_parser",
    "get_pricing_agent",
    "get_ocr_processor"
]
