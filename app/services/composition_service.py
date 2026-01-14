"""
Composition Service - Chemical composition analysis
Extract key parameters with status
100% Dynamic - No hard-coded parameters
"""

import logging
from typing import Dict, Any, List

from app.db.mongo import db

logger = logging.getLogger(__name__)


class CompositionService:
    """Analyze chemical composition of water sample"""
    
    async def analyze(
        self,
        parameters: Dict[str, Any],
        chemical_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze chemical composition
        
        Returns:
            {
                "parameters": [
                    {
                        "parameter_name": "pH",
                        "value": 7.8,
                        "unit": null,
                        "status": "optimal",
                        "threshold": {...}
                    },
                    ...
                ],
                "summary": "Overall composition analysis..."
            }
        """
        try:
            logger.info("🧪 Analyzing chemical composition")
            
            composition_params = []
            
            # Process each parameter
            for param_name, param_data in parameters.items():
                value = param_data.get("value")
                unit = param_data.get("unit")
                
                # Skip non-numeric
                if not isinstance(value, (int, float)):
                    continue
                
                # Get standard from database
                standard = await db.get_parameter_standard(param_name)
                
                # Determine status
                if standard:
                    status = await self._get_status(value, standard)
                    threshold = standard.get('thresholds', {})
                else:
                    status = "unknown"
                    threshold = None
                
                composition_params.append({
                    "parameter_name": param_name,
                    "value": value,
                    "unit": unit,
                    "status": status,
                    "threshold": threshold
                })
            
            # Generate summary
            summary = await self._generate_summary(composition_params, chemical_status)
            
            logger.info(f"✅ Composition analysis complete - {len(composition_params)} parameters")
            
            return {
                "parameters": composition_params,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"❌ Composition analysis failed: {e}")
            raise Exception(f"Composition analysis failed: {str(e)}")
    
    async def _get_status(self, value: float, standard: Dict) -> str:
        """
        Determine status based on thresholds
        
        Returns: "optimal", "good", "warning", "critical"
        """
        thresholds = standard.get('thresholds', {})
        
        for level in ['optimal', 'good', 'warning', 'critical']:
            threshold = thresholds.get(level, {})
            
            min_val = threshold.get('min', float('-inf'))
            max_val = threshold.get('max', float('inf'))
            
            if min_val <= value <= max_val:
                return level
        
        return "unknown"
    
    async def _generate_summary(
        self,
        composition_params: List[Dict],
        chemical_status: Dict
    ) -> str:
        """
        Generate AI-powered summary of composition
        
        Example: "Water shows slightly elevated TDS (450 mg/L) and moderate hardness..."
        """
        # Count statuses
        status_counts = {
            'optimal': 0,
            'good': 0,
            'warning': 0,
            'critical': 0
        }
        
        for param in composition_params:
            status = param.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
        
        total = sum(status_counts.values())
        
        # Generate summary
        summary_parts = []
        
        if status_counts['critical'] > 0:
            summary_parts.append(f"{status_counts['critical']} parameter(s) in critical range")
        
        if status_counts['warning'] > 0:
            summary_parts.append(f"{status_counts['warning']} parameter(s) need attention")
        
        if status_counts['optimal'] > total * 0.7:
            summary_parts.append("Most parameters are within optimal ranges")
        
        # Add saturation info
        saturation_indices = chemical_status.get('saturation_indices', [])
        oversaturated = [si for si in saturation_indices if si['si_value'] > 0.5]
        
        if oversaturated:
            minerals = [si['mineral_name'] for si in oversaturated]
            summary_parts.append(f"Oversaturation detected: {', '.join(minerals)}")
        
        summary = ". ".join(summary_parts) if summary_parts else "Water composition is within acceptable ranges."
        
        return summary