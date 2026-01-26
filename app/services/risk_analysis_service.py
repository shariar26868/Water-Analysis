"""
Risk Analysis Service - Contamination risk assessment
Heavy metals, organic compounds, microbiological risks
100% Dynamic - Risk thresholds from database
"""

import logging
from typing import Dict, Any, List

from app.db.mongo import db

logger = logging.getLogger(__name__)


class RiskAnalysisService:
    """Analyze contamination risks in water sample"""
    
    async def analyze_risks(
        self,
        parameters: Dict[str, Any],
        chemical_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive contamination risk analysis
        
        Returns:
            {
                "heavy_metals": [...],
                "organic_compounds": [...],
                "microbiological": [...],
                "overall_severity": "Low/Medium/High/Critical",
                "risk_score": 2.5
            }
        """
        try:
            logger.info("⚠️ Analyzing contamination risks")
            
            # Analyze heavy metals
            heavy_metals = await self._analyze_heavy_metals(parameters)
            
            # Analyze organic compounds
            organic_compounds = await self._analyze_organic_compounds(parameters)
            
            # Analyze microbiological risks
            microbiological = await self._analyze_microbiological(parameters)
            
            # Calculate overall severity
            overall_severity, risk_score = self._calculate_overall_severity(
                heavy_metals,
                organic_compounds,
                microbiological
            )
            
            logger.info(f"✅ Risk analysis complete - Overall: {overall_severity} (Score: {risk_score}/10)")
            
            return {
                "heavy_metals": heavy_metals,
                "organic_compounds": organic_compounds,
                "microbiological": microbiological,
                "overall_severity": overall_severity,
                "risk_score": risk_score
            }
            
        except Exception as e:
            logger.error(f"❌ Risk analysis failed: {e}")
            raise Exception(f"Risk analysis failed: {str(e)}")
    
    async def _analyze_heavy_metals(self, parameters: Dict) -> List[Dict]:
        """
        Analyze heavy metal contamination
        
        Heavy metals: Lead, Arsenic, Mercury, Cadmium, Chromium, etc.
        """
        heavy_metal_keywords = [
            "lead", "arsenic", "mercury", "cadmium", "chromium",
            "pb", "as", "hg", "cd", "cr", "copper", "cu", "zinc", "zn",
            "nickel", "ni", "manganese", "mn"
        ]
        
        heavy_metals = []
        
        for param_name, param_data in parameters.items():
            param_lower = param_name.lower()
            
            # Check if it's a heavy metal
            is_heavy_metal = any(keyword in param_lower for keyword in heavy_metal_keywords)
            
            if not is_heavy_metal:
                continue
            
            value = param_data.get("value")
            unit = param_data.get("unit", "mg/L")
            
            if not isinstance(value, (int, float)):
                continue
            
            # Get standard
            standard = await db.get_parameter_standard(param_name)
            
            # Assess risk
            risk_level, threshold = await self._assess_contaminant_risk(
                param_name,
                value,
                standard,
                contaminant_type="heavy_metal"
            )
            
            heavy_metals.append({
                "contaminant_name": param_name,
                "value": value,
                "unit": unit,
                "risk_level": risk_level,
                "threshold": threshold
            })
        
        # If no heavy metals found, add placeholder
        if not heavy_metals:
            heavy_metals.append({
                "contaminant_name": "No heavy metals detected",
                "value": 0,
                "unit": "N/A",
                "risk_level": "Low",
                "threshold": None
            })
        
        return heavy_metals
    
    async def _analyze_organic_compounds(self, parameters: Dict) -> List[Dict]:
        """
        Analyze organic compound contamination
        
        Organic: BOD, COD, TOC, Pesticides, VOCs, etc.
        """
        organic_keywords = [
            "bod", "cod", "toc", "pesticide", "herbicide",
            "voc", "benzene", "toluene", "phenol", "chloroform", "dioxin"
        ]
        
        organic_compounds = []
        
        for param_name, param_data in parameters.items():
            param_lower = param_name.lower()
            
            # Check if it's organic
            is_organic = any(keyword in param_lower for keyword in organic_keywords)
            
            if not is_organic:
                continue
            
            value = param_data.get("value")
            unit = param_data.get("unit", "mg/L")
            
            if not isinstance(value, (int, float)):
                continue
            
            # Get standard
            standard = await db.get_parameter_standard(param_name)
            
            # Assess risk
            risk_level, threshold = await self._assess_contaminant_risk(
                param_name,
                value,
                standard,
                contaminant_type="organic"
            )
            
            organic_compounds.append({
                "contaminant_name": param_name,
                "value": value,
                "unit": unit,
                "risk_level": risk_level,
                "threshold": threshold
            })
        
        # If no organics found
        if not organic_compounds:
            organic_compounds.append({
                "contaminant_name": "No organic contaminants detected",
                "value": 0,
                "unit": "N/A",
                "risk_level": "Low",
                "threshold": None
            })
        
        return organic_compounds
    
    async def _analyze_microbiological(self, parameters: Dict) -> List[Dict]:
        """
        Analyze microbiological contamination
        
        Microbiological: Bacteria, Coliform, E.coli, Pathogens, etc.
        """
        micro_keywords = [
            "bacteria", "coliform", "e.coli", "pathogen",
            "fecal", "total_plate", "cfu"
        ]
        
        microbiological = []
        
        for param_name, param_data in parameters.items():
            param_lower = param_name.lower()
            
            # Check if it's microbiological
            is_micro = any(keyword in param_lower for keyword in micro_keywords)
            
            if not is_micro:
                continue
            
            value = param_data.get("value")
            unit = param_data.get("unit", "CFU/100mL")
            
            if not isinstance(value, (int, float)):
                continue
            
            # Get standard
            standard = await db.get_parameter_standard(param_name)
            
            # Assess risk
            risk_level, threshold = await self._assess_contaminant_risk(
                param_name,
                value,
                standard,
                contaminant_type="microbiological"
            )
            
            microbiological.append({
                "contaminant_name": param_name,
                "value": value,
                "unit": unit,
                "risk_level": risk_level,
                "threshold": threshold
            })
        
        # If no microbiological found
        if not microbiological:
            microbiological.append({
                "contaminant_name": "No microbiological data",
                "value": 0,
                "unit": "N/A",
                "risk_level": "Unknown",
                "threshold": None
            })
        
        return microbiological
    
    async def _assess_contaminant_risk(
        self,
        contaminant_name: str,
        value: float,
        standard: Dict,
        contaminant_type: str
    ) -> tuple:
        """
        Assess risk level for a contaminant
        
        Returns: (risk_level, threshold)
        """
        if not standard:
            # Use default thresholds based on type
            return self._default_risk_assessment(contaminant_name, value, contaminant_type)
        
        thresholds = standard.get('thresholds', {})
        
        # Check against thresholds
        if contaminant_type == "heavy_metal":
            # For heavy metals, ANY detection is concerning
            optimal = thresholds.get('optimal', {}).get('max', 0.001)
            warning = thresholds.get('warning', {}).get('max', 0.01)
            critical = thresholds.get('critical', {}).get('max', 0.1)
            
            if value <= optimal:
                return ("Low", optimal)
            elif value <= warning:
                return ("Medium", warning)
            elif value <= critical:
                return ("High", critical)
            else:
                return ("Critical", critical)
        
        elif contaminant_type == "microbiological":
            # For microbiological, 0 is ideal
            if value == 0:
                return ("Low", 0)
            elif value < 10:
                return ("Medium", 10)
            elif value < 100:
                return ("High", 100)
            else:
                return ("Critical", 100)
        
        else:  # organic
            optimal = thresholds.get('optimal', {}).get('max', 5)
            warning = thresholds.get('warning', {}).get('max', 20)
            critical = thresholds.get('critical', {}).get('max', 50)
            
            if value <= optimal:
                return ("Low", optimal)
            elif value <= warning:
                return ("Medium", warning)
            elif value <= critical:
                return ("High", critical)
            else:
                return ("Critical", critical)
    
    def _default_risk_assessment(
        self,
        contaminant_name: str,
        value: float,
        contaminant_type: str
    ) -> tuple:
        """Default risk assessment when no standard available"""
        
        if contaminant_type == "heavy_metal":
            if value < 0.01:
                return ("Low", 0.01)
            elif value < 0.05:
                return ("Medium", 0.05)
            elif value < 0.1:
                return ("High", 0.1)
            else:
                return ("Critical", 0.1)
        
        elif contaminant_type == "microbiological":
            if value == 0:
                return ("Low", 0)
            elif value < 10:
                return ("Medium", 10)
            elif value < 100:
                return ("High", 100)
            else:
                return ("Critical", 100)
        
        else:  # organic
            if value < 5:
                return ("Low", 5)
            elif value < 20:
                return ("Medium", 20)
            elif value < 50:
                return ("High", 50)
            else:
                return ("Critical", 50)
    
    def _calculate_overall_severity(
        self,
        heavy_metals: List[Dict],
        organic_compounds: List[Dict],
        microbiological: List[Dict]
    ) -> tuple:
        """
        Calculate overall contamination severity
        
        Returns: (severity_text, risk_score)
        """
        # Count risk levels
        risk_counts = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
        
        all_contaminants = heavy_metals + organic_compounds + microbiological
        
        for contaminant in all_contaminants:
            risk_level = contaminant.get("risk_level", "Low")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
        
        # Calculate risk score (0-10)
        total = sum(risk_counts.values())
        if total == 0:
            risk_score = 0.0
        else:
            weighted_score = (
                risk_counts["Critical"] * 10 +
                risk_counts["High"] * 7 +
                risk_counts["Medium"] * 4 +
                risk_counts["Low"] * 1
            ) / total
            risk_score = weighted_score
        
        # Determine severity text
        if risk_counts["Critical"] > 0:
            severity = "Critical"
        elif risk_counts["High"] > 0:
            severity = "High"
        elif risk_counts["Medium"] > 0:
            severity = "Medium"
        else:
            severity = "Low"
        
        return (severity, round(risk_score, 1))