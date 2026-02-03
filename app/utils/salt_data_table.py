"""
Salt Threshold Data Table
Defines acceptable ranges for mineral saturation indices
Used in "Where Can I Treat" analysis to determine green/yellow/red zones
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ========================================
# SALT THRESHOLDS DATABASE
# ========================================

SALT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    # ========================================
    # CALCIUM CARBONATE (Most Common)
    # ========================================
    "Calcite": {
        "target_SI": 0.3,
        "cushion_percent": 20,  # 20% safety margin
        "green_range": (-0.5, 0.5),
        "yellow_range": (0.5, 1.0),
        "red_range": (1.0, float('inf')),
        "description": "Calcium carbonate (most common scale)",
        "treatment_target": "Maintain slight supersaturation for corrosion protection"
    },
    
    "Aragonite": {
        "target_SI": 0.2,
        "cushion_percent": 20,
        "green_range": (-0.5, 0.4),
        "yellow_range": (0.4, 0.8),
        "red_range": (0.8, float('inf')),
        "description": "Calcium carbonate polymorph",
        "treatment_target": "Slightly lower than calcite"
    },
    
    # ========================================
    # CALCIUM SULFATE
    # ========================================
    "Gypsum": {
        "target_SI": -0.2,
        "cushion_percent": 15,
        "green_range": (-1.0, 0.0),
        "yellow_range": (0.0, 0.3),
        "red_range": (0.3, float('inf')),
        "description": "Calcium sulfate dihydrate (CaSO4·2H2O)",
        "treatment_target": "Keep undersaturated"
    },
    
    "Anhydrite": {
        "target_SI": -0.3,
        "cushion_percent": 15,
        "green_range": (-1.0, -0.1),
        "yellow_range": (-0.1, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Anhydrous calcium sulfate (CaSO4)",
        "treatment_target": "Keep undersaturated"
    },
    
    # ========================================
    # CALCIUM PHOSPHATE
    # ========================================
    "Hydroxyapatite": {
        "target_SI": -1.0,
        "cushion_percent": 25,
        "green_range": (-3.0, -0.5),
        "yellow_range": (-0.5, 0.0),
        "red_range": (0.0, float('inf')),
        "description": "Calcium phosphate (Ca5(PO4)3OH)",
        "treatment_target": "Keep well undersaturated"
    },
    
    "Tricalcium-phosphate": {
        "target_SI": -1.5,
        "cushion_percent": 25,
        "green_range": (-4.0, -1.0),
        "yellow_range": (-1.0, -0.5),
        "red_range": (-0.5, float('inf')),
        "description": "Ca3(PO4)2",
        "treatment_target": "Keep well undersaturated"
    },
    
    # ========================================
    # SILICA / SILICATES
    # ========================================
    "SiO2(a)": {
        "target_SI": -0.5,
        "cushion_percent": 30,
        "green_range": (-2.0, -0.2),
        "yellow_range": (-0.2, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Amorphous silica",
        "treatment_target": "Keep undersaturated - silica scale is difficult to remove"
    },
    
    "Quartz": {
        "target_SI": 0.0,
        "cushion_percent": 20,
        "green_range": (-0.5, 0.2),
        "yellow_range": (0.2, 0.5),
        "red_range": (0.5, float('inf')),
        "description": "Crystalline silica (SiO2)",
        "treatment_target": "Equilibrium acceptable"
    },
    
    "Chalcedony": {
        "target_SI": -0.2,
        "cushion_percent": 20,
        "green_range": (-0.8, 0.0),
        "yellow_range": (0.0, 0.3),
        "red_range": (0.3, float('inf')),
        "description": "Microcrystalline silica",
        "treatment_target": "Keep slightly undersaturated"
    },
    
    # ========================================
    # MAGNESIUM SALTS
    # ========================================
    "Brucite": {
        "target_SI": -1.0,
        "cushion_percent": 30,
        "green_range": (-3.0, -0.5),
        "yellow_range": (-0.5, 0.0),
        "red_range": (0.0, float('inf')),
        "description": "Magnesium hydroxide (Mg(OH)2)",
        "treatment_target": "Keep undersaturated - forms at high pH"
    },
    
    "Magnesite": {
        "target_SI": -0.5,
        "cushion_percent": 25,
        "green_range": (-2.0, -0.2),
        "yellow_range": (-0.2, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Magnesium carbonate (MgCO3)",
        "treatment_target": "Keep undersaturated"
    },
    
    "Dolomite": {
        "target_SI": 0.0,
        "cushion_percent": 25,
        "green_range": (-1.0, 0.3),
        "yellow_range": (0.3, 0.8),
        "red_range": (0.8, float('inf')),
        "description": "CaMg(CO3)2",
        "treatment_target": "Near equilibrium acceptable"
    },
    
    # ========================================
    # IRON COMPOUNDS
    # ========================================
    "Goethite": {
        "target_SI": -1.0,
        "cushion_percent": 30,
        "green_range": (-3.0, -0.5),
        "yellow_range": (-0.5, 0.0),
        "red_range": (0.0, float('inf')),
        "description": "Iron oxyhydroxide (FeOOH)",
        "treatment_target": "Keep undersaturated"
    },
    
    "Hematite": {
        "target_SI": -1.5,
        "cushion_percent": 30,
        "green_range": (-4.0, -1.0),
        "yellow_range": (-1.0, -0.5),
        "red_range": (-0.5, float('inf')),
        "description": "Iron oxide (Fe2O3)",
        "treatment_target": "Keep well undersaturated"
    },
    
    "Magnetite": {
        "target_SI": -2.0,
        "cushion_percent": 30,
        "green_range": (-5.0, -1.5),
        "yellow_range": (-1.5, -1.0),
        "red_range": (-1.0, float('inf')),
        "description": "Fe3O4",
        "treatment_target": "Keep well undersaturated"
    },
    
    # ========================================
    # BARIUM / STRONTIUM SULFATES
    # ========================================
    "Barite": {
        "target_SI": -0.5,
        "cushion_percent": 20,
        "green_range": (-2.0, -0.2),
        "yellow_range": (-0.2, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Barium sulfate (BaSO4)",
        "treatment_target": "Keep undersaturated - very difficult to remove"
    },
    
    "Celestite": {
        "target_SI": -0.5,
        "cushion_percent": 20,
        "green_range": (-2.0, -0.2),
        "yellow_range": (-0.2, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Strontium sulfate (SrSO4)",
        "treatment_target": "Keep undersaturated"
    },
    
    # ========================================
    # FLUORIDE
    # ========================================
    "Fluorite": {
        "target_SI": -0.8,
        "cushion_percent": 25,
        "green_range": (-2.5, -0.5),
        "yellow_range": (-0.5, 0.0),
        "red_range": (0.0, float('inf')),
        "description": "Calcium fluoride (CaF2)",
        "treatment_target": "Keep undersaturated"
    },
    
    # ========================================
    # HALITE (Sodium Chloride)
    # ========================================
    "Halite": {
        "target_SI": -2.0,
        "cushion_percent": 50,
        "green_range": (-6.0, -1.5),
        "yellow_range": (-1.5, -0.5),
        "red_range": (-0.5, float('inf')),
        "description": "Sodium chloride (NaCl) - rarely a problem in cooling water",
        "treatment_target": "Keep very undersaturated"
    },
    
    # ========================================
    # ZINC PHOSPHATE (Corrosion Inhibitor Film)
    # ========================================
    "Zn3(PO4)2": {
        "target_SI": 0.1,
        "cushion_percent": 15,
        "green_range": (0.0, 0.3),
        "yellow_range": (-0.2, 0.0),
        "red_range": (0.3, float('inf')),
        "description": "Zinc phosphate - desired protective film",
        "treatment_target": "Slight supersaturation desired for corrosion protection"
    },
    
    # ========================================
    # ALUMINUM SILICATE (If using aluminum-based treatment)
    # ========================================
    "Kaolinite": {
        "target_SI": -1.0,
        "cushion_percent": 30,
        "green_range": (-3.0, -0.5),
        "yellow_range": (-0.5, 0.0),
        "red_range": (0.0, float('inf')),
        "description": "Aluminum silicate (Al2Si2O5(OH)4)",
        "treatment_target": "Keep undersaturated"
    },
    
    # ========================================
    # TIN SILICATE (If using tin-based treatment)
    # ========================================
    "SnO2": {
        "target_SI": -0.5,
        "cushion_percent": 25,
        "green_range": (-2.0, -0.2),
        "yellow_range": (-0.2, 0.2),
        "red_range": (0.2, float('inf')),
        "description": "Tin oxide",
        "treatment_target": "Keep undersaturated"
    }
}


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_salt_threshold(mineral_name: str) -> Optional[Dict[str, Any]]:
    """
    Get threshold data for a specific mineral
    
    Args:
        mineral_name: Name of mineral (e.g., "Calcite", "Gypsum")
    
    Returns:
        Threshold dictionary or None if not found
    """
    # Try exact match
    if mineral_name in SALT_THRESHOLDS:
        return SALT_THRESHOLDS[mineral_name]
    
    # Try case-insensitive match
    mineral_lower = mineral_name.lower()
    for key, value in SALT_THRESHOLDS.items():
        if key.lower() == mineral_lower:
            return value
    
    logger.warning(f"⚠️ No threshold data for mineral: {mineral_name}")
    return None


def classify_si_value(mineral_name: str, si_value: float) -> str:
    """
    Classify SI value as green/yellow/red
    
    Args:
        mineral_name: Name of mineral
        si_value: Saturation index value
    
    Returns:
        "green", "yellow", or "red"
    """
    threshold = get_salt_threshold(mineral_name)
    
    if not threshold:
        # Default classification
        if -0.5 <= si_value <= 0.5:
            return "green"
        elif -1.0 <= si_value <= 1.0:
            return "yellow"
        else:
            return "red"
    
    # Use defined ranges
    green_range = threshold["green_range"]
    yellow_range = threshold["yellow_range"]
    
    if green_range[0] <= si_value <= green_range[1]:
        return "green"
    elif yellow_range[0] <= si_value <= yellow_range[1]:
        return "yellow"
    else:
        return "red"


def get_all_minerals() -> list:
    """Get list of all minerals with thresholds defined"""
    return list(SALT_THRESHOLDS.keys())


def get_common_scale_formers() -> list:
    """Get list of most common scale-forming minerals"""
    return [
        "Calcite",
        "Aragonite",
        "Gypsum",
        "SiO2(a)",
        "Barite"
    ]


def get_treatment_targets() -> Dict[str, str]:
    """Get treatment targets for all minerals"""
    return {
        mineral: data["treatment_target"]
        for mineral, data in SALT_THRESHOLDS.items()
    }