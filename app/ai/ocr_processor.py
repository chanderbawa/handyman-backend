"""
OCR Processor for provider verification documents
Uses Tesseract OCR to extract text from ID/licenses/certificates

NOTE: OCR dependencies are optional. If not available, returns mock data.
"""
import re
import logging
from typing import Dict, Optional

try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    OCR processor for extracting text from verification documents
    """
    
    def __init__(self):
        """Initialize OCR processor"""
        self.ocr_enabled = OCR_AVAILABLE
        if not self.ocr_enabled:
            logger.warning("OCR dependencies not available - using mock verification")
    
    async def process_document(
        self,
        image_path: str,
        document_type: str
    ) -> Dict[str, any]:
        """
        Process a verification document and extract relevant information
        
        Args:
            image_path: Path to document image
            document_type: Type of document ('id', 'license', 'insurance', 'certification')
            
        Returns:
            Dictionary with extracted information
        """
        # Return mock data if OCR not available
        if not self.ocr_enabled:
            return self._mock_verification(document_type)
        
        try:
            # Preprocess image for better OCR
            processed_image = self._preprocess_image(image_path)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(processed_image)
            
            # Parse text based on document type
            if document_type == "id":
                return self._parse_id_document(text)
            elif document_type == "license":
                return self._parse_license(text)
            elif document_type == "insurance":
                return self._parse_insurance(text)
            elif document_type == "certification":
                return self._parse_certification(text)
            else:
                return {"raw_text": text, "parsed": False}
                
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return {"error": str(e), "parsed": False}
    
    def _preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        - Convert to grayscale
        - Apply thresholding
        - Denoise
        """
        # Read image
        img = cv2.imread(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding to create binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
        
        # Convert back to PIL Image
        return Image.fromarray(denoised)
    
    def _parse_id_document(self, text: str) -> Dict[str, Optional[str]]:
        """Parse driver's license or ID card"""
        data = {
            "document_type": "id",
            "name": self._extract_name(text),
            "id_number": self._extract_id_number(text),
            "date_of_birth": self._extract_date(text, "DOB"),
            "expiration_date": self._extract_date(text, "EXP"),
            "address": self._extract_address(text),
            "raw_text": text
        }
        return data
    
    def _parse_license(self, text: str) -> Dict[str, Optional[str]]:
        """Parse professional license"""
        data = {
            "document_type": "license",
            "name": self._extract_name(text),
            "license_number": self._extract_license_number(text),
            "issue_date": self._extract_date(text, "ISSUE"),
            "expiration_date": self._extract_date(text, "EXP"),
            "license_type": self._extract_license_type(text),
            "raw_text": text
        }
        return data
    
    def _parse_insurance(self, text: str) -> Dict[str, Optional[str]]:
        """Parse insurance certificate"""
        data = {
            "document_type": "insurance",
            "policy_number": self._extract_policy_number(text),
            "provider": self._extract_insurance_provider(text),
            "coverage_amount": self._extract_coverage(text),
            "effective_date": self._extract_date(text, "EFFECTIVE"),
            "expiration_date": self._extract_date(text, "EXP"),
            "raw_text": text
        }
        return data
    
    def _parse_certification(self, text: str) -> Dict[str, Optional[str]]:
        """Parse professional certification"""
        data = {
            "document_type": "certification",
            "name": self._extract_name(text),
            "certification_number": self._extract_cert_number(text),
            "certification_type": self._extract_cert_type(text),
            "issue_date": self._extract_date(text, "ISSUE"),
            "expiration_date": self._extract_date(text, "EXP"),
            "raw_text": text
        }
        return data
    
    # Helper methods for extracting specific fields
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text"""
        # Look for common patterns
        patterns = [
            r"NAME[:\s]+([A-Z\s]+)",
            r"FULL NAME[:\s]+([A-Z\s]+)",
            r"([A-Z][a-z]+\s[A-Z][a-z]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_id_number(self, text: str) -> Optional[str]:
        """Extract ID number"""
        patterns = [
            r"ID[:\s#]+([A-Z0-9]{8,})",
            r"DL[:\s#]+([A-Z0-9]{8,})",
            r"LICENSE[:\s#]+([A-Z0-9]{8,})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_license_number(self, text: str) -> Optional[str]:
        """Extract license number"""
        patterns = [
            r"LICENSE[:\s#]+([A-Z0-9-]{6,})",
            r"LIC[:\s#]+([A-Z0-9-]{6,})",
            r"#\s*([A-Z0-9-]{6,})"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_date(self, text: str, date_type: str) -> Optional[str]:
        """Extract date (DOB, EXP, etc.)"""
        # Look for dates near the specified label
        pattern = f"{date_type}[:\\s]+([0-9]{{1,2}}[/-][0-9]{{1,2}}[/-][0-9]{{2,4}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Generic date pattern
        date_pattern = r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
        dates = re.findall(date_pattern, text)
        if dates:
            return dates[0]
        
        return None
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address"""
        # Simple address pattern (can be improved)
        pattern = r"(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln))"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_license_type(self, text: str) -> Optional[str]:
        """Extract license type"""
        types = ["plumbing", "electrical", "hvac", "general contractor", "carpentry"]
        text_lower = text.lower()
        
        for license_type in types:
            if license_type in text_lower:
                return license_type
        return None
    
    def _extract_policy_number(self, text: str) -> Optional[str]:
        """Extract insurance policy number"""
        pattern = r"POLICY[:\s#]+([A-Z0-9-]{6,})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_insurance_provider(self, text: str) -> Optional[str]:
        """Extract insurance provider name"""
        providers = ["State Farm", "Allstate", "Progressive", "GEICO", "Liberty Mutual"]
        text_lower = text.lower()
        
        for provider in providers:
            if provider.lower() in text_lower:
                return provider
        return None
    
    def _extract_coverage(self, text: str) -> Optional[str]:
        """Extract coverage amount"""
        pattern = r"\$\s*([0-9,]+(?:\.[0-9]{2})?)"
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
        return None
    
    def _extract_cert_number(self, text: str) -> Optional[str]:
        """Extract certification number"""
        pattern = r"CERT(?:IFICATE)?[:\s#]+([A-Z0-9-]{6,})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_cert_type(self, text: str) -> Optional[str]:
        """Extract certification type"""
        types = ["OSHA", "CPR", "First Aid", "Forklift", "Asbestos"]
        text_lower = text.lower()
        
        for cert_type in types:
            if cert_type.lower() in text_lower:
                return cert_type
        return None
    
    def _mock_verification(self, document_type: str) -> Dict[str, any]:
        """Return mock verification when OCR is not available"""
        mock_data = {
            "id": {
                "full_name": "John Doe",
                "id_number": "123456789",
                "expiration_date": "2025-12-31",
                "verified": True,
                "confidence": 0.7
            },
            "license": {
                "license_number": "LIC123456",
                "state": "CA",
                "expiration_date": "2025-12-31",
                "verified": True,
                "confidence": 0.7
            },
            "insurance": {
                "policy_number": "POL123456",
                "provider": "Mock Insurance Co.",
                "expiration_date": "2025-12-31",
                "verified": True,
                "confidence": 0.7
            },
            "certification": {
                "cert_number": "CERT123",
                "cert_type": "General",
                "expiration_date": "2025-12-31",
                "verified": True,
                "confidence": 0.7
            }
        }
        
        result = mock_data.get(document_type, mock_data["id"])
        result["mock_data"] = True
        return result


# Singleton instance
_ocr_processor = None

def get_ocr_processor() -> OCRProcessor:
    """Get or create OCRProcessor singleton"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor
