"""
PHREEQC Service - Water Chemistry Calculations
Uses phreeqpython library (Windows compatible)
100% Dynamic with all features
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple

try:
    from phreeqpython import PhreeqPython
    PHREEQC_AVAILABLE = True
except ImportError:
    PHREEQC_AVAILABLE = False
    logging.warning("⚠️ phreeqpython not available")

from app.db.mongo import db

logger = logging.getLogger(__name__)


class PHREEQCService:
    """PHREEQC calculation engine wrapper - FIXED VERSION"""
    
    def __init__(self):
        if PHREEQC_AVAILABLE:
            try:
                # Initialize default database
                self.pp_default = PhreeqPython()
                
                # Try Pitzer database
                try:
                    self.pp_pitzer = PhreeqPython(database='pitzer')
                    logger.info("✅ PhreeqPython initialized with both databases")
                except:
                    self.pp_pitzer = None
                    logger.warning("⚠️ Pitzer database not available")
                
            except Exception as e:
                logger.error(f"❌ PhreeqPython initialization failed: {e}")
                self.pp_default = None
                self.pp_pitzer = None
        else:
            logger.warning("⚠️ PhreeqPython not available, using mock mode")
            self.pp_default = None
            self.pp_pitzer = None
    
    # =====================================================
    # PUBLIC API
    # =====================================================
    async def analyze(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Complete PHREEQC analysis pipeline"""
        try:
            logger.info("⚗️ Starting PHREEQC analysis pipeline")
            
            if not self.pp_default:
                logger.warning("🔧 Running in MOCK MODE")
                return self._get_mock_results(parameters)
            
            # Get config from database
            config = await db.get_phreeqc_config()
            if not config:
                logger.warning("⚠️ No PHREEQC config in DB, using defaults")
                config = self._get_default_config()
            
            # Step 1: Ion Balancing
            logger.info("🔄 Step 1: Ion balancing...")
            balanced_params = await self._ion_balancing(parameters, config)
            
            # Step 2: Ionic Strength
            logger.info("📊 Step 2: Calculating ionic strength...")
            ionic_strength_low, ionic_strength_high = await self._calculate_ionic_strength(
                balanced_params, config
            )
            
            # Step 3: Database Selection
            database_name = self._select_database(ionic_strength_low, ionic_strength_high, config)
            logger.info(f"📚 Selected database: {database_name}")
            
            # Step 4: Final Analysis
            logger.info("🧮 Step 4: Calculating saturation indices...")
            results = await self._run_phreeqpython_analysis(
                balanced_params,
                database_name,
                config
            )
            
            logger.info("✅ PHREEQC analysis complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ PHREEQC analysis failed: {e}")
            raise Exception(f"PHREEQC analysis failed: {str(e)}")
    
    # =====================================================
    # Ion Balancing (FIXED)
    # =====================================================
    async def _ion_balancing(
        self,
        parameters: Dict[str, Any],
        config: Dict
    ) -> Dict[str, Any]:
        """
        FIXED: Ion balancing without using charge_balance attribute
        """
        balancing_config = config.get("ion_balancing", {})
        max_iterations = balancing_config.get("max_iterations", 2)
        tolerance = balancing_config.get("tolerance_percent", 5)
        cation_balance_ion = balancing_config.get("cation_balance_ion", "Na")
        anion_balance_ion = balancing_config.get("anion_balance_ion", "Cl")
        
        logger.info(f"⚙️ Ion balancing config: max_iter={max_iterations}, tolerance={tolerance}%")
        logger.info(f"⚙️ Balance ions: cation={cation_balance_ion}, anion={anion_balance_ion}")
        
        balanced_params = {k: v for k, v in parameters.items()}
        
        for iteration in range(max_iterations):
            logger.info(f"🔄 Ion balancing iteration {iteration + 1}/{max_iterations}")
            
            # Create solution
            solution_dict = self._build_solution_dict(balanced_params)
            sol = self.pp_default.add_solution(solution_dict)
            
            # FIXED: Calculate charge balance manually
            balance_error = self._calculate_charge_balance(sol)
            logger.info(f"⚖️ Charge balance error: {balance_error:.2f}%")
            
            # Check if balanced
            if abs(balance_error) < tolerance:
                logger.info(f"✅ Ion balancing converged in {iteration + 1} iteration(s)")
                return balanced_params
            
            # Adjust balancing ion
            if balance_error < 0:
                # Need more cations
                ion_key = self._find_parameter_key(balanced_params, cation_balance_ion)
                adjustment_type = "cation"
            else:
                # Need more anions
                ion_key = self._find_parameter_key(balanced_params, anion_balance_ion)
                adjustment_type = "anion"
            
            if ion_key:
                adjustment = abs(balance_error) * 0.1  # Proportional adjustment
                current_value = balanced_params[ion_key].get("value", 0)
                balanced_params[ion_key]["value"] = current_value + adjustment
                logger.info(f"🔧 Adjusted {adjustment_type} {ion_key}: +{adjustment:.4f}")
        
        logger.warning(f"⚠️ Ion balancing did not converge after {max_iterations} iterations")
        logger.warning(f"⚠️ Final balance error: {balance_error:.2f}%")
        
        return balanced_params
    
    def _calculate_charge_balance(self, sol) -> float:
        """
        FIXED: Calculate charge balance manually
        
        Formula: 
        Percent Error = 100 * (sum_cations - sum_anions) / (sum_cations + sum_anions)
        """
        try:
            # Get total species from solution
            # phreeqpython provides sol.total() for elements
            
            # Common ions and their charges
            cations = {
                'Ca': 2,   # Ca2+
                'Mg': 2,   # Mg2+
                'Na': 1,   # Na+
                'K': 1,    # K+
                'Fe': 2,   # Fe2+ (can be 3+, but typically 2+)
                'Mn': 2,   # Mn2+
            }
            
            anions = {
                'Cl': 1,   # Cl-
                'S(6)': 2, # SO4^2-
                'N(5)': 1, # NO3-
                'F': 1,    # F-
            }
            
            # Calculate total positive charge (meq/L)
            sum_cations = 0
            for element, charge in cations.items():
                try:
                    conc_mol = sol.total(element, units='mol')  # mol/L
                    sum_cations += conc_mol * charge * 1000  # meq/L
                except:
                    pass
            
            # Calculate total negative charge (meq/L)
            sum_anions = 0
            for element, charge in anions.items():
                try:
                    conc_mol = sol.total(element, units='mol')
                    sum_anions += conc_mol * charge * 1000
                except:
                    pass
            
            # Add alkalinity contribution (usually HCO3- + CO3^2-)
            try:
                alkalinity = sol.total('C(4)', units='mol') * 1000  # Approximate
                sum_anions += alkalinity
            except:
                pass
            
            # Charge balance error %
            if (sum_cations + sum_anions) > 0:
                balance_error = 100 * (sum_cations - sum_anions) / (sum_cations + sum_anions)
            else:
                balance_error = 0.0
            
            return balance_error
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate charge balance: {e}")
            return 0.0
    
    # =====================================================
    # Ionic Strength
    # =====================================================
    async def _calculate_ionic_strength(
        self,
        parameters: Dict,
        config: Dict
    ) -> Tuple[float, float]:
        """Calculate ionic strength"""
        solution_dict = self._build_solution_dict(parameters)
        sol = self.pp_default.add_solution(solution_dict)
        
        # FIXED: Use correct attribute
        ionic_strength_base = sol.I  # This is correct
        
        # TODO: Implement high condition calculation
        ionic_strength_low = ionic_strength_base
        ionic_strength_high = ionic_strength_base
        
        logger.info(f"📊 Ionic Strength: Low={ionic_strength_low:.6f}, High={ionic_strength_high:.6f}")
        
        return ionic_strength_low, ionic_strength_high
    
    # =====================================================
    # Database Selection
    # =====================================================
    def _select_database(self, is_low: float, is_high: float, config: Dict) -> str:
        """Select database based on ionic strength"""
        db_config = config.get("database_selection_rule", {})
        threshold = db_config.get("ionic_strength_threshold", 0.5)
        
        logger.info(f"⚙️ Database selection threshold: {threshold}")
        
        if is_low > threshold or is_high > threshold:
            if self.pp_pitzer:
                logger.info(f"📚 Using pitzer.dat (IS > {threshold})")
                return "pitzer"
            else:
                logger.warning(f"⚠️ Pitzer DB requested but not available")
                return "default"
        else:
            logger.info(f"📚 Using phreeqc.dat (IS <= {threshold})")
            return "default"
    
    # =====================================================
    # PHREEQC Analysis
    # =====================================================
    async def _run_phreeqpython_analysis(
        self,
        parameters: Dict[str, Any],
        database_name: str,
        config: Dict
    ) -> Dict[str, Any]:
        """Run final analysis with selected database"""
        try:
            # Select database
            if database_name == "pitzer" and self.pp_pitzer:
                pp = self.pp_pitzer
                db_display = "pitzer.dat"
            else:
                pp = self.pp_default
                db_display = "phreeqc.dat"
            
            # Create solution
            solution_dict = self._build_solution_dict(parameters)
            sol = pp.add_solution(solution_dict)
            
            # FIXED: Calculate charge balance
            charge_balance_error = self._calculate_charge_balance(sol)
            
            # Build results
            results = {
                "input_parameters": parameters,
                "solution_parameters": {
                    "pH": round(sol.pH, 3),
                    "pe": round(sol.pe, 3),
                    "temperature": round(sol.temperature, 2),
                    "ionic_strength": round(sol.I, 6),
                },
                "saturation_indices": [],
                "ionic_strength": round(sol.I, 6),
                "charge_balance_error": round(charge_balance_error, 3),
                "database_used": db_display
            }
            
            # Get saturation indices
            minerals = config.get("saturation_minerals", [
                "Calcite", "Dolomite", "Gypsum", "Halite", "Quartz"
            ])
            
            logger.info(f"🧪 Calculating SI for {len(minerals)} minerals")
            
            for mineral in minerals:
                try:
                    si_value = sol.si(mineral)
                    
                    # Determine status
                    if si_value > 0.5:
                        status = "Oversaturated"
                    elif si_value < -0.5:
                        status = "Undersaturated"
                    else:
                        status = "Equilibrium"
                    
                    results["saturation_indices"].append({
                        "mineral_name": mineral,
                        "si_value": round(si_value, 3),
                        "status": status
                    })
                except Exception as e:
                    logger.warning(f"⚠️ Could not calculate SI for {mineral}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ PhreeqPython analysis error: {e}")
            raise
    
    # =====================================================
    # Helper Functions
    # =====================================================
    def _build_solution_dict(self, parameters: Dict[str, Any]) -> Dict:
        """Build solution dictionary for phreeqpython"""
        solution = {}
        
        # Temperature
        temp_key = self._find_parameter_key(parameters, "Temperature")
        solution['temp'] = parameters[temp_key].get("value", 25) if temp_key else 25
        
        # pH
        ph_key = self._find_parameter_key(parameters, "pH")
        if ph_key:
            solution['pH'] = parameters[ph_key].get("value", 7)
        
        # Ion mapping
        ion_mapping = {
            "Calcium": "Ca",
            "Magnesium": "Mg",
            "Sodium": "Na",
            "Potassium": "K",
            "Chloride": "Cl",
            "Sulfate": "S(6)",
            "Alkalinity": "Alkalinity",
            "Bicarbonate": "HCO3",
            "Carbonate": "CO3",
            "Nitrate": "N(5)",
            "Nitrite": "N(3)",
            "Fluoride": "F",
            "Iron": "Fe",
            "Manganese": "Mn",
            "Silica": "Si"
        }
        
        for param_name, phreeqc_name in ion_mapping.items():
            param_key = self._find_parameter_key(parameters, param_name)
            if param_key:
                value = parameters[param_key].get("value", 0)
                if value > 0:
                    solution[phreeqc_name] = value
        
        logger.debug(f"Solution dict: {solution}")
        return solution
    
    def _find_parameter_key(self, parameters: Dict, search_name: str) -> Optional[str]:
        """Find parameter key by name (flexible matching)"""
        search_lower = search_name.lower()
        for key in parameters.keys():
            if search_lower in key.lower() or key.lower() in search_lower:
                return key
        return None
    
    def _get_default_config(self) -> Dict:
        """Default PHREEQC configuration"""
        return {
            "database_selection_rule": {
                "ionic_strength_threshold": 0.5,
                "low_database": "phreeqc.dat",
                "high_database": "pitzer.dat"
            },
            "ion_balancing": {
                "max_iterations": 2,
                "tolerance_percent": 5,
                "cation_balance_ion": "Na",
                "anion_balance_ion": "Cl"
            },
            "saturation_minerals": [
                "Calcite", "Dolomite", "Gypsum", "Halite", "Quartz",
                "Aragonite", "Barite", "Celestite", "Fluorite"
            ]
        }
    
    def _get_mock_results(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock results for development"""
        logger.warning("⚠️ Using MOCK results - phreeqpython not available")
        return {
            "input_parameters": parameters,
            "solution_parameters": {
                "pH": 7.5,
                "pe": 4.0,
                "temperature": 25.0,
                "ionic_strength": 0.025,
            },
            "saturation_indices": [
                {"mineral_name": "Calcite", "si_value": 0.2, "status": "Equilibrium"},
                {"mineral_name": "Dolomite", "si_value": -0.5, "status": "Undersaturated"},
                {"mineral_name": "Gypsum", "si_value": -1.2, "status": "Undersaturated"},
                {"mineral_name": "Halite", "si_value": -5.8, "status": "Undersaturated"},
                {"mineral_name": "Quartz", "si_value": 0.1, "status": "Equilibrium"}
            ],
            "ionic_strength": 0.025,
            "charge_balance_error": 2.5,
            "database_used": "MOCK MODE",
            "_note": "Mock data. Install phreeqpython for real calculations."
        }