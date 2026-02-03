"""
3D Grid Calculator for PHREEQC Analysis
Generates pH × CoC × Temperature grids for batch processing
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from itertools import product

logger = logging.getLogger(__name__)


class GridCalculator:
    """Generate 3D analysis grids for PHREEQC batch processing"""
    
    # ========================================
    # 3D GRID GENERATION
    # ========================================
    
    @staticmethod
    def generate_3d_grid(
        ph_range: Tuple[float, float],
        coc_range: Tuple[float, float],
        temp_range: Tuple[float, float],
        ph_steps: int = 10,
        coc_steps: int = 10,
        temp_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Generate 3D grid for pH × CoC × Temperature analysis
        
        Args:
            ph_range: (min_pH, max_pH)
            coc_range: (min_CoC, max_CoC)
            temp_range: (min_temp_C, max_temp_C)
            ph_steps: Number of pH points
            coc_steps: Number of CoC points
            temp_steps: Number of temperature points
        
        Returns:
            {
                "grid_points": List of (pH, CoC, temp) tuples,
                "total_points": int,
                "ph_values": List[float],
                "coc_values": List[float],
                "temp_values": List[float]
            }
        """
        try:
            # Generate linear spacing for each axis
            ph_values = np.linspace(ph_range[0], ph_range[1], ph_steps).tolist()
            coc_values = np.linspace(coc_range[0], coc_range[1], coc_steps).tolist()
            temp_values = np.linspace(temp_range[0], temp_range[1], temp_steps).tolist()
            
            # Generate all combinations (Cartesian product)
            grid_points = list(product(ph_values, coc_values, temp_values))
            
            total_points = len(grid_points)
            
            logger.info(f"✅ Generated 3D grid: {ph_steps}×{coc_steps}×{temp_steps} = {total_points} points")
            logger.info(f"   pH: {ph_range[0]:.1f} to {ph_range[1]:.1f}")
            logger.info(f"   CoC: {coc_range[0]:.1f} to {coc_range[1]:.1f}")
            logger.info(f"   Temp: {temp_range[0]:.1f}°C to {temp_range[1]:.1f}°C")
            
            return {
                "grid_points": grid_points,
                "total_points": total_points,
                "ph_values": [round(v, 2) for v in ph_values],
                "coc_values": [round(v, 2) for v in coc_values],
                "temp_values": [round(v, 1) for v in temp_values]
            }
            
        except Exception as e:
            logger.error(f"❌ 3D grid generation failed: {e}")
            raise
    
    # ========================================
    # 2D GRID (Fixed 3rd Variable)
    # ========================================
    
    @staticmethod
    def generate_2d_grid(
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        x_steps: int = 20,
        y_steps: int = 20,
        fixed_z_value: float = None
    ) -> Dict[str, Any]:
        """
        Generate 2D grid with fixed 3rd variable
        
        Used when user wants to see pH vs CoC at fixed temperature, etc.
        
        Args:
            x_range: (min_x, max_x)
            y_range: (min_y, max_y)
            x_steps: Number of X points
            y_steps: Number of Y points
            fixed_z_value: Fixed value for 3rd axis
        
        Returns:
            {
                "grid_points": List of (x, y, z) tuples,
                "total_points": int,
                "x_values": List[float],
                "y_values": List[float]
            }
        """
        try:
            x_values = np.linspace(x_range[0], x_range[1], x_steps).tolist()
            y_values = np.linspace(y_range[0], y_range[1], y_steps).tolist()
            
            # Generate 2D grid with fixed Z
            if fixed_z_value is None:
                # If no fixed Z, just return 2D points
                grid_points = list(product(x_values, y_values))
            else:
                # Add fixed Z to each point
                grid_points = [(x, y, fixed_z_value) for x, y in product(x_values, y_values)]
            
            total_points = len(grid_points)
            
            logger.info(f"✅ Generated 2D grid: {x_steps}×{y_steps} = {total_points} points")
            
            return {
                "grid_points": grid_points,
                "total_points": total_points,
                "x_values": [round(v, 2) for v in x_values],
                "y_values": [round(v, 2) for v in y_values],
                "fixed_z_value": fixed_z_value
            }
            
        except Exception as e:
            logger.error(f"❌ 2D grid generation failed: {e}")
            raise
    
    # ========================================
    # CONCENTRATE WATER AT COC
    # ========================================
    
    @staticmethod
    def concentrate_water(
        base_water_analysis: Dict[str, Any],
        coc: float
    ) -> Dict[str, Any]:
        """
        Multiply all ion concentrations by CoC
        
        Args:
            base_water_analysis: Dictionary of parameters
            coc: Cycles of concentration
        
        Returns:
            Concentrated water analysis
        """
        try:
            concentrated = {}
            
            # Parameters that should NOT be concentrated
            non_concentrated_params = ["pH", "Temperature", "pe", "Eh"]
            
            for param_name, param_data in base_water_analysis.items():
                if isinstance(param_data, dict):
                    value = param_data.get("value")
                    unit = param_data.get("unit")
                    
                    # Check if this parameter should be concentrated
                    if param_name in non_concentrated_params:
                        # Keep as-is
                        concentrated[param_name] = {
                            "value": value,
                            "unit": unit
                        }
                    elif isinstance(value, (int, float)):
                        # Concentrate the value
                        concentrated_value = value * coc
                        concentrated[param_name] = {
                            "value": round(concentrated_value, 4),
                            "unit": unit
                        }
                    else:
                        # Non-numeric, keep as-is
                        concentrated[param_name] = param_data
                else:
                    concentrated[param_name] = param_data
            
            return concentrated
            
        except Exception as e:
            logger.error(f"❌ Water concentration failed: {e}")
            raise
    
    # ========================================
    # BATCH PREPARATION FOR PHREEQC
    # ========================================
    
    @staticmethod
    def prepare_batch_inputs(
        base_water_analysis: Dict[str, Any],
        grid_points: List[Tuple[float, float, float]]
    ) -> List[Dict[str, Any]]:
        """
        Prepare batch of water analyses for all grid points
        
        Each grid point: (pH, CoC, temp)
        
        Args:
            base_water_analysis: Base makeup water analysis
            grid_points: List of (pH, CoC, temp) tuples
        
        Returns:
            List of water analyses ready for PHREEQC
        """
        try:
            batch_inputs = []
            
            for i, (ph, coc, temp) in enumerate(grid_points):
                # Concentrate water at this CoC
                concentrated = GridCalculator.concentrate_water(base_water_analysis, coc)
                
                # Override pH and Temperature
                concentrated["pH"] = {"value": ph, "unit": ""}
                concentrated["Temperature"] = {"value": temp, "unit": "°C"}
                
                # Add metadata
                concentrated["_grid_point_index"] = i
                concentrated["_grid_pH"] = ph
                concentrated["_grid_CoC"] = coc
                concentrated["_grid_temp"] = temp
                
                batch_inputs.append(concentrated)
            
            logger.info(f"✅ Prepared {len(batch_inputs)} batch inputs for PHREEQC")
            
            return batch_inputs
            
        except Exception as e:
            logger.error(f"❌ Batch preparation failed: {e}")
            raise
    
    # ========================================
    # ADAPTIVE GRID REFINEMENT
    # ========================================
    
    @staticmethod
    def refine_grid_around_point(
        center_point: Tuple[float, float, float],
        refinement_radius: Tuple[float, float, float],
        refinement_steps: int = 5
    ) -> List[Tuple[float, float, float]]:
        """
        Generate refined grid around a point of interest
        
        Useful for zooming in on critical regions (e.g., near SI = 0)
        
        Args:
            center_point: (pH, CoC, temp) center of refinement
            refinement_radius: (±pH, ±CoC, ±temp) radius
            refinement_steps: Steps in each direction
        
        Returns:
            List of refined grid points
        """
        try:
            center_ph, center_coc, center_temp = center_point
            radius_ph, radius_coc, radius_temp = refinement_radius
            
            # Generate refined ranges
            ph_range = (center_ph - radius_ph, center_ph + radius_ph)
            coc_range = (center_coc - radius_coc, center_coc + radius_coc)
            temp_range = (center_temp - radius_temp, center_temp + radius_temp)
            
            # Generate refined grid
            refined = GridCalculator.generate_3d_grid(
                ph_range, coc_range, temp_range,
                ph_steps=refinement_steps,
                coc_steps=refinement_steps,
                temp_steps=refinement_steps
            )
            
            logger.info(f"✅ Refined grid around ({center_ph}, {center_coc}, {center_temp}): {refined['total_points']} points")
            
            return refined["grid_points"]
            
        except Exception as e:
            logger.error(f"❌ Grid refinement failed: {e}")
            raise
    
    # ========================================
    # GRID SUBSET EXTRACTION
    # ========================================
    
    @staticmethod
    def extract_slice(
        grid_results: List[Dict[str, Any]],
        axis: str,  # "pH", "CoC", or "temp"
        fixed_value: float,
        tolerance: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Extract a 2D slice from 3D grid results
        
        Example: Get all results where pH = 7.5 (±0.1)
        
        Args:
            grid_results: Full grid results with metadata
            axis: Which axis to fix ("pH", "CoC", "temp")
            fixed_value: Value to fix axis at
            tolerance: Acceptable deviation from fixed value
        
        Returns:
            Filtered subset of results
        """
        try:
            axis_key = f"_grid_{axis}"
            
            filtered = [
                result for result in grid_results
                if abs(result.get(axis_key, 0) - fixed_value) <= tolerance
            ]
            
            logger.info(f"✅ Extracted slice: {axis}={fixed_value} (±{tolerance}) → {len(filtered)} points")
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ Slice extraction failed: {e}")
            raise