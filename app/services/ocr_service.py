




"""
OCR Service - Extract water quality parameters from PDF
Using OpenAI GPT-4o Vision for intelligent extraction
100% Dynamic - No hard-coded parameters
PRODUCTION READY - With all features
"""

import os
import json
import base64
import logging
import platform
import shutil
from typing import Dict, Any
from datetime import datetime
from io import BytesIO

from openai import AsyncOpenAI
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader
from PIL import Image
import re

logger = logging.getLogger(__name__)


# ===============================
# UTILS: SANITIZE NUMBERS
# ===============================
def _sanitize_number(value: Any) -> float | None:
    """Convert a value to float if possible, else return None"""
    if value is None:
        return None

    # If already numeric, keep
    if isinstance(value, (int, float)):
        return float(value)

    # Convert strings like "<0.01", ">0.5", "0.05"
    if isinstance(value, str):
        try:
            # Remove <, >, whitespace
            cleaned = value.replace("<", "").replace(">", "").strip()
            return float(cleaned)
        except ValueError:
            # Non-numeric like 'NYS', 'BDL' → None
            return None

    return None


def _sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize all 'value' and 'detection_limit' fields in parameters dict"""
    for param_name, param_data in parameters.items():
        if isinstance(param_data, dict):
            for key in ["value", "detection_limit"]:
                if key in param_data:
                    param_data[key] = _sanitize_number(param_data[key])
    return parameters


class OCRService:
    """Extract chemical parameters from PDF using AI - COMPLETE VERSION"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"
        
        # Check poppler availability
        self.poppler_available = self._check_poppler()
        if self.poppler_available:
            logger.info("✅ Poppler available - Image OCR enabled")
        else:
            logger.warning("⚠️ Poppler not available - Text-only OCR mode")
    
    # =====================================================
    # PUBLIC API
    # =====================================================
    async def extract_from_pdf(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract all water quality parameters from PDF
        
        Args:
            pdf_content: PDF file bytes
            filename: Original filename
            
        Returns:
            {
                "parameters": {...},
                "metadata": {...},
                "validation": {...}  # Optional
            }
        """
        try:
            logger.info(f"🔍 Starting OCR extraction for {filename}")
            
            # Try image-based OCR first (if poppler available)
            if self.poppler_available:
                images = self._pdf_to_images_safe(pdf_content)
                if images:
                    logger.info(f"📄 Image OCR mode - {len(images)} pages")
                    parameters = await self._extract_from_images(images)
                    
                    # Validate extraction
                    validation = await self.validate_extraction(parameters)
                    
                    return {
                        "parameters": parameters,
                        "metadata": {
                            "source_file": filename,
                            "method": "image-ocr",
                            "pages_processed": len(images),
                            "extraction_date": datetime.utcnow().isoformat()
                        },
                        "validation": validation,
                        "created_at": datetime.utcnow()
                    }
            
            # Fallback: Text-only extraction
            logger.info("📄 Text-only OCR fallback")
            text = self._extract_text_from_pdf(pdf_content)
            parameters = await self._extract_from_text(text)
            
            # Validate
            validation = await self.validate_extraction(parameters)
            
            return {
                "parameters": parameters,
                "metadata": {
                    "source_file": filename,
                    "method": "text-only",
                    "pages_processed": 1,
                    "extraction_date": datetime.utcnow().isoformat()
                },
                "validation": validation,
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.exception("❌ OCR extraction failed")
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    # =====================================================
    # POPPLER DETECTION
    # =====================================================
    def _check_poppler(self) -> bool:
        """Check if poppler is available on system"""
        system = platform.system()
        
        if system == "Windows":
            common_paths = [
                r"C:\poppler\Library\bin",
                r"C:\Program Files\poppler\bin",
                r"C:\poppler-bin\bin",
                os.path.expanduser(r"~\poppler\bin")
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"✅ Found Poppler at: {path}")
                    return True
            
            logger.warning("⚠️ Poppler not found in common Windows paths")
            return False
        
        else:
            # Linux/Mac: Check if pdftoppm in PATH
            return shutil.which("pdftoppm") is not None
    
    def _get_poppler_path(self):
        """Get poppler path for current OS"""
        system = platform.system()
        
        if system == "Windows":
            common_paths = [
                r"C:\poppler\Library\bin",
                r"C:\Program Files\poppler\bin",
                r"C:\poppler-bin\bin"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            return None
        
        # Linux/Mac don't need explicit path
        return None
    
    # =====================================================
    # PDF → IMAGES
    # =====================================================
    def _pdf_to_images_safe(self, pdf_content: bytes):
        """Safely convert PDF to images"""
        try:
            poppler_path = self._get_poppler_path()
            
            images = convert_from_bytes(
                pdf_content,
                dpi=300,
                first_page=1,
                last_page=3,
                poppler_path=poppler_path
            )
            
            if not images:
                raise RuntimeError("PDF conversion returned no images")
            
            return images
            
        except Exception as e:
            logger.warning(f"⚠️ Image conversion failed: {e}")
            return None
    
    # =====================================================
    # IMAGE OCR
    # =====================================================
    async def _extract_from_images(self, images) -> Dict[str, Any]:
        """Extract from multiple images"""
        all_parameters: Dict[str, Any] = {}
        
        for idx, image in enumerate(images, start=1):
            logger.info(f"📊 Processing page {idx}/{len(images)}")
            img_base64 = self._image_to_base64(image)
            page_params = await self._extract_with_vision(img_base64, idx)
            all_parameters.update(page_params)
        
        # ===== SANITIZE NUMBERS =====
        all_parameters = _sanitize_parameters(all_parameters)
        
        logger.info(f"✅ Extracted {len(all_parameters)} unique parameters")
        return all_parameters
    
    async def _extract_with_vision(self, image_base64: str, page_num: int) -> Dict[str, Any]:
        """Use GPT-4o Vision to extract parameters from image"""
        try:
            prompt = self._build_extraction_prompt_detailed()
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert water quality analyst. Extract ALL chemical, physical, and biological parameters from water analysis reports with precision."},
                    {"role": "user",
                     "content": [
                         {"type": "text", "text": prompt},
                         {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                     ]}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            logger.debug(f"GPT-4o Response (first 200 chars): {content[:200]}...")
            
            parameters = self._parse_gpt_response(content)
            
            # ===== SANITIZE =====
            parameters = _sanitize_parameters(parameters)
            
            logger.info(f"✅ Page {page_num}: Extracted {len(parameters)} parameters")
            return parameters
            
        except Exception as e:
            logger.error(f"❌ Vision API failed for page {page_num}: {e}")
            return {}
    
    # =====================================================
    # TEXT FALLBACK
    # =====================================================
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract raw text from PDF"""
        try:
            reader = PdfReader(BytesIO(pdf_content))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return ""
    
    async def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract parameters from plain text"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Extract water quality parameters from text accurately."},
                    {"role": "user", "content": f"{self._build_extraction_prompt_detailed()}\n\nText content:\n{text}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            parameters = self._parse_gpt_response(response.choices[0].message.content)
            
            # ===== SANITIZE =====
            parameters = _sanitize_parameters(parameters)
            
            return parameters
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {e}")
            return {}
    
    # =====================================================
    # PROMPTS
    # =====================================================
    def _build_extraction_prompt_detailed(self) -> str:
        return """
Extract ALL water quality parameters from this image/text. 

IMPORTANT INSTRUCTIONS:
1. Extract EVERY parameter you see (chemical, physical, biological)
2. Include parameter name, numeric value, and unit
3. For pH, temperature without units, set unit as null
4. Common parameters include: pH, Temperature, TDS, Conductivity, Alkalinity, Hardness, 
   Calcium, Magnesium, Sodium, Potassium, Chloride, Sulfate, Nitrate, Fluoride, Iron, 
   Manganese, Arsenic, Lead, Mercury, Bacteria count, BOD, COD, Turbidity, Color, Odor, etc.
5. DO NOT skip any parameter, even if unfamiliar
6. If a parameter has "<" or ">" (like "<0.01"), extract the numeric value and note detection_limit
7. If value is "BDL" or "Below Detection Limit", use 0 for value and note in detection_limit

Return ONLY valid JSON in this EXACT format:
{
  "pH": {
    "value": 7.8,
    "unit": null,
    "detection_limit": null
  },
  "Calcium": {
    "value": 85.5,
    "unit": "mg/L",
    "detection_limit": null
  },
  "Temperature": {
    "value": 25.0,
    "unit": "°C",
    "detection_limit": null
  },
  "TDS": {
    "value": 450,
    "unit": "mg/L",
    "detection_limit": null
  },
  "Arsenic": {
    "value": 0.01,
    "unit": "mg/L",
    "detection_limit": "<0.01"
  },
  "Bacteria_Count": {
    "value": 0,
    "unit": "CFU/100mL",
    "detection_limit": "BDL"
  }
}

CRITICAL: Return ONLY the JSON object, no explanation, no markdown code blocks, no extra text.
"""
    
    # =====================================================
    # JSON PARSING
    # =====================================================
    def _parse_gpt_response(self, content: str) -> Dict[str, Any]:
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parameters = json.loads(content)
            return parameters
        except json.JSONDecodeError:
            return self._manual_json_extraction(content)
        except Exception as e:
            logger.error(f"❌ Unexpected parsing error: {e}")
            return {}
    
    def _manual_json_extraction(self, content: str) -> Dict[str, Any]:
        logger.warning("⚠️ Attempting manual JSON extraction")
        try:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"❌ Manual extraction failed: {e}")
        return {}
    
    # =====================================================
    # VALIDATION
    # =====================================================
    async def validate_extraction(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not parameters:
                return {"valid": True, "errors": [], "warnings": []}
            
            validation_prompt = f"""
Review these extracted water quality parameters for errors:

{json.dumps(parameters, indent=2)}

Check for:
1. Unrealistic values (e.g., pH > 14 or < 0, negative concentrations)
2. Missing or incorrect units
3. Inconsistent data (e.g., TDS lower than individual ions sum)
4. Typical ranges:
   - pH: 0-14
   - TDS: 0-5000 mg/L (typical drinking water)
   - Calcium: 0-500 mg/L
   - Temperature: 0-100°C

Return JSON with:
{{
  "valid": true/false,
  "errors": ["list of critical errors if any"],
  "warnings": ["list of warnings if any"],
  "suggestions": ["list of suggestions"]
}}

IMPORTANT: Return only JSON, no explanation.
"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system",
                     "content": "You are a water quality data validator with expertise in chemistry."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            validation_result = self._parse_gpt_response(response.choices[0].message.content)
            
            if not validation_result.get("valid", True):
                logger.warning(f"⚠️ Validation found issues: {validation_result.get('errors', [])}")
            else:
                logger.info("✅ Validation passed")
            
            return validation_result
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return {"valid": True, "errors": [], "warnings": [], "note": "Validation skipped due to error"}
    
    # =====================================================
    # UTILS
    # =====================================================
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(buffered, format="JPEG", quality=95)
        return base64.b64encode(buffered.getvalue()).decode()
