"""
Cooling Tower Calculations
All cooling water system specific calculations
"""

import logging
import math
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class CoolingTowerService:
    """Cooling tower and cooling water system calculations"""
    
    # ========================================
    # CYCLES OF CONCENTRATION (CoC)
    # ========================================
    
    @staticmethod
    def calculate_coc(
        base_water_ion_mg_l: float,
        concentrated_water_ion_mg_l: float
    ) -> float:
        """
        Calculate Cycles of Concentration
        
        Formula: CoC = Concentrated Ion Value / Base Ion Value
        
        Typically uses: Silica, Calcium, Magnesium, or TDS
        
        Args:
            base_water_ion_mg_l: Ion concentration in makeup water
            concentrated_water_ion_mg_l: Ion concentration in recirculating water
        
        Returns:
            Cycles of concentration (float)
        """
        try:
            if base_water_ion_mg_l == 0:
                logger.warning("⚠️ Base water ion concentration is zero")
                return 1.0
            
            coc = concentrated_water_ion_mg_l / base_water_ion_mg_l
            
            logger.info(f"✅ Cycles of Concentration: {coc:.2f}")
            
            return round(coc, 2)
            
        except Exception as e:
            logger.error(f"❌ CoC calculation failed: {e}")
            raise
    
    @staticmethod
    def concentrate_water(
        base_water_analysis: Dict[str, Any],
        coc: float
    ) -> Dict[str, Any]:
        """
        Calculate concentrated water composition
        
        Formula: Concentrated Value = Base Value × CoC
        
        Args:
            base_water_analysis: Dictionary of parameters with values
            coc: Cycles of concentration
        
        Returns:
            Dictionary with concentrated values
        """
        try:
            concentrated = {}
            
            for param_name, param_data in base_water_analysis.items():
                if isinstance(param_data, dict):
                    value = param_data.get("value")
                    unit = param_data.get("unit")
                    
                    if isinstance(value, (int, float)):
                        # Concentrate the value
                        concentrated_value = value * coc
                        
                        concentrated[param_name] = {
                            "value": concentrated_value,
                            "unit": unit
                        }
                    else:
                        # Keep non-numeric as-is
                        concentrated[param_name] = param_data
                else:
                    concentrated[param_name] = param_data
            
            logger.info(f"✅ Concentrated water at {coc} CoC")
            
            return concentrated
            
        except Exception as e:
            logger.error(f"❌ Water concentration failed: {e}")
            raise
    
    # ========================================
    # EVAPORATION RATE
    # ========================================
    
    @staticmethod
    def calculate_evaporation_rate(
        recirculation_rate_gpm: float,
        delta_t_f: float,  # Cooling tower range in °F
        evaporation_factor_percent: float = 85.0
    ) -> Dict[str, Any]:
        """
        Calculate evaporation rate in cooling tower
        
        Formula: Evap = 0.01 × Recirc × (ΔT / 10) × Evap_Factor
        
        Args:
            recirculation_rate_gpm: Recirculation flow rate (GPM)
            delta_t_f: Temperature drop across tower (°F)
            evaporation_factor_percent: Efficiency factor (default 85%)
        
        Returns:
            {
                "evaporation_rate_gpm": float,
                "evaporation_rate_gpd": float,
                "evaporation_rate_gpy": float
            }
        """
        try:
            evap_factor = evaporation_factor_percent / 100.0
            
            evap_gpm = 0.01 * recirculation_rate_gpm * (delta_t_f / 10.0) * evap_factor
            evap_gpd = evap_gpm * 60 * 24  # GPM to GPD
            evap_gpy = evap_gpd * 365  # GPD to GPY
            
            logger.info(f"✅ Evaporation Rate: {evap_gpm:.2f} GPM ({evap_gpd:.0f} GPD)")
            
            return {
                "evaporation_rate_gpm": round(evap_gpm, 2),
                "evaporation_rate_gpd": round(evap_gpd, 0),
                "evaporation_rate_gpy": round(evap_gpy, 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Evaporation rate calculation failed: {e}")
            raise
    
    # ========================================
    # BLOWDOWN RATE
    # ========================================
    
    @staticmethod
    def calculate_blowdown_rate(
        evaporation_rate_gpm: float,
        coc: float
    ) -> Dict[str, Any]:
        """
        Calculate blowdown rate
        
        Formula: Blowdown = Evaporation / (CoC - 1)
        
        Args:
            evaporation_rate_gpm: Evaporation rate (GPM)
            coc: Cycles of concentration
        
        Returns:
            {
                "blowdown_rate_gpm": float,
                "blowdown_rate_gpd": float,
                "blowdown_rate_gpy": float
            }
        """
        try:
            if coc <= 1:
                logger.warning("⚠️ CoC must be > 1 for blowdown calculation")
                return {
                    "blowdown_rate_gpm": 0.0,
                    "blowdown_rate_gpd": 0.0,
                    "blowdown_rate_gpy": 0.0
                }
            
            bd_gpm = evaporation_rate_gpm / (coc - 1)
            bd_gpd = bd_gpm * 60 * 24
            bd_gpy = bd_gpd * 365
            
            logger.info(f"✅ Blowdown Rate: {bd_gpm:.2f} GPM ({bd_gpd:.0f} GPD)")
            
            return {
                "blowdown_rate_gpm": round(bd_gpm, 2),
                "blowdown_rate_gpd": round(bd_gpd, 0),
                "blowdown_rate_gpy": round(bd_gpy, 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Blowdown rate calculation failed: {e}")
            raise
    
    # ========================================
    # MAKEUP RATE
    # ========================================
    
    @staticmethod
    def calculate_makeup_rate(
        evaporation_rate_gpm: float,
        blowdown_rate_gpm: float,
        recirculation_rate_gpm: float,
        drift_percent: float = 0.1
    ) -> Dict[str, Any]:
        """
        Calculate makeup water rate
        
        Formula: Makeup = Evaporation + Blowdown + Drift
        Where: Drift = Recirculation × (Drift% / 100)
        
        Args:
            evaporation_rate_gpm: Evaporation (GPM)
            blowdown_rate_gpm: Blowdown (GPM)
            recirculation_rate_gpm: Recirculation (GPM)
            drift_percent: Drift as % of recirculation (default 0.1%)
        
        Returns:
            {
                "makeup_rate_gpm": float,
                "makeup_rate_gpd": float,
                "makeup_rate_gpy": float,
                "drift_gpm": float
            }
        """
        try:
            drift_gpm = recirculation_rate_gpm * (drift_percent / 100.0)
            
            makeup_gpm = evaporation_rate_gpm + blowdown_rate_gpm + drift_gpm
            makeup_gpd = makeup_gpm * 60 * 24
            makeup_gpy = makeup_gpd * 365
            
            logger.info(f"✅ Makeup Rate: {makeup_gpm:.2f} GPM ({makeup_gpd:.0f} GPD)")
            
            return {
                "makeup_rate_gpm": round(makeup_gpm, 2),
                "makeup_rate_gpd": round(makeup_gpd, 0),
                "makeup_rate_gpy": round(makeup_gpy, 0),
                "drift_gpm": round(drift_gpm, 3)
            }
            
        except Exception as e:
            logger.error(f"❌ Makeup rate calculation failed: {e}")
            raise
    
    # ========================================
    # COOLING TOWER RANGE
    # ========================================
    
    @staticmethod
    def calculate_tower_range(
        hot_water_temp_f: float,
        cold_water_temp_f: float
    ) -> float:
        """
        Calculate cooling tower range (ΔT)
        
        Formula: Range = Hot Water Temp - Cold Water Temp
        
        Returns:
            Temperature difference in °F
        """
        try:
            range_f = hot_water_temp_f - cold_water_temp_f
            
            logger.info(f"✅ Cooling Tower Range: {range_f}°F")
            
            return round(range_f, 1)
            
        except Exception as e:
            logger.error(f"❌ Tower range calculation failed: {e}")
            raise
    
    # ========================================
    # APPROACH TEMPERATURE
    # ========================================
    
    @staticmethod
    def calculate_approach_temperature(
        cold_water_temp_f: float,
        wet_bulb_temp_f: float
    ) -> float:
        """
        Calculate cooling tower approach temperature
        
        Formula: Approach = Cold Water Temp - Wet Bulb Temp
        
        Returns:
            Approach temperature in °F
        """
        try:
            approach = cold_water_temp_f - wet_bulb_temp_f
            
            logger.info(f"✅ Approach Temperature: {approach}°F")
            
            return round(approach, 1)
            
        except Exception as e:
            logger.error(f"❌ Approach calculation failed: {e}")
            raise
    
    # ========================================
    # TOWER EFFICIENCY
    # ========================================
    
    @staticmethod
    def calculate_tower_efficiency(
        range_f: float,
        approach_f: float
    ) -> Dict[str, Any]:
        """
        Calculate cooling tower efficiency
        
        Formula: Efficiency = (Range / (Range + Approach)) × 100
        
        Returns:
            {
                "efficiency_percent": float,
                "interpretation": str
            }
        """
        try:
            if range_f + approach_f == 0:
                logger.warning("⚠️ Range + Approach = 0, cannot calculate efficiency")
                return {
                    "efficiency_percent": 0.0,
                    "interpretation": "Cannot calculate"
                }
            
            efficiency = (range_f / (range_f + approach_f)) * 100
            
            # Interpretation
            if efficiency >= 80:
                rating = "Excellent"
            elif efficiency >= 70:
                rating = "Good"
            elif efficiency >= 60:
                rating = "Fair"
            else:
                rating = "Poor"
            
            logger.info(f"✅ Tower Efficiency: {efficiency:.1f}% ({rating})")
            
            return {
                "efficiency_percent": round(efficiency, 1),
                "interpretation": f"{rating} efficiency",
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"❌ Efficiency calculation failed: {e}")
            raise
    
    # ========================================
    # HEAT LOAD
    # ========================================
    
    @staticmethod
    def calculate_heat_load(
        recirculation_rate_gpm: float,
        range_f: float
    ) -> Dict[str, Any]:
        """
        Calculate heat load
        
        Formula: Q = 500 × Recirculation Rate × Range
        
        Args:
            recirculation_rate_gpm: GPM
            range_f: Temperature drop (°F)
        
        Returns:
            {
                "heat_load_btu_hr": float,
                "heat_load_tons": float
            }
        """
        try:
            q_btu_hr = 500 * recirculation_rate_gpm * range_f
            q_tons = q_btu_hr / 12000  # 1 ton = 12,000 BTU/hr
            
            logger.info(f"✅ Heat Load: {q_btu_hr:,.0f} BTU/hr ({q_tons:.1f} tons)")
            
            return {
                "heat_load_btu_hr": round(q_btu_hr, 0),
                "heat_load_tons": round(q_tons, 1)
            }
            
        except Exception as e:
            logger.error(f"❌ Heat load calculation failed: {e}")
            raise
    
    # ========================================
    # COOLING TONS ↔ RECIRCULATION RATE
    # ========================================
    
    @staticmethod
    def tons_to_recirculation(
        tons_of_cooling: float,
        range_f: float
    ) -> float:
        """
        Convert cooling tons to recirculation rate
        
        Formula: Recirc = (30 × Tons) / Range
        
        Returns:
            Recirculation rate in GPM
        """
        try:
            if range_f == 0:
                logger.warning("⚠️ Range cannot be zero")
                return 0.0
            
            recirc_gpm = (30 * tons_of_cooling) / range_f
            
            logger.info(f"✅ {tons_of_cooling} tons → {recirc_gpm:.1f} GPM")
            
            return round(recirc_gpm, 1)
            
        except Exception as e:
            logger.error(f"❌ Tons to GPM conversion failed: {e}")
            raise
    
    @staticmethod
    def recirculation_to_tons(
        recirculation_rate_gpm: float,
        range_f: float
    ) -> float:
        """
        Convert recirculation rate to cooling tons
        
        Formula: Tons = (Recirc × Range) / 30
        
        Returns:
            Cooling tons
        """
        try:
            tons = (recirculation_rate_gpm * range_f) / 30
            
            logger.info(f"✅ {recirculation_rate_gpm} GPM → {tons:.1f} tons")
            
            return round(tons, 1)
            
        except Exception as e:
            logger.error(f"❌ GPM to tons conversion failed: {e}")
            raise
    
    # ========================================
    # DISSOLVED OXYGEN
    # ========================================
    
    @staticmethod
    def calculate_dissolved_oxygen(
        water_temp_c: float,
        wet_bulb_temp_c: float
    ) -> Dict[str, Any]:
        """
        Calculate dissolved oxygen in open recirculating cooling water
        
        Formula: DO ≈ 14.6 - 0.41×T_w - 0.05×(T_w - T_wb)
        
        Args:
            water_temp_c: Water temperature (°C)
            wet_bulb_temp_c: Wet bulb temperature (°C)
        
        Returns:
            {
                "dissolved_oxygen_ppm": float,
                "interpretation": str
            }
        """
        try:
            do_ppm = 14.6 - 0.41 * water_temp_c - 0.05 * (water_temp_c - wet_bulb_temp_c)
            
            # Ensure DO is not negative
            do_ppm = max(do_ppm, 0.0)
            
            logger.info(f"✅ Dissolved Oxygen: {do_ppm:.2f} ppm")
            
            return {
                "dissolved_oxygen_ppm": round(do_ppm, 2),
                "interpretation": f"Air-saturated DO at {water_temp_c}°C"
            }
            
        except Exception as e:
            logger.error(f"❌ DO calculation failed: {e}")
            raise