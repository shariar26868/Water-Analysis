
"""
Water Analysis Routes - Enhanced
EXISTING endpoints kept intact.
NEW endpoints added:
  POST /calculations/standalone
  POST /calculations/cooling-tower
  GET  /analysis/{id}/3d-graph
  GET  /analysis/history
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from app.services.ocr_service          import OCRService
from app.services.phreeqc_service      import PHREEQCService
from app.services.graph_service        import GraphService
from app.services.standalone_calculations import StandaloneCalculations
from app.services.cooling_tower_service    import CoolingTowerService
from app.services.chemical_dosage_service  import ChemicalDosageService
from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# EXISTING ENDPOINTS (keep as-is)
# ========================================

@router.post("/extract")
async def extract_parameters(file: UploadFile = File(...)):
    """
    Extract water quality parameters from uploaded PDF/image
    Uses GPT-4o Vision OCR
    """
    try:
        logger.info("📤 File upload received")

        # ✅ FIXED: Read file content and call correct method
        file_content = await file.read()
        ocr = OCRService()
        result = await ocr.extract_from_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )

        return {
            "status":       "success",
            "parameters":   result.get("parameters", {}),
            "metadata":     result.get("metadata", {}),
            "validation":   result.get("validation", {}),
            "extracted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Extract failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_water(data: Dict[str, Any]):
    """
    Full water quality analysis (single point)
    Input:  extracted parameters
    Output: SI, ionic strength, charge balance, graphs
    
    ✅ Auto-adds Temperature if missing
    ✅ Auto-fixes Chloride = 0 issue
    ✅ Auto-sets balance_cation and balance_anion
    """
    try:
        logger.info("🔬 Single-point analysis started")
        
        # ✅ STEP 1: Get parameters
        original_params = data.get("parameters", {})
        
        # ✅ STEP 2: Auto-add Temperature if missing
        if "Temperature" not in original_params:
            logger.info("⚠️  Temperature missing, adding default 25°C")
            original_params["Temperature"] = {"value": 25, "unit": "°C"}
        
        # ✅ STEP 3: Auto-fix Chloride = 0 issue
        chloride_value = _get_param_value(original_params, "Chloride")
        if chloride_value is not None and chloride_value == 0:
            logger.info("⚠️  Chloride = 0, changing to 1 mg/L")
            original_params["Chloride"] = {"value": 1, "unit": "mg/L"}
        
        # ✅ STEP 4: Map parameter names (Calcium → Ca, etc.)
        mapped_params = map_water_parameters(original_params)
        
        logger.info(f"📊 Mapped {len(original_params)} → {len(mapped_params)} PHREEQC params")
        
        # ✅ STEP 5: Auto-determine balance ions
        # Use Na/Cl if available, otherwise use K/SO4
        balance_cation = "Na" if "Na" in mapped_params else "K"
        balance_anion  = "Cl" if "Cl" in mapped_params else "SO4"
        
        logger.info(f"⚖️  Ion balance: {balance_cation} (cation), {balance_anion} (anion)")
        
        # ✅ STEP 6: Run PHREEQC analysis
        phreeqc = PHREEQCService()
        result  = await phreeqc.analyze(
            mapped_params,
            balance_cation=balance_cation,
            balance_anion=balance_anion
        )

        # ✅ STEP 7: Generate graphs (only if SI data exists)
        graph_svc = GraphService()
        graphs = {}
        
        si_data = result.get("saturation_indices", [])
        if si_data and len(si_data) > 0:
            try:
                graphs = graph_svc.generate_si_bar_chart(si_data)
                logger.info(f"✅ Graph generated with {len(si_data)} minerals")
            except Exception as e:
                logger.warning(f"⚠️ Graph generation failed: {e}")
                graphs = {
                    "image_base64": None,
                    "minerals": [],
                    "values": [],
                    "error": str(e)
                }
        else:
            logger.warning("⚠️ No saturation indices data - skipping graph generation")
            graphs = {
                "image_base64": None,
                "minerals": [],
                "values": [],
                "note": "No mineral saturation data available for this water sample"
            }

        # ✅ STEP 8: Save to DB
# ✅ STEP 8: Save to DB
        analysis_doc = {
            "analysis_id":  f"STD-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "analysis_type":"standard",
            "input":        data,
            "mapped_input": mapped_params,
            "result":       result,
            "results":      [result],      # ✅ এই লাইন যোগ করুন (3D graph এর জন্য)
            "graphs":       graphs,
            "created_at":   datetime.utcnow()
}
        await db.save_analysis(analysis_doc)

        return {
            "status":      "success",
            "analysis_id": analysis_doc["analysis_id"],
            "result":      result,
            "graphs":      graphs
        }
        
    except Exception as e:
        logger.error(f"❌ Analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/calculations/standalone")
async def run_standalone_calculations(data: Dict[str, Any]):
    """
    Run standalone calculations (no PHREEQC needed)
    Supports: LSI, Ryznar, Puckorius, Stiff & Davis,
              Larson-Skold, Corrosion Rates
    
    NOW SUPPORTS DYNAMIC INPUT FROM /extract ENDPOINT!
    
    Request Body - Two formats supported:
    
    Format 1: Direct parameters (legacy)
    {
        "ph": 7.5,
        "temperature_c": 30,
        "calcium_mg_l": 120,
        ...
    }
    
    Format 2: Extract response format (NEW - recommended)
    {
        "parameters": {
            "pH": {"value": 7.45, "unit": null},
            "Temperature": {"value": 28.5, "unit": "°C"},
            "Calcium": {"value": 68, "unit": "mg/L"},
            ...
        }
    }
    """
    try:
        logger.info("🧮 Standalone calculations requested")
        
        # ============================================
        # DETECT INPUT FORMAT & NORMALIZE DATA
        # ============================================
        
        # Check if this is extract response format
        if "parameters" in data and isinstance(data["parameters"], dict):
            logger.info("📥 Detected /extract response format - auto-mapping parameters")
            normalized_data = _map_extract_to_calculations(data)
        else:
            logger.info("📥 Using direct parameter format")
            normalized_data = data
        
        # ============================================
        # EXTRACT PARAMETERS WITH SAFE DEFAULTS
        # ============================================
        
        # Required parameters
        ph = normalized_data.get("ph")
        temp_c = normalized_data.get("temperature_c")
        
        # Validate required fields
        if ph is None or temp_c is None:
            raise HTTPException(
                status_code=400, 
                detail="pH and temperature_c are required. Ensure your extract response contains 'pH' and 'Temperature' parameters."
            )
        
        # Optional parameters with safe defaults
        calcium = normalized_data.get("calcium_mg_l", 0)
        alkalinity = normalized_data.get("alkalinity_mg_l", 0)
        tds = normalized_data.get("tds_mg_l", 0)
        chloride = normalized_data.get("chloride_mg_l", 0)
        sulfate = normalized_data.get("sulfate_mg_l", 0)
        bicarbonate = normalized_data.get("bicarbonate_mg_l", 0)
        carbonate = normalized_data.get("carbonate_mg_l", 0)
        do_ppm = normalized_data.get("dissolved_oxygen_ppm", 5.0)
        
        # Determine which calculations to run
        calculations = normalized_data.get("calculations")
        
        if not calculations:
            # Auto-detect based on available data
            calculations = _auto_detect_calculations(normalized_data)
            logger.info(f"🔍 Auto-detected calculations: {calculations}")
        
        # ============================================
        # RUN CALCULATIONS
        # ============================================
        
        results = {}
        skipped = []
        
        # --- LSI ---
        if "lsi" in calculations:
            if all([calcium > 0, alkalinity > 0, tds > 0]):
                try:
                    results["lsi"] = StandaloneCalculations.calculate_lsi(
                        ph=ph, temperature_c=temp_c,
                        calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                        tds_mg_l=tds
                    )
                except Exception as e:
                    logger.warning(f"⚠️ LSI calculation failed: {e}")
                    skipped.append({"calculation": "lsi", "reason": str(e)})
            else:
                skipped.append({"calculation": "lsi", "reason": "Missing required parameters (calcium, alkalinity, or tds)"})
        
        # --- Ryznar ---
        if "ryznar" in calculations:
            if all([calcium > 0, alkalinity > 0, tds > 0]):
                try:
                    results["ryznar"] = StandaloneCalculations.calculate_ryznar(
                        ph=ph, temperature_c=temp_c,
                        calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                        tds_mg_l=tds
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Ryznar calculation failed: {e}")
                    skipped.append({"calculation": "ryznar", "reason": str(e)})
            else:
                skipped.append({"calculation": "ryznar", "reason": "Missing required parameters"})
        
        # --- Puckorius ---
        if "puckorius" in calculations:
            if all([calcium > 0, alkalinity > 0, tds > 0]):
                try:
                    results["puckorius"] = StandaloneCalculations.calculate_puckorius(
                        temperature_c=temp_c,
                        calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                        tds_mg_l=tds
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Puckorius calculation failed: {e}")
                    skipped.append({"calculation": "puckorius", "reason": str(e)})
            else:
                skipped.append({"calculation": "puckorius", "reason": "Missing required parameters"})
        
        # --- Stiff & Davis ---
        if "stiff_davis" in calculations:
            if all([calcium > 0, alkalinity > 0, tds > 0]):
                try:
                    results["stiff_davis"] = StandaloneCalculations.calculate_stiff_davis(
                        ph=ph, calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                        temperature_c=temp_c, tds_mg_l=tds
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Stiff & Davis calculation failed: {e}")
                    skipped.append({"calculation": "stiff_davis", "reason": str(e)})
            else:
                skipped.append({"calculation": "stiff_davis", "reason": "Missing required parameters"})
        
        # --- Larson-Skold ---
        if "larson_skold" in calculations:
            # Need at least bicarbonate OR carbonate
            if bicarbonate > 0 or carbonate > 0:
                try:
                    results["larson_skold"] = StandaloneCalculations.calculate_larson_skold(
                        chloride_mg_l=chloride, 
                        sulfate_mg_l=sulfate,
                        bicarbonate_mg_l=bicarbonate, 
                        carbonate_mg_l=carbonate
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Larson-Skold calculation failed: {e}")
                    skipped.append({"calculation": "larson_skold", "reason": str(e)})
            else:
                skipped.append({"calculation": "larson_skold", "reason": "Missing bicarbonate and carbonate"})
        
        # --- Mild Steel Corrosion ---
        if "mild_steel" in calculations:
            try:
                results["mild_steel_corrosion"] = StandaloneCalculations.estimate_mild_steel_corrosion(
                    ph=ph,
                    dissolved_oxygen_ppm=do_ppm,
                    temperature_c=temp_c,
                    si_caco3=normalized_data.get("si_caco3", 0.0),
                    pma_ppm=normalized_data.get("pma_ppm", 0.0),
                    si_alsi=normalized_data.get("si_alsi", -999),
                    si_snsi=normalized_data.get("si_snsi", -999),
                    si_tcp=normalized_data.get("si_tcp", -999),
                    si_zp=normalized_data.get("si_zp", -999)
                )
            except Exception as e:
                logger.warning(f"⚠️ Mild steel corrosion calculation failed: {e}")
                skipped.append({"calculation": "mild_steel", "reason": str(e)})
        
        # --- Copper Corrosion ---
        if "copper" in calculations:
            try:
                results["copper_corrosion"] = StandaloneCalculations.estimate_copper_corrosion(
                    ph=ph,
                    dissolved_oxygen_ppm=do_ppm,
                    temperature_c=temp_c,
                    si_caco3=normalized_data.get("si_caco3", 0.0),
                    chloride_ppm=normalized_data.get("chloride_ppm", chloride),
                    free_chlorine_ppm=normalized_data.get("free_chlorine_ppm", 0.0),
                    total_chlorine_ppm=normalized_data.get("total_chlorine_ppm", 0.0),
                    tta_ppm=normalized_data.get("tta_ppm", 0.0),
                    bta_ppm=normalized_data.get("bta_ppm", 0.0),
                    mbt_ppm=normalized_data.get("mbt_ppm", 0.0),
                    copper_free_ppm=normalized_data.get("copper_free_ppm", 0.0)
                )
            except Exception as e:
                logger.warning(f"⚠️ Copper corrosion calculation failed: {e}")
                skipped.append({"calculation": "copper", "reason": str(e)})
        
        # --- Admiralty Brass Corrosion ---
        if "admiralty_brass" in calculations:
            try:
                results["admiralty_brass_corrosion"] = StandaloneCalculations.estimate_admiralty_brass_corrosion(
                    ph=ph,
                    dissolved_oxygen_ppm=do_ppm,
                    temperature_c=temp_c,
                    si_caco3=normalized_data.get("si_caco3", 0.0),
                    chloride_ppm=normalized_data.get("chloride_ppm", chloride),
                    ammonia_ppm=normalized_data.get("ammonia_ppm", 0.0),
                    free_chlorine_ppm=normalized_data.get("free_chlorine_ppm", 0.0),
                    total_chlorine_ppm=normalized_data.get("total_chlorine_ppm", 0.0),
                    tta_ppm=normalized_data.get("tta_ppm", 0.0),
                    bta_ppm=normalized_data.get("bta_ppm", 0.0),
                    mbt_ppm=normalized_data.get("mbt_ppm", 0.0),
                    copper_free_ppm=normalized_data.get("copper_free_ppm", 0.0)
                )
            except Exception as e:
                logger.warning(f"⚠️ Admiralty brass corrosion calculation failed: {e}")
                skipped.append({"calculation": "admiralty_brass", "reason": str(e)})
        
        logger.info(f"✅ Completed {len(results)} calculations, skipped {len(skipped)}")
        
        response = {
            "status": "success",
            "calculations": results,
            "computed_at": datetime.utcnow().isoformat()
        }
        
        if skipped:
            response["skipped_calculations"] = skipped
            response["warning"] = f"{len(skipped)} calculation(s) skipped due to missing parameters"
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Standalone calculations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HELPER FUNCTIONS
# ============================================

def _map_extract_to_calculations(extract_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map /extract response format to /calculations/standalone request format
    
    Args:
        extract_response: Response from /extract endpoint with "parameters" key
        
    Returns:
        Normalized data dict for calculations
    """
    params = extract_response.get("parameters", {})
    
    def get_value(param_name, default=0):
        """Safely extract parameter value"""
        param = params.get(param_name, {})
        if isinstance(param, dict):
            value = param.get("value", default)
        else:
            value = param
        return value if value is not None else default
    
    normalized = {}
    
    # Required parameters
    normalized["ph"] = get_value("pH", None)
    normalized["temperature_c"] = get_value("Temperature", None)
    
    # Optional - Major ions
    if "Calcium" in params:
        normalized["calcium_mg_l"] = get_value("Calcium")
    
    if "Total_Alkalinity" in params:
        normalized["alkalinity_mg_l"] = get_value("Total_Alkalinity")
    
    if "TDS" in params or "Total_Dissolved_Solids" in params:
        normalized["tds_mg_l"] = get_value("TDS") or get_value("Total_Dissolved_Solids")
    
    if "Chloride" in params:
        normalized["chloride_mg_l"] = get_value("Chloride")
        normalized["chloride_ppm"] = get_value("Chloride")  # Same value
    
    if "Sulphate" in params or "Sulfate" in params:
        normalized["sulfate_mg_l"] = get_value("Sulphate") or get_value("Sulfate")
    
    if "Bicarbonate" in params:
        normalized["bicarbonate_mg_l"] = get_value("Bicarbonate")
    
    if "Carbonate" in params:
        normalized["carbonate_mg_l"] = get_value("Carbonate")
    
    if "Dissolved_Oxygen" in params:
        normalized["dissolved_oxygen_ppm"] = get_value("Dissolved_Oxygen")
    
    # Corrosion-specific parameters
    if "Saturation_Index" in params:
        normalized["si_caco3"] = get_value("Saturation_Index")
    
    if "Polymaleic_Acid" in params:
        normalized["pma_ppm"] = get_value("Polymaleic_Acid")
    
    if "Free_Chlorine" in params:
        normalized["free_chlorine_ppm"] = get_value("Free_Chlorine")
    
    if "Total_Chlorine" in params:
        normalized["total_chlorine_ppm"] = get_value("Total_Chlorine")
    
    if "Tolyltriazole" in params or "TTA" in params:
        normalized["tta_ppm"] = get_value("Tolyltriazole") or get_value("TTA")
    
    if "Benzotriazole" in params or "BTA" in params:
        normalized["bta_ppm"] = get_value("Benzotriazole") or get_value("BTA")
    
    if "Mercaptobenzothiazole" in params or "MBT" in params:
        normalized["mbt_ppm"] = get_value("Mercaptobenzothiazole") or get_value("MBT")
    
    if "Copper_Free" in params:
        normalized["copper_free_ppm"] = get_value("Copper_Free")
    
    if "Ammonia" in params:
        normalized["ammonia_ppm"] = get_value("Ammonia")
    
    return normalized


def _auto_detect_calculations(data: Dict[str, Any]) -> list:
    """
    Auto-detect which calculations can be run based on available parameters
    
    Args:
        data: Normalized parameter dict
        
    Returns:
        List of calculation names that can be performed
    """
    calculations = []
    
    # Check for LSI/Ryznar/Puckorius/Stiff & Davis requirements
    has_scaling_params = all([
        data.get("calcium_mg_l", 0) > 0,
        data.get("alkalinity_mg_l", 0) > 0,
        data.get("tds_mg_l", 0) > 0
    ])
    
    if has_scaling_params:
        calculations.extend(["lsi", "ryznar", "puckorius", "stiff_davis"])
    
    # Check for Larson-Skold
    has_larson_skold_params = (
        data.get("bicarbonate_mg_l", 0) > 0 or 
        data.get("carbonate_mg_l", 0) > 0
    )
    
    if has_larson_skold_params:
        calculations.append("larson_skold")
    
    # Corrosion calculations (need pH, temp, DO)
    has_corrosion_basics = all([
        data.get("ph") is not None,
        data.get("temperature_c") is not None,
        data.get("dissolved_oxygen_ppm", 0) > 0
    ])
    
    if has_corrosion_basics:
        calculations.append("mild_steel")
        
        # Copper if chlorine or azoles present
        if any([
            data.get("free_chlorine_ppm", 0) > 0,
            data.get("total_chlorine_ppm", 0) > 0,
            data.get("tta_ppm", 0) > 0,
            data.get("bta_ppm", 0) > 0,
            data.get("mbt_ppm", 0) > 0
        ]):
            calculations.append("copper")
        
        # Admiralty brass if ammonia present
        if data.get("ammonia_ppm", 0) > 0:
            calculations.append("admiralty_brass")
    
    # If nothing detected, try at least basic calculations
    if not calculations:
        calculations = ["lsi"]
    
    return calculations



# ========================================
# NEW ENDPOINT: COOLING TOWER CALCULATIONS
# ========================================
@router.post("/calculations/cooling-tower")
async def run_cooling_tower_calculations(data: Dict[str, Any]):
    """
    Run cooling tower calculations
    
    SUPPORTS FLEXIBLE INPUT - only required: recirculation_rate_gpm
    All other parameters are optional and calculations adapt accordingly
    
    Request Body Options:
    
    Minimal (only flow rate):
    {
        "recirculation_rate_gpm": 5000
    }
    
    With temperatures:
    {
        "recirculation_rate_gpm": 5000,
        "hot_water_temp_f": 105,
        "cold_water_temp_f": 85,
        "wet_bulb_temp_f": 78
    }
    
    With water chemistry (for CoC):
    {
        "recirculation_rate_gpm": 5000,
        "hot_water_temp_f": 105,
        "cold_water_temp_f": 85,
        "makeup_silica_mg_l": 40,
        "recirculating_silica_mg_l": 160
    }
    
    OR with extract response format:
    {
        "system_parameters": {
            "recirculation_rate_gpm": 5000,
            "hot_water_temp_f": 105,
            "cold_water_temp_f": 85
        },
        "makeup_water": {
            "parameters": {
                "Silica": {"value": 40, "unit": "mg/L"}
            }
        },
        "circulating_water": {
            "parameters": {
                "Silica": {"value": 160, "unit": "mg/L"}
            }
        }
    }
    
    Optional parameters:
    - drift_percent (default: 0.1)
    - evaporation_factor_percent (default: 85)
    - cooling_tons (auto-calculated if not provided)
    """
    try:
        logger.info("🌊 Cooling tower calculations requested")
        
        # ============================================
        # NORMALIZE INPUT DATA
        # ============================================
        
        normalized = _normalize_cooling_tower_input(data)
        
        # ============================================
        # EXTRACT PARAMETERS
        # ============================================
        
        # Required
        recirc_gpm = normalized.get("recirculation_rate_gpm")
        
        if recirc_gpm is None or recirc_gpm <= 0:
            raise HTTPException(
                status_code=400,
                detail="recirculation_rate_gpm is required and must be > 0"
            )
        
        # Optional - Temperatures
        hot_temp_f = normalized.get("hot_water_temp_f")
        cold_temp_f = normalized.get("cold_water_temp_f")
        wet_bulb_f = normalized.get("wet_bulb_temp_f")
        
        # Optional - Water chemistry
        makeup_silica = normalized.get("makeup_silica_mg_l")
        recirc_silica = normalized.get("recirculating_silica_mg_l")
        
        # Optional - System parameters
        drift_pct = normalized.get("drift_percent", 0.1)
        evap_factor = normalized.get("evaporation_factor_percent", 85.0)
        cooling_tons = normalized.get("cooling_tons")
        
        # ============================================
        # RUN CALCULATIONS
        # ============================================
        
        results = {}
        warnings = []
        calculations_performed = []
        
        # --- 1. Cycles of Concentration (CoC) ---
        coc = None
        if makeup_silica and recirc_silica and makeup_silica > 0:
            try:
                coc = CoolingTowerService.calculate_coc(
                    base_water_ion_mg_l=makeup_silica,
                    concentrated_water_ion_mg_l=recirc_silica
                )
                results["cycles_of_concentration"] = {
                    "coc": coc,
                    "based_on": "Silica concentration",
                    "makeup_silica_mg_l": makeup_silica,
                    "recirculating_silica_mg_l": recirc_silica
                }
                calculations_performed.append("cycles_of_concentration")
            except Exception as e:
                logger.warning(f"⚠️ CoC calculation failed: {e}")
                warnings.append(f"CoC calculation skipped: {str(e)}")
        else:
            warnings.append("CoC calculation skipped: Missing makeup or recirculating silica data")
        
        # --- 2. Tower Range ---
        range_f = None
        if hot_temp_f is not None and cold_temp_f is not None:
            try:
                range_f = CoolingTowerService.calculate_tower_range(
                    hot_water_temp_f=hot_temp_f,
                    cold_water_temp_f=cold_temp_f
                )
                results["tower_range"] = {
                    "range_f": range_f,
                    "hot_water_temp_f": hot_temp_f,
                    "cold_water_temp_f": cold_temp_f
                }
                calculations_performed.append("tower_range")
            except Exception as e:
                logger.warning(f"⚠️ Range calculation failed: {e}")
                warnings.append(f"Range calculation skipped: {str(e)}")
        else:
            warnings.append("Range calculation skipped: Missing hot or cold water temperature")
        
        # --- 3. Approach Temperature ---
        approach_f = None
        if cold_temp_f is not None and wet_bulb_f is not None:
            try:
                approach_f = CoolingTowerService.calculate_approach_temperature(
                    cold_water_temp_f=cold_temp_f,
                    wet_bulb_temp_f=wet_bulb_f
                )
                results["approach_temperature"] = {
                    "approach_f": approach_f,
                    "cold_water_temp_f": cold_temp_f,
                    "wet_bulb_temp_f": wet_bulb_f
                }
                calculations_performed.append("approach_temperature")
            except Exception as e:
                logger.warning(f"⚠️ Approach calculation failed: {e}")
                warnings.append(f"Approach calculation skipped: {str(e)}")
        else:
            warnings.append("Approach calculation skipped: Missing cold water or wet bulb temperature")
        
        # --- 4. Tower Efficiency ---
        if range_f is not None and approach_f is not None:
            try:
                efficiency_result = CoolingTowerService.calculate_tower_efficiency(
                    range_f=range_f,
                    approach_f=approach_f
                )
                results["tower_efficiency"] = efficiency_result
                calculations_performed.append("tower_efficiency")
            except Exception as e:
                logger.warning(f"⚠️ Efficiency calculation failed: {e}")
                warnings.append(f"Efficiency calculation skipped: {str(e)}")
        else:
            warnings.append("Efficiency calculation skipped: Missing range or approach")
        
        # --- 5. Evaporation Rate ---
        evap_gpm = None
        if range_f is not None:
            try:
                evap_result = CoolingTowerService.calculate_evaporation_rate(
                    recirculation_rate_gpm=recirc_gpm,
                    delta_t_f=range_f,
                    evaporation_factor_percent=evap_factor
                )
                results["evaporation_rate"] = evap_result
                evap_gpm = evap_result["evaporation_rate_gpm"]
                calculations_performed.append("evaporation_rate")
            except Exception as e:
                logger.warning(f"⚠️ Evaporation calculation failed: {e}")
                warnings.append(f"Evaporation calculation skipped: {str(e)}")
        else:
            warnings.append("Evaporation calculation skipped: Missing range")
        
        # --- 6. Blowdown Rate ---
        bd_gpm = None
        if evap_gpm is not None and coc is not None and coc > 1:
            try:
                bd_result = CoolingTowerService.calculate_blowdown_rate(
                    evaporation_rate_gpm=evap_gpm,
                    coc=coc
                )
                results["blowdown_rate"] = bd_result
                bd_gpm = bd_result["blowdown_rate_gpm"]
                calculations_performed.append("blowdown_rate")
            except Exception as e:
                logger.warning(f"⚠️ Blowdown calculation failed: {e}")
                warnings.append(f"Blowdown calculation skipped: {str(e)}")
        else:
            if evap_gpm is None:
                warnings.append("Blowdown calculation skipped: Missing evaporation rate")
            elif coc is None:
                warnings.append("Blowdown calculation skipped: Missing CoC")
            else:
                warnings.append("Blowdown calculation skipped: CoC must be > 1")
        
        # --- 7. Makeup Rate ---
        if evap_gpm is not None and bd_gpm is not None:
            try:
                makeup_result = CoolingTowerService.calculate_makeup_rate(
                    evaporation_rate_gpm=evap_gpm,
                    blowdown_rate_gpm=bd_gpm,
                    recirculation_rate_gpm=recirc_gpm,
                    drift_percent=drift_pct
                )
                results["makeup_rate"] = makeup_result
                calculations_performed.append("makeup_rate")
            except Exception as e:
                logger.warning(f"⚠️ Makeup calculation failed: {e}")
                warnings.append(f"Makeup calculation skipped: {str(e)}")
        else:
            warnings.append("Makeup calculation skipped: Missing evaporation or blowdown rate")
        
        # --- 8. Heat Load ---
        if range_f is not None:
            try:
                heat_result = CoolingTowerService.calculate_heat_load(
                    recirculation_rate_gpm=recirc_gpm,
                    range_f=range_f
                )
                results["heat_load"] = heat_result
                calculations_performed.append("heat_load")
            except Exception as e:
                logger.warning(f"⚠️ Heat load calculation failed: {e}")
                warnings.append(f"Heat load calculation skipped: {str(e)}")
        else:
            warnings.append("Heat load calculation skipped: Missing range")
        
        # --- 9. Cooling Tons ---
        if cooling_tons is None and range_f is not None:
            try:
                cooling_tons = CoolingTowerService.recirculation_to_tons(
                    recirculation_rate_gpm=recirc_gpm,
                    range_f=range_f
                )
                results["cooling_capacity"] = {
                    "cooling_tons": cooling_tons,
                    "calculation_method": "auto-calculated from flow and range"
                }
                calculations_performed.append("cooling_capacity")
            except Exception as e:
                logger.warning(f"⚠️ Cooling tons calculation failed: {e}")
                warnings.append(f"Cooling tons calculation skipped: {str(e)}")
        elif cooling_tons is not None:
            results["cooling_capacity"] = {
                "cooling_tons": cooling_tons,
                "calculation_method": "user-provided"
            }
            calculations_performed.append("cooling_capacity")
        
        # --- 10. Dissolved Oxygen ---
        if cold_temp_f is not None and wet_bulb_f is not None:
            try:
                # Convert F to C
                cold_temp_c = (cold_temp_f - 32) * 5/9
                wet_bulb_c = (wet_bulb_f - 32) * 5/9
                
                do_result = CoolingTowerService.calculate_dissolved_oxygen(
                    water_temp_c=cold_temp_c,
                    wet_bulb_temp_c=wet_bulb_c
                )
                results["dissolved_oxygen"] = do_result
                calculations_performed.append("dissolved_oxygen")
            except Exception as e:
                logger.warning(f"⚠️ DO calculation failed: {e}")
                warnings.append(f"DO calculation skipped: {str(e)}")
        else:
            warnings.append("DO calculation skipped: Missing temperatures")
        
        # ============================================
        # BUILD RESPONSE
        # ============================================
        
        logger.info(f"✅ Completed {len(calculations_performed)} cooling tower calculations")
        
        response = {
            "status": "success",
            "calculations": results,
            "calculations_performed": calculations_performed,
            "input_parameters": {
                "recirculation_rate_gpm": recirc_gpm,
                "hot_water_temp_f": hot_temp_f,
                "cold_water_temp_f": cold_temp_f,
                "wet_bulb_temp_f": wet_bulb_f,
                "makeup_silica_mg_l": makeup_silica,
                "recirculating_silica_mg_l": recirc_silica,
                "drift_percent": drift_pct,
                "evaporation_factor_percent": evap_factor
            },
            "computed_at": datetime.utcnow().isoformat()
        }
        
        if warnings:
            response["warnings"] = warnings
            response["note"] = f"{len(warnings)} calculation(s) skipped due to missing parameters"
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cooling tower calculations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HELPER FUNCTION
# ============================================

def _normalize_cooling_tower_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize cooling tower input - supports multiple formats
    
    Formats supported:
    1. Direct parameters
    2. Nested structure with system_parameters, makeup_water, circulating_water
    3. Extract response format
    """
    normalized = {}
    
    # Check if using nested structure
    if "system_parameters" in data:
        # System parameters
        sys_params = data.get("system_parameters", {})
        normalized.update(sys_params)
        
        # Extract silica from makeup water
        makeup = data.get("makeup_water", {})
        if "parameters" in makeup:
            makeup_params = makeup["parameters"]
            if "Silica" in makeup_params:
                silica_data = makeup_params["Silica"]
                if isinstance(silica_data, dict):
                    normalized["makeup_silica_mg_l"] = silica_data.get("value")
                else:
                    normalized["makeup_silica_mg_l"] = silica_data
        
        # Extract silica from circulating water
        circ = data.get("circulating_water", {})
        if "parameters" in circ:
            circ_params = circ["parameters"]
            if "Silica" in circ_params:
                silica_data = circ_params["Silica"]
                if isinstance(silica_data, dict):
                    normalized["recirculating_silica_mg_l"] = silica_data.get("value")
                else:
                    normalized["recirculating_silica_mg_l"] = silica_data
    else:
        # Direct format
        normalized = data.copy()
    
    return normalized

# ========================================
# NEW ENDPOINT: CHEMICAL DOSAGE
# ========================================

@router.post("/calculations/chemical-dosage")
async def run_chemical_dosage(data: Dict[str, Any]):
    """
    Chemical dosage & cost calculations

    Request Body:
    {
        "product_dosage_ppm": 50,
        "blowdown_rate_gpm": 20,
        "price_per_lb": 2.50,
        "active_percent": 35,
        "formulation": {"Phosphonate": 15, "Polymer": 5, "Azole": 2.5}
    }
    """
    try:
        logger.info("💊 Chemical dosage calculations requested")

        dosage_ppm   = data.get("product_dosage_ppm", 0)
        bd_gpm       = data.get("blowdown_rate_gpm", 0)
        price_per_lb = data.get("price_per_lb", 0)
        active_pct   = data.get("active_percent", 100)
        formulation  = data.get("formulation")

        results = {}

        # Usage per day
        if dosage_ppm and bd_gpm:
            results["usage"] = ChemicalDosageService.calculate_chemical_usage_per_day(
                dosage_ppm, bd_gpm
            )

        # Annual cost
        if dosage_ppm and bd_gpm and price_per_lb:
            results["annual_cost"] = ChemicalDosageService.calculate_total_annual_cost(
                dosage_ppm, price_per_lb, bd_gpm
            )

        # Cost per million lbs BD
        if dosage_ppm and price_per_lb:
            results["cost_per_mlb"] = ChemicalDosageService.calculate_cost_per_million_lbs_blowdown(
                dosage_ppm, price_per_lb
            )

        # Active component
        if dosage_ppm and active_pct:
            results["active_ppm"] = ChemicalDosageService.calculate_active_component_dosage(
                dosage_ppm, active_pct
            )

        # Multi-component formulation
        if dosage_ppm and formulation:
            results["components"] = ChemicalDosageService.calculate_multi_component_dosages(
                dosage_ppm, formulation
            )

        logger.info(f"✅ Chemical dosage done: {list(results.keys())}")

        return {
            "status":  "success",
            "results": results,
            "computed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Chemical dosage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT: GET 3D GRAPH DATA
# ========================================

# @router.get("/analysis/{analysis_id}/3d-graph")
# async def get_3d_graph(
#     analysis_id: str,
#     salt_name:   str   = Query(...,       description="Mineral (e.g. Calcite)"),
#     x_axis:      str   = Query("pH",      description="X axis: pH | CoC | temp"),
#     y_axis:      str   = Query("CoC",     description="Y axis: pH | CoC | temp"),
#     format:      str   = Query("json",    description="json | png")
# ):
#     """
#     Get 3D graph for a specific salt from stored analysis results.
#     format=json  → raw data for frontend Plotly rendering
#     format=png   → server-rendered PNG image
#     """
#     try:
#         logger.info(f"📈 3D graph: analysis={analysis_id}, salt={salt_name}, format={format}")

#         # Fetch stored analysis
#         # analysis = await db.get_analysis_result(analysis_id)
#         analysis = await db.get_analysis(analysis_id)
#         if not analysis:
#             raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

#         graph_svc = GraphService()

#         if format == "json":
#             graph_data = graph_svc.prepare_3d_graph_data(
#                 results=analysis.get("results", []),
#                 salt_name=salt_name,
#                 x_axis=x_axis,
#                 y_axis=y_axis
#             )
#             return {"status": "success", "graph_data": graph_data}

#         elif format == "png":
#             png_base64 = graph_svc.generate_3d_surface_png(
#                 results=analysis.get("results", []),
#                 salt_name=salt_name,
#                 x_axis=x_axis,
#                 y_axis=y_axis
#             )
#             return {"status": "success", "image_base64": png_base64}

#         else:
#             raise HTTPException(status_code=400, detail="format must be 'json' or 'png'")

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ 3D graph failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


from app.services.s3_service import S3Service

@router.get("/analysis/{analysis_id}/3d-graph")
async def get_3d_graph(
    analysis_id: str,
    salt_name: str = Query(..., description="Mineral (e.g. Calcite)"),
    x_axis: str = Query("pH", description="X axis: pH | CoC | temp"),
    y_axis: str = Query("CoC", description="Y axis: pH | CoC | temp"),
    format: str = Query("json", description="json | png"),
    upload_to_s3: bool = Query(False, description="Upload PNG to S3 and return URL")
):
    """
    Get 3D graph for a specific salt from stored grid analysis results.
    
    format=json → raw data for frontend Plotly.js rendering
    format=png  → server-rendered PNG image (base64 or S3 URL)
    
    Examples:
    - JSON: /analysis/GRID-20260210-123456/3d-graph?salt_name=Calcite&format=json
    - PNG:  /analysis/GRID-20260210-123456/3d-graph?salt_name=Calcite&format=png&upload_to_s3=true
    """
    try:
        logger.info(f"📈 3D graph: analysis={analysis_id}, salt={salt_name}, format={format}")

        # ✅ Fetch stored analysis from analysis_results collection
        analysis = await db.get_analysis_result(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis '{analysis_id}' not found. Please run grid analysis first."
            )
        
        # ✅ Check if it's a grid analysis
        if analysis.get("analysis_type") != "grid":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis '{analysis_id}' is not a grid analysis. Only grid analyses support 3D graphs."
            )
        
        # ✅ Get results array
        results = analysis.get("results", [])
        
        if not results or len(results) == 0:
            raise HTTPException(
                status_code=400,
                detail="No grid results found in this analysis."
            )
        
        logger.info(f"📊 Processing {len(results)} grid points")

        graph_svc = GraphService()

        if format == "json":
            # ✅ Return JSON data for frontend Plotly.js
            graph_data = graph_svc.prepare_3d_graph_data(
                results=results,
                salt_name=salt_name,
                x_axis=x_axis,
                y_axis=y_axis
            )
            
            return {
                "status": "success",
                "graph_data": graph_data,
                "analysis_id": analysis_id,
                "data_points": len(results),
                "grid_config": analysis.get("grid_config", {})
            }

        elif format == "png":
            # ✅ Generate 3D surface PNG
            png_base64 = graph_svc.generate_3d_surface_png(
                results=results,
                salt_name=salt_name,
                x_axis=x_axis,
                y_axis=y_axis
            )
            
            response = {
                "status": "success",
                "analysis_id": analysis_id,
                "salt_name": salt_name,
                "x_axis": x_axis,
                "y_axis": y_axis
            }
            
            # ✅ Upload to S3 if requested
            if upload_to_s3:
                try:
                    s3_svc = S3Service()
                    filename = f"{analysis_id}_{salt_name}_{x_axis}_{y_axis}.png"
                    
                    s3_result = s3_svc.upload_base64_image(
                        base64_data=png_base64,
                        folder="graphs/3d",
                        filename=filename
                    )
                    
                    response["s3_url"] = s3_result["url"]
                    response["s3_key"] = s3_result["key"]
                    response["s3_bucket"] = s3_result["bucket"]
                    
                    logger.info(f"✅ Graph uploaded to S3: {s3_result['url']}")
                    
                except Exception as e:
                    logger.error(f"❌ S3 upload failed: {e}")
                    response["s3_error"] = str(e)
                    response["image_base64"] = png_base64  # Fallback
            else:
                # Return base64 if not uploading to S3
                response["image_base64"] = png_base64
            
            return response

        else:
            raise HTTPException(
                status_code=400,
                detail="format must be 'json' or 'png'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 3D graph generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT: ANALYSIS HISTORY
# ========================================

@router.get("/analysis/history")
async def get_analysis_history(
    analysis_type: Optional[str] = Query(None, description="Filter by type"),
    limit:         int           = Query(20,   description="Max results"),
    skip:          int           = Query(0,    description="Offset")
):
    """List past analyses (newest first)"""
    try:
        results = await db.list_analysis_results(
            analysis_type=analysis_type, skip=skip, limit=limit
        )
        # Strip heavy 'results' array for listing (keep metadata only)
        for r in results:
            r.pop("results", None)
            r.pop("_id", None)

        return {"status": "success", "count": len(results), "analyses": results}

    except Exception as e:
        logger.error(f"❌ History fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

# ========================================
# HELPER FUNCTIONS
# ========================================

def _get_param_value(params: Dict[str, Any], key: str) -> Optional[float]:
    """Extract numeric value from params dict"""
    val = params.get(key)
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        return float(val.get("value", 0))
    return None


def map_water_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert full parameter names to PHREEQC chemical symbols
    
    Examples:
        {"Calcium": {"value": 17}} → {"Ca": {"value": 17}}
        {"Sulphate": {"value": 5}} → {"SO4": {"value": 5}}
    """
    
    PARAM_MAP = {
        # Cations
        "Calcium":           "Ca",
        "Magnesium":         "Mg",
        "Sodium":            "Na",
        "Potassium":         "K",
        "Barium":            "Ba",
        "Strontium":         "Sr",
        "Iron":              "Fe",
        "Aluminum":          "Al",
        "Aluminium":         "Al",
        "Lithium":           "Li",
        "Zinc":              "Zn",
        "Copper":            "Cu",
        "Tin":               "Sn",
        
        # Anions
        "Chloride":          "Cl",
        "Sulphate":          "SO4",
        "Sulfate":           "SO4",
        "Bicarbonate":       "HCO3",
        "Carbonate":         "CO3",
        "Fluoride":          "F",
        "Phosphate":         "PO4",
        
        # Other
        "Silica":            "SiO2",
        "Silicon":           "SiO2",
        "Total_Alkalinity":  "HCO3",
        "Alkalinity":        "HCO3",
        
        # Keep as-is
        "pH":                "pH",
        "Temperature":       "Temperature",
        "pe":                "pe",
        "Eh":                "Eh",
    }
    
    mapped = {}
    
    for key, value in params.items():
        if key in PARAM_MAP:
            mapped[PARAM_MAP[key]] = value
        elif key in ["Ca", "Mg", "Na", "K", "Cl", "SO4", "HCO3", "CO3", 
                     "SiO2", "Ba", "Sr", "Fe", "Al", "F", "PO4", "Li", 
                     "Zn", "Cu", "Sn", "pH", "Temperature", "pe", "Eh"]:
            mapped[key] = value
        else:
            logger.warning(f"⚠️  Unknown parameter (skipping): {key}")
    
    return mapped


@router.post("/extract-and-grid-analysis")
async def extract_and_run_grid_analysis(
    file: UploadFile = File(...),
    ph_range: Optional[str] = Query(None, description="Comma-separated: 7.0,7.5,8.0,8.5"),
    coc_range: Optional[str] = Query(None, description="Comma-separated: 2,3,4,5,6"),
    temperature_c: float = Query(25, description="Temperature in Celsius")
):
    """
    ONE-CLICK SOLUTION:
    1. Extract parameters from file (PDF/image)
    2. Auto-run grid analysis
    3. Return analysis_id for 3D graph generation
    
    Example:
    POST /extract-and-grid-analysis?ph_range=7.0,7.5,8.0&coc_range=2,3,4,5
    """
    try:
        logger.info("🚀 Extract + Grid Analysis started")
        
        # ============================================
        # STEP 1: EXTRACT PARAMETERS
        # ============================================
        
        file_content = await file.read()
        ocr = OCRService()
        extract_result = await ocr.extract_from_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        extracted_params = extract_result.get("parameters", {})
        
        if not extracted_params:
            raise HTTPException(
                status_code=400,
                detail="No parameters could be extracted from file"
            )
        
        logger.info(f"✅ Extracted {len(extracted_params)} parameters")
        
        # ============================================
        # STEP 2: PARSE GRID RANGES
        # ============================================
        
        # Default ranges
        default_ph_range = [6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
        default_coc_range = [2, 3, 4, 5, 6]
        
        # Parse user-provided ranges
        if ph_range:
            ph_list = [float(x.strip()) for x in ph_range.split(",")]
        else:
            ph_list = default_ph_range
        
        if coc_range:
            coc_list = [float(x.strip()) for x in coc_range.split(",")]
        else:
            coc_list = default_coc_range
        
        # ============================================
        # STEP 3: RUN GRID ANALYSIS
        # ============================================
        
        # Map parameters
        mapped_base = map_water_parameters(extracted_params)
        
        # Add temperature
        if "Temperature" not in mapped_base:
            mapped_base["Temperature"] = {"value": temperature_c, "unit": "°C"}
        
        # Run grid analysis
        phreeqc = PHREEQCService()
        all_results = []
        successful_count = 0
        failed_count = 0
        
        total_points = len(ph_list) * len(coc_list)
        logger.info(f"📊 Calculating {total_points} grid points...")
        
        for ph in ph_list:
            for coc in coc_list:
                # Clone and modify parameters
                grid_params = {}
                
                for key, val in mapped_base.items():
                    if key == "pH":
                        grid_params[key] = {"value": ph, "unit": None}
                    elif key == "Temperature":
                        grid_params[key] = val
                    elif key not in ["pe", "Eh"]:
                        original_val = _get_param_value(mapped_base, key)
                        if original_val and original_val > 0:
                            grid_params[key] = {
                                "value": round(original_val * coc, 3),
                                "unit": "mg/L"
                            }
                
                # Auto-fix Chloride = 0
                chloride_val = _get_param_value(grid_params, "Cl")
                if chloride_val is not None and chloride_val == 0:
                    grid_params["Cl"] = {"value": 1, "unit": "mg/L"}
                
                # Balance ions
                balance_cation = "Na" if "Na" in grid_params else "K"
                balance_anion = "Cl" if "Cl" in grid_params else "SO4"
                
                # Run analysis
                try:
                    result = await phreeqc.analyze(
                        grid_params,
                        balance_cation=balance_cation,
                        balance_anion=balance_anion
                    )
                    
                    result["pH"] = ph
                    result["CoC"] = coc
                    result["temperature_C"] = temperature_c
                    
                    all_results.append(result)
                    successful_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Grid ({ph}, {coc}) failed: {e}")
                    all_results.append({
                        "pH": ph,
                        "CoC": coc,
                        "temperature_C": temperature_c,
                        "error": str(e)
                    })
                    failed_count += 1
        
        # ============================================
        # STEP 4: SAVE TO DATABASE
        # ============================================
        
        analysis_id = f"GRID-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        analysis_doc = {
            "analysis_id": analysis_id,
            "analysis_type": "grid",
            "source": "auto_extract",
            "extracted_parameters": extracted_params,
            "base_parameters": mapped_base,
            "grid_config": {
                "ph_range": ph_list,
                "coc_range": coc_list,
                "temperature_c": temperature_c
            },
            "results": all_results,
            "metadata": {
                "total_points": total_points,
                "successful_points": successful_count,
                "failed_points": failed_count,
                "source_file": file.filename
            },
            "created_at": datetime.utcnow()
        }
        
        await db.save_analysis_result(analysis_doc)
        
        logger.info(f"✅ Auto grid analysis complete: {successful_count}/{total_points}")
        
        # ============================================
        # RESPONSE
        # ============================================
        
        return {
            "status": "success",
            "message": "File extracted and grid analysis completed",
            "analysis_id": analysis_id,
            "extracted_parameters": extracted_params,
            "grid_config": {
                "ph_range": ph_list,
                "coc_range": coc_list,
                "temperature_c": temperature_c
            },
            "results_summary": {
                "total_points": total_points,
                "successful_points": successful_count,
                "failed_points": failed_count
            },
            "next_steps": {
                "3d_graph_json": f"/api/v1/analysis/{analysis_id}/3d-graph?salt_name=Calcite&format=json",
                "3d_graph_png": f"/api/v1/analysis/{analysis_id}/3d-graph?salt_name=Calcite&format=png&upload_to_s3=true"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Auto grid analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))