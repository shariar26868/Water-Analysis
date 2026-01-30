
"""
Compliance Service - Check regulatory compliance - FIXED VERSION
✅ Fixed value mapping for TDS, Sulphate
✅ Proper parameter matching
✅ Better status determination
"""

import logging
from typing import Dict, Any, List

from app.db.mongo import db

logger = logging.getLogger(__name__)


class ComplianceService:
    """Check water quality compliance against standards - FIXED VERSION"""
    
    async def check_compliance(
        self,
        parameters: Dict[str, Any],
        chemical_status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check compliance against all standards - FIXED
        """
        try:
            logger.info("✓ Checking compliance against standards")
            
            # Get compliance rules from database
            compliance_rules = await db.get_compliance_rules()
            
            if not compliance_rules:
                logger.warning("⚠️ No compliance rules found in database")
                compliance_rules = self._get_default_rules()
            
            items = []
            passed = 0
            failed = 0
            pending = 0
            
            # Check each rule
            for rule in compliance_rules:
                param_name = rule.get('parameter')
                standard = rule.get('standard', 'WHO')
                requirement = rule.get('requirement', {})
                
                # ✅ FIXED: Better parameter finding
                param_key = self._find_parameter_enhanced(parameters, param_name)
                
                if not param_key:
                    # Parameter not tested
                    items.append({
                        "parameter": param_name,
                        "standard": standard,
                        "status": "Pending",
                        "actual_value": None,
                        "required_value": self._format_requirement(requirement),
                        "remarks": "Not tested"
                    })
                    pending += 1
                    continue
                
                actual_value = parameters[param_key].get("value")
                
                # ✅ Check if value is valid
                if actual_value is None or not isinstance(actual_value, (int, float)):
                    items.append({
                        "parameter": param_name,
                        "standard": standard,
                        "status": "Pending",
                        "actual_value": None,
                        "required_value": self._format_requirement(requirement),
                        "remarks": "Invalid or missing value"
                    })
                    pending += 1
                    continue
                
                # Check compliance
                status, remarks = self._check_requirement(actual_value, requirement)
                
                if status == "Passed":
                    passed += 1
                elif status == "Failed":
                    failed += 1
                else:
                    pending += 1
                
                items.append({
                    "parameter": param_name,
                    "standard": standard,
                    "status": status,
                    "actual_value": actual_value,
                    "required_value": self._format_requirement(requirement),
                    "remarks": remarks
                })
                
                logger.info(f"✓ {param_name}: {actual_value} → {status}")
            
            # Calculate overall compliance percentage
            total = passed + failed
            if total > 0:
                overall_compliance = (passed / total) * 100
            else:
                overall_compliance = 0.0
            
            logger.info(f"✅ Compliance check complete - {passed} passed, {failed} failed, {pending} pending")
            
            return {
                "items": items,
                "overall_compliance": round(overall_compliance, 1),
                "passed_count": passed,
                "failed_count": failed,
                "pending_count": pending
            }
            
        except Exception as e:
            logger.error(f"❌ Compliance check failed: {e}")
            raise Exception(f"Compliance check failed: {str(e)}")
    
    def _check_requirement(self, actual_value: Any, requirement: Dict) -> tuple:
        """
        Check if value meets requirement
        
        Returns: (status, remarks)
        """
        if not isinstance(actual_value, (int, float)):
            return ("Pending", "Non-numeric value")
        
        min_val = requirement.get('min')
        max_val = requirement.get('max')
        
        # Range check
        if min_val is not None and max_val is not None:
            if min_val <= actual_value <= max_val:
                return ("Passed", "Within acceptable range")
            else:
                if actual_value < min_val:
                    return ("Failed", f"Below minimum ({min_val})")
                else:
                    return ("Failed", f"Exceeds maximum ({max_val})")
        
        # Only max check
        elif max_val is not None:
            if actual_value <= max_val:
                return ("Passed", "Below maximum limit")
            else:
                return ("Failed", f"Exceeds maximum ({max_val})")
        
        # Only min check
        elif min_val is not None:
            if actual_value >= min_val:
                return ("Passed", "Above minimum limit")
            else:
                return ("Failed", f"Below minimum ({min_val})")
        
        return ("Pending", "No requirement defined")
    
    def _format_requirement(self, requirement: Dict) -> str:
        """
        Format requirement as string
        
        Example: "6.5-8.5" or "≤ 10" or "≥ 5"
        """
        min_val = requirement.get('min')
        max_val = requirement.get('max')
        
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}"
        elif max_val is not None:
            return f"≤ {max_val}"
        elif min_val is not None:
            return f"≥ {min_val}"
        else:
            return "Not specified"
    
    def _find_parameter_enhanced(self, parameters: Dict, search_name: str) -> str:
        """
        ✅ FIXED: Enhanced parameter finding with multiple strategies
        
        Handles:
        - TDS vs Total_Dissolved_Solids
        - Sulfate vs Sulphate
        - Case insensitive matching
        - Underscore/space variations
        """
        # Strategy 1: Direct match (case insensitive)
        for key in parameters.keys():
            if key.lower() == search_name.lower():
                return key
        
        # Strategy 2: Partial match (normalized)
        search_normalized = search_name.lower().replace("_", "").replace(" ", "").replace("-", "")
        
        for key in parameters.keys():
            key_normalized = key.lower().replace("_", "").replace(" ", "").replace("-", "")
            
            if search_normalized == key_normalized:
                return key
        
        # Strategy 3: Contains match
        search_lower = search_name.lower()
        
        for key in parameters.keys():
            key_lower = key.lower()
            
            if search_lower in key_lower or key_lower in search_lower:
                return key
        
        # Strategy 4: Special aliases
        aliases = {
            "tds": ["total_dissolved_solids", "totaldissolvedsolids", "dissolved_solids"],
            "sulfate": ["sulphate", "so4"],
            "sulphate": ["sulfate", "so4"],
            "bacteria_count": ["total_coliform", "coliform", "bacteria"],
            "hardness": ["total_hardness", "totalhardness"],
            "turbidity": ["turb"],
        }
        
        search_lower = search_name.lower().replace("_", "").replace(" ", "")
        
        if search_lower in aliases:
            for alias in aliases[search_lower]:
                for key in parameters.keys():
                    key_normalized = key.lower().replace("_", "").replace(" ", "")
                    if alias in key_normalized or key_normalized in alias:
                        return key
        
        # Not found
        return None
    
    def _get_default_rules(self) -> List[Dict]:
        """Default compliance rules (WHO standards)"""
        return [
            {
                "parameter": "pH",
                "standard": "WHO",
                "requirement": {"min": 6.5, "max": 8.5}
            },
            {
                "parameter": "TDS",
                "standard": "WHO",
                "requirement": {"max": 1000}
            },
            {
                "parameter": "Turbidity",
                "standard": "WHO",
                "requirement": {"max": 5}
            },
            {
                "parameter": "Chloride",
                "standard": "WHO",
                "requirement": {"max": 250}
            },
            {
                "parameter": "Sulfate",
                "standard": "WHO",
                "requirement": {"max": 250}
            },
            {
                "parameter": "Nitrate",
                "standard": "WHO",
                "requirement": {"max": 50}
            },
            {
                "parameter": "Fluoride",
                "standard": "WHO",
                "requirement": {"max": 1.5}
            },
            {
                "parameter": "Iron",
                "standard": "WHO",
                "requirement": {"max": 0.3}
            },
            {
                "parameter": "Bacteria_Count",
                "standard": "WHO",
                "requirement": {"max": 0}
            },
            {
                "parameter": "Lead",
                "standard": "WHO",
                "requirement": {"max": 0.01}
            },
            {
                "parameter": "Arsenic",
                "standard": "WHO",
                "requirement": {"max": 0.01}
            },
            {
                "parameter": "Mercury",
                "standard": "WHO",
                "requirement": {"max": 0.001}
            }
        ]