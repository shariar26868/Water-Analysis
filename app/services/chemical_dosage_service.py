"""
Chemical Dosage and Cost Calculations
PPM calculations, chemical usage, customer costs
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ChemicalDosageService:
    """Chemical dosage and cost calculations"""
    
    # Constants
    LBS_PER_GALLON_WATER = 8.34  # Standard water density
    
    # ========================================
    # PPM / MG/L CALCULATIONS
    # ========================================
    
    @staticmethod
    def calculate_ppm(
        lbs_material: float,
        gallons_water: float
    ) -> float:
        """
        Calculate PPM (Parts Per Million)
        
        Formula: PPM = (lbs material / Million lbs water)
        
        Args:
            lbs_material: Pounds of chemical added
            gallons_water: Gallons of water in system
        
        Returns:
            Concentration in PPM (mg/L)
        """
        try:
            # Convert gallons to million lbs
            million_lbs_water = (gallons_water * ChemicalDosageService.LBS_PER_GALLON_WATER) / 1_000_000
            
            if million_lbs_water == 0:
                logger.warning("⚠️ Zero water volume")
                return 0.0
            
            ppm = lbs_material / million_lbs_water
            
            logger.info(f"✅ {lbs_material} lbs in {gallons_water} gal = {ppm:.2f} ppm")
            
            return round(ppm, 2)
            
        except Exception as e:
            logger.error(f"❌ PPM calculation failed: {e}")
            raise
    
    @staticmethod
    def calculate_lbs_from_ppm(
        ppm_dosage: float,
        gallons_water: float
    ) -> float:
        """
        Calculate pounds of chemical from PPM dosage
        
        Formula: lbs = PPM × Million lbs water
        
        Args:
            ppm_dosage: Target concentration (PPM)
            gallons_water: Gallons of water
        
        Returns:
            Pounds of chemical needed
        """
        try:
            million_lbs_water = (gallons_water * ChemicalDosageService.LBS_PER_GALLON_WATER) / 1_000_000
            
            lbs_needed = ppm_dosage * million_lbs_water
            
            logger.info(f"✅ {ppm_dosage} ppm in {gallons_water} gal = {lbs_needed:.2f} lbs")
            
            return round(lbs_needed, 2)
            
        except Exception as e:
            logger.error(f"❌ Lbs from PPM calculation failed: {e}")
            raise
    
    # ========================================
    # CHEMICAL QUANTITY REQUIRED
    # ========================================
    
    @staticmethod
    def calculate_chemical_usage_per_day(
        product_dosage_ppm: float,
        blowdown_rate_gpm: float
    ) -> Dict[str, Any]:
        """
        Calculate chemical quantity required per day
        
        Formula: lbs/day = PPM × Million lbs Blowdown/day
        Where: Million lbs BD/day = BD(gpm) × 60 × 24 × 8.34 / 1,000,000
        
        Args:
            product_dosage_ppm: Product dosage (PPM)
            blowdown_rate_gpm: Blowdown rate (GPM)
        
        Returns:
            {
                "lbs_per_day": float,
                "lbs_per_year": float,
                "million_lbs_blowdown_per_day": float
            }
        """
        try:
            # Calculate million lbs blowdown per day
            million_lbs_bd_per_day = (blowdown_rate_gpm * 60 * 24 * ChemicalDosageService.LBS_PER_GALLON_WATER) / 1_000_000
            
            # Calculate lbs chemical per day
            lbs_per_day = product_dosage_ppm * million_lbs_bd_per_day
            
            # Assume 350 operating days per year (default)
            operating_days_per_year = 350
            lbs_per_year = lbs_per_day * operating_days_per_year
            
            logger.info(f"✅ Chemical usage: {lbs_per_day:.2f} lbs/day, {lbs_per_year:.0f} lbs/year")
            
            return {
                "lbs_per_day": round(lbs_per_day, 2),
                "lbs_per_year": round(lbs_per_year, 0),
                "million_lbs_blowdown_per_day": round(million_lbs_bd_per_day, 6),
                "operating_days_per_year": operating_days_per_year
            }
            
        except Exception as e:
            logger.error(f"❌ Chemical usage calculation failed: {e}")
            raise
    
    @staticmethod
    def calculate_chemical_usage_gallons(
        lbs_required: float,
        density_lbs_per_gal: float
    ) -> float:
        """
        Convert pounds to gallons using density
        
        Formula: Gallons = lbs / density
        
        Args:
            lbs_required: Pounds of chemical
            density_lbs_per_gal: Product density (lbs/gal)
        
        Returns:
            Gallons of chemical
        """
        try:
            if density_lbs_per_gal == 0:
                logger.warning("⚠️ Zero density")
                return 0.0
            
            gallons = lbs_required / density_lbs_per_gal
            
            logger.info(f"✅ {lbs_required} lbs @ {density_lbs_per_gal} lbs/gal = {gallons:.2f} gal")
            
            return round(gallons, 2)
            
        except Exception as e:
            logger.error(f"❌ Gallons conversion failed: {e}")
            raise
    
    # ========================================
    # CUSTOMER USE-COST
    # ========================================
    
    @staticmethod
    def calculate_cost_per_million_lbs_blowdown(
        ppm_dosage: float,
        price_per_lb: float
    ) -> Dict[str, Any]:
        """
        Calculate customer cost
        
        Formula: $/Million lbs BD = PPM × Price($/lb)
        
        Args:
            ppm_dosage: Product dosage (PPM)
            price_per_lb: Product price ($/lb)
        
        Returns:
            {
                "cost_per_million_lbs_blowdown": float,
                "cost_per_day": float (if blowdown rate provided),
                "cost_per_year": float
            }
        """
        try:
            cost_per_million_lbs = ppm_dosage * price_per_lb
            
            logger.info(f"✅ Cost: ${cost_per_million_lbs:.2f} per Million lbs BD")
            
            return {
                "cost_per_million_lbs_blowdown": round(cost_per_million_lbs, 2),
                "ppm_dosage": ppm_dosage,
                "price_per_lb": price_per_lb
            }
            
        except Exception as e:
            logger.error(f"❌ Cost calculation failed: {e}")
            raise
    
    @staticmethod
    def calculate_total_annual_cost(
        ppm_dosage: float,
        price_per_lb: float,
        blowdown_rate_gpm: float,
        operating_days_per_year: int = 350
    ) -> Dict[str, Any]:
        """
        Calculate total annual chemical cost
        
        Args:
            ppm_dosage: Product dosage (PPM)
            price_per_lb: Product price ($/lb)
            blowdown_rate_gpm: Blowdown rate (GPM)
            operating_days_per_year: Operating days (default 350)
        
        Returns:
            {
                "cost_per_day": float,
                "cost_per_year": float,
                "lbs_per_year": float
            }
        """
        try:
            # Calculate usage
            usage = ChemicalDosageService.calculate_chemical_usage_per_day(
                ppm_dosage, blowdown_rate_gpm
            )
            
            lbs_per_day = usage["lbs_per_day"]
            lbs_per_year = lbs_per_day * operating_days_per_year
            
            # Calculate cost
            cost_per_day = lbs_per_day * price_per_lb
            cost_per_year = lbs_per_year * price_per_lb
            
            logger.info(f"✅ Annual cost: ${cost_per_year:,.2f} ({lbs_per_year:.0f} lbs @ ${price_per_lb}/lb)")
            
            return {
                "cost_per_day": round(cost_per_day, 2),
                "cost_per_year": round(cost_per_year, 2),
                "lbs_per_year": round(lbs_per_year, 0),
                "operating_days_per_year": operating_days_per_year
            }
            
        except Exception as e:
            logger.error(f"❌ Annual cost calculation failed: {e}")
            raise
    
    # ========================================
    # ACTIVE COMPONENT CALCULATIONS
    # ========================================
    
    @staticmethod
    def calculate_active_component_dosage(
        product_dosage_ppm: float,
        active_percent: float
    ) -> float:
        """
        Calculate active component PPM from product dosage
        
        Formula: Active PPM = Product PPM × (Active % / 100)
        
        Args:
            product_dosage_ppm: Total product dosage (PPM)
            active_percent: Active ingredient percentage (%)
        
        Returns:
            Active component dosage (PPM)
        """
        try:
            active_ppm = product_dosage_ppm * (active_percent / 100.0)
            
            logger.info(f"✅ {product_dosage_ppm} ppm product @ {active_percent}% active = {active_ppm:.2f} ppm active")
            
            return round(active_ppm, 3)
            
        except Exception as e:
            logger.error(f"❌ Active component calculation failed: {e}")
            raise
    
    @staticmethod
    def calculate_product_dosage_from_active(
        active_ppm_required: float,
        active_percent: float
    ) -> float:
        """
        Calculate product dosage needed to achieve target active PPM
        
        Formula: Product PPM = Active PPM / (Active % / 100)
        
        Args:
            active_ppm_required: Target active component (PPM)
            active_percent: Active ingredient percentage (%)
        
        Returns:
            Product dosage needed (PPM)
        """
        try:
            if active_percent == 0:
                logger.warning("⚠️ Zero active percentage")
                return 0.0
            
            product_ppm = active_ppm_required / (active_percent / 100.0)
            
            logger.info(f"✅ Need {active_ppm_required} ppm active @ {active_percent}% = {product_ppm:.2f} ppm product")
            
            return round(product_ppm, 2)
            
        except Exception as e:
            logger.error(f"❌ Product dosage calculation failed: {e}")
            raise
    
    # ========================================
    # MULTI-COMPONENT PRODUCT CALCULATIONS
    # ========================================
    
    @staticmethod
    def calculate_multi_component_dosages(
        product_dosage_ppm: float,
        formulation: Dict[str, float]  # {"component_name": active_percent}
    ) -> Dict[str, float]:
        """
        Calculate all active component dosages from a multi-component product
        
        Args:
            product_dosage_ppm: Total product dosage (PPM)
            formulation: Dict of component names and their active %
                Example: {"Phosphonate": 15.0, "Polymer": 5.0, "Azole": 2.5}
        
        Returns:
            Dict of component names and their PPM dosages
        """
        try:
            component_dosages = {}
            
            for component_name, active_percent in formulation.items():
                active_ppm = ChemicalDosageService.calculate_active_component_dosage(
                    product_dosage_ppm, active_percent
                )
                component_dosages[component_name] = active_ppm
            
            logger.info(f"✅ Multi-component dosages calculated for {len(formulation)} components")
            
            return component_dosages
            
        except Exception as e:
            logger.error(f"❌ Multi-component calculation failed: {e}")
            raise