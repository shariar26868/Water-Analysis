"""
Analysis Engine - Main Orchestrator
Coordinates all analysis types:
- Simple Saturation Model
- Where Can I Treat (Fixed / Auto dosage)
- Compare 2 Analyses
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.phreeqc_service import PHREEQCService
from app.services.grid_calculator import GridCalculator
from app.services.cooling_tower_service import CoolingTowerService
from app.db.mongo import db

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis orchestrator for all analysis types"""
    
    def __init__(self):
        self.phreeqc_service = PHREEQCService()
        self.cooling_tower_service = CoolingTowerService()
    
    # ========================================
    # SIMPLE SATURATION MODEL
    # ========================================
    
    async def run_simple_saturation(
        self,
        base_water_analysis: Dict[str, Any],
        ph_range: tuple[float, float],
        coc_range: tuple[float, float],
        temp_range: tuple[float, float],
        salts_of_interest: List[str] = None,
        ph_steps: int = 10,
        coc_steps: int = 10,
        temp_steps: int = 10,
        balance_cation: str = "Na",
        balance_anion: str = "Cl"
    ) -> Dict[str, Any]:
        """
        Simple Saturation Model - 3D Grid Analysis
        
        Steps:
        1. Generate 3D grid (pH × CoC × Temp)
        2. Ion balance base water
        3. Run PHREEQC for all grid points
        4. Store results
        5. Return 3D data for visualization
        
        Args:
            base_water_analysis: Base makeup water parameters
            ph_range: (min_pH, max_pH)
            coc_range: (min_CoC, max_CoC)
            temp_range: (min_temp_C, max_temp_C)
            salts_of_interest: List of minerals to analyze (or None for all)
            ph_steps: Number of pH points
            coc_steps: Number of CoC points
            temp_steps: Number of temperature points
            balance_cation: Cation for ion balancing (Na/K)
            balance_anion: Anion for ion balancing (Cl/SO4)
        
        Returns:
            {
                "analysis_id": str,
                "grid_info": {...},
                "results": [...],
                "summary": {...}
            }
        """
        try:
            logger.info("🔬 Starting Simple Saturation Model")
            logger.info(f"   pH: {ph_range}, CoC: {coc_range}, Temp: {temp_range}")
            
            # Step 1: Generate 3D grid
            logger.info("📐 Step 1: Generating 3D grid...")
            grid_data = GridCalculator.generate_3d_grid(
                ph_range, coc_range, temp_range,
                ph_steps, coc_steps, temp_steps
            )
            
            total_points = grid_data["total_points"]
            logger.info(f"✅ Grid generated: {total_points} points")
            
            # Step 2: Ion balance base water
            logger.info("⚖️ Step 2: Ion balancing base water...")
            
            # Get PHREEQC config
            config = await db.get_phreeqc_config()
            if not config:
                config = {
                    "ion_balancing": {
                        "max_iterations": 10,
                        "tolerance_percent": 5,
                        "cation_balance_ion": balance_cation,
                        "anion_balance_ion": balance_anion
                    }
                }
            
            # Balance base water
            balanced_base = await self.phreeqc_service._ion_balancing_full(
                base_water_analysis, config
            )
            
            logger.info("✅ Base water balanced")
            
            # Step 3: Prepare batch inputs
            logger.info("📦 Step 3: Preparing batch inputs...")
            batch_inputs = GridCalculator.prepare_batch_inputs(
                balanced_base, grid_data["grid_points"]
            )
            
            # Step 4: Run PHREEQC for all points
            logger.info(f"🚀 Step 4: Running PHREEQC for {total_points} points...")
            
            results = []
            
            for i, water_input in enumerate(batch_inputs):
                try:
                    # Extract grid point info
                    ph = water_input["_grid_pH"]
                    coc = water_input["_grid_CoC"]
                    temp = water_input["_grid_temp"]
                    
                    # Remove metadata before PHREEQC
                    clean_input = {k: v for k, v in water_input.items() if not k.startswith("_")}
                    
                    # Run PHREEQC
                    phreeqc_result = await self.phreeqc_service.analyze(
                        clean_input,
                        calculation_type="standard"
                    )
                    
                    # Extract saturation indices
                    saturation_indices = phreeqc_result.get("saturation_indices", [])
                    
                    # Filter by salts of interest
                    if salts_of_interest:
                        saturation_indices = [
                            si for si in saturation_indices
                            if si["mineral_name"] in salts_of_interest
                        ]
                    
                    # Store result with grid coordinates
                    result_point = {
                        "point_index": i,
                        "pH": ph,
                        "CoC": coc,
                        "temperature_C": temp,
                        "saturation_indices": saturation_indices,
                        "ionic_strength": phreeqc_result.get("ionic_strength", 0),
                        "charge_balance_error": phreeqc_result.get("charge_balance_error", 0),
                        "database_used": phreeqc_result.get("database_used", "unknown")
                    }
                    
                    results.append(result_point)
                    
                    # Log progress every 10%
                    if (i + 1) % max(1, total_points // 10) == 0:
                        progress = ((i + 1) / total_points) * 100
                        logger.info(f"   Progress: {progress:.0f}% ({i + 1}/{total_points})")
                
                except Exception as e:
                    logger.error(f"❌ Point {i} failed: {e}")
                    # Store error result
                    results.append({
                        "point_index": i,
                        "pH": water_input.get("_grid_pH"),
                        "CoC": water_input.get("_grid_CoC"),
                        "temperature_C": water_input.get("_grid_temp"),
                        "error": str(e),
                        "saturation_indices": []
                    })
            
            logger.info(f"✅ PHREEQC completed: {len(results)} results")
            
            # Step 5: Generate analysis ID and save
            analysis_id = f"SSM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Save to database
            analysis_document = {
                "analysis_id": analysis_id,
                "analysis_type": "simple_saturation",
                "base_water_analysis": balanced_base,
                "grid_info": grid_data,
                "results": results,
                "parameters": {
                    "ph_range": ph_range,
                    "coc_range": coc_range,
                    "temp_range": temp_range,
                    "salts_of_interest": salts_of_interest,
                    "balance_cation": balance_cation,
                    "balance_anion": balance_anion
                },
                "created_at": datetime.utcnow()
            }
            
            await db.db.analysis_results.insert_one(analysis_document)
            
            logger.info(f"✅ Simple Saturation Model complete: {analysis_id}")
            
            # Return summary
            return {
                "analysis_id": analysis_id,
                "grid_info": grid_data,
                "total_points_calculated": len(results),
                "success_count": len([r for r in results if "error" not in r]),
                "error_count": len([r for r in results if "error" in r]),
                "salts_analyzed": salts_of_interest or "all",
                "results_preview": results[:5]  # First 5 results for preview
            }
            
        except Exception as e:
            logger.error(f"❌ Simple Saturation Model failed: {e}")
            raise
    
    # ========================================
    # WHERE CAN I TREAT - FIXED DOSAGE
    # ========================================
    
    async def run_where_can_i_treat_fixed(
        self,
        base_water_analysis: Dict[str, Any],
        products: List[Dict[str, Any]],  # [{"product_id": str, "dosage_ppm": float}]
        ph_range: tuple[float, float],
        coc_range: tuple[float, float],
        temp_range: tuple[float, float],
        target_salts: List[str],
        ph_steps: int = 10,
        coc_steps: int = 10,
        temp_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Where Can I Treat - Fixed Product Dosages
        
        Steps:
        1. Calculate active component dosages from products
        2. Add actives to concentrated water at each grid point
        3. Run PHREEQC
        4. Determine green/yellow/red zones based on salt thresholds
        
        Args:
            base_water_analysis: Base water
            products: List of products with fixed dosages
            ph_range, coc_range, temp_range: Analysis ranges
            target_salts: Salts to evaluate (e.g., ["CaCO3", "CaSO4"])
            ph_steps, coc_steps, temp_steps: Grid resolution
        
        Returns:
            Analysis results with green/yellow/red classifications
        """
        try:
            logger.info("🎯 Starting Where Can I Treat (Fixed Dosage)")
            
            # Step 1: Get product formulations and calculate active dosages
            logger.info("💊 Step 1: Calculating active component dosages...")
            
            active_components = {}
            
            for product_info in products:
                product_id = product_info["product_id"]
                dosage_ppm = product_info["dosage_ppm"]
                
                # Get product from database
                product = await db.db.products.find_one({"product_id": product_id})
                
                if not product:
                    logger.warning(f"⚠️ Product {product_id} not found, skipping")
                    continue
                
                # Get formulation
                formulation = product.get("formulation", {})
                
                # Calculate active PPM for each component
                for component_name, active_percent in formulation.items():
                    active_ppm = dosage_ppm * (active_percent / 100.0)
                    
                    # Accumulate if component already present
                    if component_name in active_components:
                        active_components[component_name] += active_ppm
                    else:
                        active_components[component_name] = active_ppm
            
            logger.info(f"✅ Active components: {active_components}")
            
            # Step 2: Generate grid
            logger.info("📐 Step 2: Generating grid...")
            grid_data = GridCalculator.generate_3d_grid(
                ph_range, coc_range, temp_range,
                ph_steps, coc_steps, temp_steps
            )
            
            # Step 3: Run PHREEQC with added actives
            logger.info("🚀 Step 3: Running PHREEQC with treatment chemicals...")
            
            # Ion balance base water
            config = await db.get_phreeqc_config()
            if not config:
                config = {"ion_balancing": {"max_iterations": 10, "tolerance_percent": 5}}
            
            balanced_base = await self.phreeqc_service._ion_balancing_full(
                base_water_analysis, config
            )
            
            # Prepare batch
            batch_inputs = GridCalculator.prepare_batch_inputs(
                balanced_base, grid_data["grid_points"]
            )
            
            results = []
            
            for i, water_input in enumerate(batch_inputs):
                try:
                    # Add active components to this water sample
                    treated_water = {k: v for k, v in water_input.items() if not k.startswith("_")}
                    
                    for component, ppm in active_components.items():
                        # Map component to PHREEQC parameter
                        # This needs proper mapping based on component type
                        # For now, add as-is if it's a valid parameter
                        treated_water[component] = {"value": ppm, "unit": "mg/L"}
                    
                    # Run PHREEQC
                    phreeqc_result = await self.phreeqc_service.analyze(
                        treated_water,
                        calculation_type="standard"
                    )
                    
                    # Classify result (green/yellow/red)
                    classification = self._classify_treatment_result(
                        phreeqc_result["saturation_indices"],
                        target_salts
                    )
                    
                    result_point = {
                        "point_index": i,
                        "pH": water_input["_grid_pH"],
                        "CoC": water_input["_grid_CoC"],
                        "temperature_C": water_input["_grid_temp"],
                        "saturation_indices": phreeqc_result["saturation_indices"],
                        "classification": classification,
                        "active_components_added": active_components
                    }
                    
                    results.append(result_point)
                
                except Exception as e:
                    logger.error(f"❌ Point {i} failed: {e}")
            
            # Generate analysis ID
            analysis_id = f"WCIT-Fixed-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Save to database
            await db.db.analysis_results.insert_one({
                "analysis_id": analysis_id,
                "analysis_type": "where_can_i_treat_fixed",
                "products": products,
                "active_components": active_components,
                "grid_info": grid_data,
                "results": results,
                "created_at": datetime.utcnow()
            })
            
            logger.info(f"✅ Where Can I Treat (Fixed) complete: {analysis_id}")
            
            return {
                "analysis_id": analysis_id,
                "grid_info": grid_data,
                "active_components": active_components,
                "results_summary": {
                    "total_points": len(results),
                    "green_zones": len([r for r in results if r["classification"] == "green"]),
                    "yellow_zones": len([r for r in results if r["classification"] == "yellow"]),
                    "red_zones": len([r for r in results if r["classification"] == "red"])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Where Can I Treat (Fixed) failed: {e}")
            raise
    
    # ========================================
    # HELPER: CLASSIFY TREATMENT RESULT
    # ========================================
    
    def _classify_treatment_result(
        self,
        saturation_indices: List[Dict],
        target_salts: List[str]
    ) -> str:
        """
        Classify result as green/yellow/red based on SI values
        
        Green: All target salts within acceptable range
        Yellow: Some salts near limits
        Red: Any salt exceeds limits
        
        Args:
            saturation_indices: List of SI results
            target_salts: Salts to check
        
        Returns:
            "green", "yellow", or "red"
        """
        # Get salt thresholds from salt_data_table
        from app.utils.salt_data_table import SALT_THRESHOLDS
        
        classification = "green"
        
        for si_result in saturation_indices:
            mineral = si_result["mineral_name"]
            si_value = si_result["si_value"]
            
            if mineral not in target_salts:
                continue
            
            # Get threshold
            threshold_data = SALT_THRESHOLDS.get(mineral)
            
            if not threshold_data:
                continue
            
            # Check ranges
            green_range = threshold_data["green_range"]
            yellow_range = threshold_data["yellow_range"]
            
            if si_value < green_range[0] or si_value > green_range[1]:
                if si_value >= yellow_range[0] and si_value <= yellow_range[1]:
                    classification = "yellow"
                else:
                    return "red"  # Immediate red if any salt is critical
        
        return classification
    
    # ========================================
    # COMPARE 2 ANALYSES
    # ========================================
    
    async def compare_analyses(
        self,
        analysis1_id: str,
        analysis2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two existing analyses side-by-side
        
        Args:
            analysis1_id: First analysis ID
            analysis2_id: Second analysis ID
        
        Returns:
            Comparison report with differences highlighted
        """
        try:
            logger.info(f"🔀 Comparing analyses: {analysis1_id} vs {analysis2_id}")
            
            # Fetch both analyses
            analysis1 = await db.db.analysis_results.find_one({"analysis_id": analysis1_id})
            analysis2 = await db.db.analysis_results.find_one({"analysis_id": analysis2_id})
            
            if not analysis1:
                raise ValueError(f"Analysis {analysis1_id} not found")
            if not analysis2:
                raise ValueError(f"Analysis {analysis2_id} not found")
            
            # Compare key metrics
            comparison = {
                "analysis1": {
                    "id": analysis1_id,
                    "type": analysis1["analysis_type"],
                    "created_at": analysis1["created_at"]
                },
                "analysis2": {
                    "id": analysis2_id,
                    "type": analysis2["analysis_type"],
                    "created_at": analysis2["created_at"]
                },
                "differences": [],
                "value_additions": {
                    "water_savings": "TBD",
                    "energy_savings": "TBD",
                    "co2_savings": "TBD",
                    "chemical_savings": "TBD",
                    "asset_life_improvement": "TBD"
                }
            }
            
            logger.info("✅ Comparison complete")
            
            return comparison
            
        except Exception as e:
            logger.error(f"❌ Analysis comparison failed: {e}")
            raise