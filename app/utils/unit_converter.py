"""
Unit Conversion Utilities
Convert between Metric and Imperial units
User can input in their preferred units, stored in common unit, returned in original units
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UnitConverter:
    """Convert between different unit systems"""
    
    # ========================================
    # TEMPERATURE CONVERSIONS
    # ========================================
    
    @staticmethod
    def celsius_to_fahrenheit(celsius: float) -> float:
        """Convert °C to °F"""
        return (celsius * 9/5) + 32
    
    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert °F to °C"""
        return (fahrenheit - 32) * 5/9
    
    @staticmethod
    def celsius_to_kelvin(celsius: float) -> float:
        """Convert °C to K"""
        return celsius + 273.15
    
    @staticmethod
    def kelvin_to_celsius(kelvin: float) -> float:
        """Convert K to °C"""
        return kelvin - 273.15
    
    @staticmethod
    def convert_temperature(
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Convert temperature between units
        
        Args:
            value: Temperature value
            from_unit: Source unit ('C', 'F', 'K')
            to_unit: Target unit ('C', 'F', 'K')
        
        Returns:
            Converted temperature
        """
        try:
            # Normalize unit strings
            from_unit = from_unit.upper().replace('°', '').strip()
            to_unit = to_unit.upper().replace('°', '').strip()
            
            # Convert to Celsius first
            if from_unit == 'C':
                celsius = value
            elif from_unit == 'F':
                celsius = UnitConverter.fahrenheit_to_celsius(value)
            elif from_unit == 'K':
                celsius = UnitConverter.kelvin_to_celsius(value)
            else:
                raise ValueError(f"Unknown temperature unit: {from_unit}")
            
            # Convert from Celsius to target
            if to_unit == 'C':
                return celsius
            elif to_unit == 'F':
                return UnitConverter.celsius_to_fahrenheit(celsius)
            elif to_unit == 'K':
                return UnitConverter.celsius_to_kelvin(celsius)
            else:
                raise ValueError(f"Unknown temperature unit: {to_unit}")
                
        except Exception as e:
            logger.error(f"❌ Temperature conversion failed: {e}")
            raise
    
    # ========================================
    # CONCENTRATION CONVERSIONS
    # ========================================
    
    @staticmethod
    def convert_concentration(
        value: float,
        from_unit: str,
        to_unit: str,
        molecular_weight: Optional[float] = None
    ) -> float:
        """
        Convert concentration units
        
        Common conversions:
        - mg/L ↔ ppm (identical for dilute solutions)
        - mg/L ↔ meq/L (requires molecular weight)
        - mg/L ↔ mol/L (requires molecular weight)
        - mg/L ↔ grains/gallon (1 gpg = 17.1 mg/L)
        
        Args:
            value: Concentration value
            from_unit: Source unit
            to_unit: Target unit
            molecular_weight: Required for molar conversions
        
        Returns:
            Converted concentration
        """
        try:
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # mg/L ↔ ppm (essentially 1:1 for water)
            if from_unit in ['mg/l', 'ppm'] and to_unit in ['mg/l', 'ppm']:
                return value
            
            # mg/L ↔ grains/gallon
            if from_unit in ['mg/l', 'ppm'] and to_unit == 'gpg':
                return value / 17.1
            
            if from_unit == 'gpg' and to_unit in ['mg/l', 'ppm']:
                return value * 17.1
            
            # mg/L ↔ mol/L (requires molecular weight)
            if from_unit in ['mg/l', 'ppm'] and to_unit in ['mol/l', 'm']:
                if not molecular_weight:
                    raise ValueError("Molecular weight required for molar conversion")
                return (value / 1000) / molecular_weight
            
            if from_unit in ['mol/l', 'm'] and to_unit in ['mg/l', 'ppm']:
                if not molecular_weight:
                    raise ValueError("Molecular weight required for molar conversion")
                return value * molecular_weight * 1000
            
            # mg/L ↔ meq/L (requires molecular weight and charge)
            # Note: For meq/L, need charge as well
            # This is simplified - proper implementation needs charge parameter
            
            raise ValueError(f"Unsupported conversion: {from_unit} → {to_unit}")
            
        except Exception as e:
            logger.error(f"❌ Concentration conversion failed: {e}")
            raise
    
    # ========================================
    # PRESSURE CONVERSIONS
    # ========================================
    
    @staticmethod
    def convert_pressure(
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Convert pressure units
        
        Supported units:
        - psi (pounds per square inch)
        - bar
        - kPa (kilopascals)
        - atm (atmospheres)
        - Pa (pascals)
        
        Args:
            value: Pressure value
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted pressure
        """
        try:
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # Conversion factors to Pa (base unit)
            to_pa = {
                'pa': 1.0,
                'kpa': 1000.0,
                'bar': 100000.0,
                'psi': 6894.76,
                'atm': 101325.0
            }
            
            if from_unit not in to_pa:
                raise ValueError(f"Unknown pressure unit: {from_unit}")
            if to_unit not in to_pa:
                raise ValueError(f"Unknown pressure unit: {to_unit}")
            
            # Convert to Pa, then to target
            pa_value = value * to_pa[from_unit]
            result = pa_value / to_pa[to_unit]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Pressure conversion failed: {e}")
            raise
    
    # ========================================
    # FLOW RATE CONVERSIONS
    # ========================================
    
    @staticmethod
    def convert_flow_rate(
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Convert flow rate units
        
        Supported units:
        - gpm (gallons per minute)
        - gpd (gallons per day)
        - m3/h (cubic meters per hour)
        - m3/d (cubic meters per day)
        - L/min (liters per minute)
        - L/s (liters per second)
        
        Args:
            value: Flow rate value
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted flow rate
        """
        try:
            from_unit = from_unit.lower().strip().replace(' ', '')
            to_unit = to_unit.lower().strip().replace(' ', '')
            
            # Conversion factors to L/min (base unit)
            to_lpm = {
                'l/min': 1.0,
                'lpm': 1.0,
                'l/s': 60.0,
                'lps': 60.0,
                'gpm': 3.78541,
                'gpd': 3.78541 / (24 * 60),
                'm3/h': 1000.0 / 60,
                'm3/d': 1000.0 / (24 * 60)
            }
            
            if from_unit not in to_lpm:
                raise ValueError(f"Unknown flow rate unit: {from_unit}")
            if to_unit not in to_lpm:
                raise ValueError(f"Unknown flow rate unit: {to_unit}")
            
            # Convert to L/min, then to target
            lpm_value = value * to_lpm[from_unit]
            result = lpm_value / to_lpm[to_unit]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Flow rate conversion failed: {e}")
            raise
    
    # ========================================
    # VOLUME CONVERSIONS
    # ========================================
    
    @staticmethod
    def convert_volume(
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Convert volume units
        
        Supported units:
        - gal (US gallons)
        - L (liters)
        - m3 (cubic meters)
        - ft3 (cubic feet)
        
        Args:
            value: Volume value
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted volume
        """
        try:
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # Conversion factors to liters (base unit)
            to_liters = {
                'l': 1.0,
                'liters': 1.0,
                'gal': 3.78541,
                'gallons': 3.78541,
                'm3': 1000.0,
                'ft3': 28.3168
            }
            
            if from_unit not in to_liters:
                raise ValueError(f"Unknown volume unit: {from_unit}")
            if to_unit not in to_liters:
                raise ValueError(f"Unknown volume unit: {to_unit}")
            
            # Convert to liters, then to target
            liters_value = value * to_liters[from_unit]
            result = liters_value / to_liters[to_unit]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Volume conversion failed: {e}")
            raise
    
    # ========================================
    # MASS CONVERSIONS
    # ========================================
    
    @staticmethod
    def convert_mass(
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Convert mass units
        
        Supported units:
        - kg (kilograms)
        - g (grams)
        - lb (pounds)
        - oz (ounces)
        - ton (metric ton)
        
        Args:
            value: Mass value
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted mass
        """
        try:
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # Conversion factors to kg (base unit)
            to_kg = {
                'kg': 1.0,
                'g': 0.001,
                'lb': 0.453592,
                'lbs': 0.453592,
                'oz': 0.0283495,
                'ton': 1000.0,
                'tonne': 1000.0
            }
            
            if from_unit not in to_kg:
                raise ValueError(f"Unknown mass unit: {from_unit}")
            if to_unit not in to_kg:
                raise ValueError(f"Unknown mass unit: {to_unit}")
            
            # Convert to kg, then to target
            kg_value = value * to_kg[from_unit]
            result = kg_value / to_kg[to_unit]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Mass conversion failed: {e}")
            raise
    
    # ========================================
    # PARAMETER CONVERSION WITH AUTO-DETECT
    # ========================================
    
    @staticmethod
    def convert_parameter(
        parameter_name: str,
        value: float,
        from_unit: str,
        to_unit: str
    ) -> float:
        """
        Auto-detect parameter type and convert
        
        Args:
            parameter_name: Name of parameter (e.g., "Temperature", "Calcium")
            value: Value to convert
            from_unit: Source unit
            to_unit: Target unit
        
        Returns:
            Converted value
        """
        try:
            param_lower = parameter_name.lower()
            
            # Temperature parameters
            if 'temp' in param_lower or param_lower == 'temperature':
                return UnitConverter.convert_temperature(value, from_unit, to_unit)
            
            # Pressure parameters
            if 'pressure' in param_lower:
                return UnitConverter.convert_pressure(value, from_unit, to_unit)
            
            # Flow rate parameters
            if any(x in param_lower for x in ['flow', 'rate', 'recirculation', 'makeup', 'blowdown', 'evaporation']):
                return UnitConverter.convert_flow_rate(value, from_unit, to_unit)
            
            # Volume parameters
            if 'volume' in param_lower:
                return UnitConverter.convert_volume(value, from_unit, to_unit)
            
            # Mass parameters
            if any(x in param_lower for x in ['mass', 'weight']):
                return UnitConverter.convert_mass(value, from_unit, to_unit)
            
            # Default: assume concentration
            return UnitConverter.convert_concentration(value, from_unit, to_unit)
            
        except Exception as e:
            logger.error(f"❌ Parameter conversion failed: {e}")
            raise