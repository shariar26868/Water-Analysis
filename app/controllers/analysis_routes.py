"""
Analysis Routes - New Analysis Types
Simple Saturation, Where Can I Treat, Compare Analyses
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from app.services.analysis_engine import AnalysisEngine
from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# SIMPLE SATURATION MODEL
# ========================================

@router.post("/analysis/simple-saturation")
async def run_simple_saturation_analysis(
    data: Dict[str, Any] = Body(...)
):
    """
    Simple Saturation Model - 3D Grid Analysis
    
    Request Body:
    {
        "base_water_analysis": {...},
        "ph_range": [6.5, 8.5],
        "coc_range": [2.0, 6.0],
        "temp_range": [20, 40],
        "salts_of_interest": ["Calcite", "Gypsum", "SiO2(a)"],
        "ph_steps": 10,
        "coc_steps": 10,
        "temp_steps": 10,
        "balance_cation": "Na",
        "balance_anion": "Cl"
    }
    
    Returns:
        Analysis ID and summary
    """
    try:
        logger.info("🔬 Simple Saturation Model API called")
        
        # Extract parameters
        base_water = data.get("base_water_analysis")
        ph_range = tuple(data.get("ph_range", [6.5, 8.5]))
        coc_range = tuple(data.get("coc_range", [2.0, 6.0]))
        temp_range = tuple(data.get("temp_range", [20, 40]))
        salts = data.get("salts_of_interest")
        ph_steps = data.get("ph_steps", 10)
        coc_steps = data.get("coc_steps", 10)
        temp_steps = data.get("temp_steps", 10)
        balance_cation = data.get("balance_cation", "Na")
        balance_anion = data.get("balance_anion", "Cl")
        
        # Validate
        if not base_water:
            raise HTTPException(status_code=400, detail="base_water_analysis is required")
        
        # Run analysis
        engine = AnalysisEngine()
        
        result = await engine.run_simple_saturation(
            base_water_analysis=base_water,
            ph_range=ph_range,
            coc_range=coc_range,
            temp_range=temp_range,
            salts_of_interest=salts,
            ph_steps=ph_steps,
            coc_steps=coc_steps,
            temp_steps=temp_steps,
            balance_cation=balance_cation,
            balance_anion=balance_anion
        )
        
        logger.info(f"✅ Analysis complete: {result['analysis_id']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Simple Saturation API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# WHERE CAN I TREAT - FIXED DOSAGE
# ========================================

@router.post("/analysis/where-can-i-treat-fixed")
async def run_where_can_i_treat_fixed(
    data: Dict[str, Any] = Body(...)
):
    """
    Where Can I Treat - Fixed Product Dosages
    
    Request Body:
    {
        "base_water_analysis": {...},
        "products": [
            {"product_id": "prod-123", "dosage_ppm": 50},
            {"product_id": "prod-456", "dosage_ppm": 25}
        ],
        "ph_range": [7.0, 8.5],
        "coc_range": [2.0, 5.0],
        "temp_range": [25, 35],
        "target_salts": ["Calcite", "Gypsum"],
        "ph_steps": 10,
        "coc_steps": 10,
        "temp_steps": 5
    }
    
    Returns:
        Analysis results with green/yellow/red zones
    """
    try:
        logger.info("🎯 Where Can I Treat (Fixed) API called")
        
        # Extract parameters
        base_water = data.get("base_water_analysis")
        products = data.get("products", [])
        ph_range = tuple(data.get("ph_range", [7.0, 8.5]))
        coc_range = tuple(data.get("coc_range", [2.0, 5.0]))
        temp_range = tuple(data.get("temp_range", [25, 35]))
        target_salts = data.get("target_salts", ["Calcite"])
        ph_steps = data.get("ph_steps", 10)
        coc_steps = data.get("coc_steps", 10)
        temp_steps = data.get("temp_steps", 5)
        
        # Validate
        if not base_water:
            raise HTTPException(status_code=400, detail="base_water_analysis is required")
        if not products:
            raise HTTPException(status_code=400, detail="products list is required")
        
        # Run analysis
        engine = AnalysisEngine()
        
        result = await engine.run_where_can_i_treat_fixed(
            base_water_analysis=base_water,
            products=products,
            ph_range=ph_range,
            coc_range=coc_range,
            temp_range=temp_range,
            target_salts=target_salts,
            ph_steps=ph_steps,
            coc_steps=coc_steps,
            temp_steps=temp_steps
        )
        
        logger.info(f"✅ Analysis complete: {result['analysis_id']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Where Can I Treat (Fixed) API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# WHERE CAN I TREAT - AUTO DOSAGE
# ========================================

@router.post("/analysis/where-can-i-treat-auto")
async def run_where_can_i_treat_auto(
    data: Dict[str, Any] = Body(...)
):
    """
    Where Can I Treat - Auto-Select Dosages
    
    AI determines optimal dosages to treat every CoC
    
    Request Body:
    {
        "base_water_analysis": {...},
        "products": [
            {"product_id": "prod-123"},
            {"product_id": "prod-456"}
        ],
        "ph_range": [7.0, 8.5],
        "coc_range": [2.0, 5.0],
        "temp_range": [25, 35],
        "target_salts": ["Calcite", "Gypsum"],
        "ph_steps": 10,
        "coc_steps": 10,
        "temp_steps": 5
    }
    
    Returns:
        Analysis with auto-calculated dosages
    """
    try:
        logger.info("🤖 Where Can I Treat (Auto) API called")
        
        # TODO: Implement auto-dosage selection logic
        # This is complex - requires iterative optimization
        
        raise HTTPException(
            status_code=501,
            detail="Auto-dosage selection not yet implemented. Use /where-can-i-treat-fixed for now."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Where Can I Treat (Auto) API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# COMPARE 2 ANALYSES
# ========================================

@router.post("/analysis/compare")
async def compare_analyses(
    data: Dict[str, Any] = Body(...)
):
    """
    Compare 2 Analyses Side-by-Side
    
    Request Body:
    {
        "analysis1_id": "SSM-20260131-123456",
        "analysis2_id": "WCIT-Fixed-20260131-234567"
    }
    
    Returns:
        Comparison report
    """
    try:
        logger.info("🔀 Compare Analyses API called")
        
        analysis1_id = data.get("analysis1_id")
        analysis2_id = data.get("analysis2_id")
        
        if not analysis1_id or not analysis2_id:
            raise HTTPException(
                status_code=400,
                detail="Both analysis1_id and analysis2_id are required"
            )
        
        # Run comparison
        engine = AnalysisEngine()
        
        result = await engine.compare_analyses(analysis1_id, analysis2_id)
        
        logger.info("✅ Comparison complete")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Comparison API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# GET ANALYSIS RESULTS
# ========================================

@router.get("/analysis/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get complete analysis results by ID
    
    Args:
        analysis_id: Analysis ID (e.g., "SSM-20260131-123456")
    
    Returns:
        Full analysis document
    """
    try:
        logger.info(f"📊 Fetching analysis: {analysis_id}")
        
        analysis = await db.db.analysis_results.find_one({"analysis_id": analysis_id})
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        
        # Remove MongoDB _id
        if "_id" in analysis:
            del analysis["_id"]
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# GET 3D GRAPH DATA
# ========================================

@router.get("/analysis/{analysis_id}/3d-graph")
async def get_3d_graph_data(
    analysis_id: str,
    salt_name: str = Query(..., description="Mineral name (e.g., 'Calcite')"),
    x_axis: str = Query("pH", description="X-axis parameter"),
    y_axis: str = Query("CoC", description="Y-axis parameter"),
    fixed_z_value: Optional[float] = Query(None, description="Fixed value for Z-axis")
):
    """
    Get 3D graph data for visualization
    
    Args:
        analysis_id: Analysis ID
        salt_name: Which mineral to graph
        x_axis: X-axis parameter ("pH", "CoC", "temp")
        y_axis: Y-axis parameter ("pH", "CoC", "temp")
        fixed_z_value: Fixed value for 3rd axis (optional)
    
    Returns:
        Graph data ready for frontend plotting
    """
    try:
        logger.info(f"📈 3D graph data request: {analysis_id}, salt={salt_name}")
        
        # Get analysis
        analysis = await db.db.analysis_results.find_one({"analysis_id": analysis_id})
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        
        results = analysis.get("results", [])
        
        # Extract SI values for the requested salt
        graph_data = {
            "x_values": [],
            "y_values": [],
            "z_values": [],
            "si_values": []
        }
        
        axis_map = {
            "pH": "pH",
            "CoC": "CoC",
            "temp": "temperature_C"
        }
        
        x_key = axis_map.get(x_axis)
        y_key = axis_map.get(y_axis)
        
        if not x_key or not y_key:
            raise HTTPException(status_code=400, detail="Invalid axis parameter")
        
        for result in results:
            # Find SI for this salt
            si_list = result.get("saturation_indices", [])
            si_value = None
            
            for si in si_list:
                if si["mineral_name"] == salt_name:
                    si_value = si["si_value"]
                    break
            
            if si_value is not None:
                graph_data["x_values"].append(result[x_key])
                graph_data["y_values"].append(result[y_key])
                graph_data["si_values"].append(si_value)
                
                # Add Z value (or fixed value)
                if fixed_z_value is not None:
                    graph_data["z_values"].append(fixed_z_value)
                else:
                    # Get the 3rd axis value
                    z_axis = [a for a in ["pH", "CoC", "temp"] if a != x_axis and a != y_axis][0]
                    z_key = axis_map[z_axis]
                    graph_data["z_values"].append(result[z_key])
        
        graph_data["salt_name"] = salt_name
        graph_data["x_axis"] = x_axis
        graph_data["y_axis"] = y_axis
        
        logger.info(f"✅ Graph data prepared: {len(graph_data['si_values'])} points")
        
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 3D graph data failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))