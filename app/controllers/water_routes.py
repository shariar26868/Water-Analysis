
#etaaaa valo kaj koreeee

# """
# Water Analysis API Routes - FIXED VERSION
# ✅ Better error handling
# ✅ File validation
# ✅ Proper response formatting
# ✅ Memory management
# """

# from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
# from typing import Optional, Dict, Any
# import logging
# from datetime import datetime

# from app.models.schemas import (
#     WaterAnalysisResponse,
#     GraphModifyRequest,
#     RecalculateRequest,
#     ReportHistoryResponse,
#     ErrorResponse
# )
# from app.services.ocr_service import OCRService
# from app.services.phreeqc_service import PHREEQCService
# from app.services.graph_service import GraphService
# from app.services.scoring_service import ScoringService
# from app.services.quality_report_service import QualityReportService
# from app.services.composition_service import CompositionService
# from app.services.biological_service import BiologicalService
# from app.services.compliance_service import ComplianceService
# from app.services.risk_analysis_service import RiskAnalysisService
# from app.services.report_history_service import ReportHistoryService
# from app.db.mongo import db

# logger = logging.getLogger(__name__)

# router = APIRouter()


# # ========================================
# # ALLOWED FILE TYPES
# # ========================================
# ALLOWED_TYPES = {
#     "application/pdf": "PDF",
#     "image/jpeg": "JPEG",
#     "image/jpg": "JPG",
#     "image/png": "PNG",
#     "image/tiff": "TIFF",
#     "image/tif": "TIF"
# }

# MAX_FILE_SIZE_MB = 50


# # ========================================
# # HELPER: VALIDATE FILE
# # ========================================
# def validate_upload_file(file: UploadFile) -> tuple[bytes, float, str]:
#     """
#     Validate uploaded file
    
#     Returns:
#         (file_content, size_mb, file_type)
    
#     Raises:
#         HTTPException if invalid
#     """
#     # Check content type
#     if file.content_type not in ALLOWED_TYPES:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES.values())}"
#         )
    
#     # Check file extension
#     if not file.filename:
#         raise HTTPException(status_code=400, detail="No filename provided")
    
#     ext = file.filename.lower().split('.')[-1]
#     if ext not in ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif']:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid file extension: .{ext}"
#         )
    
#     return (file.content_type, ALLOWED_TYPES[file.content_type])


# async def read_and_validate_file(file: UploadFile) -> tuple[bytes, float]:
#     """
#     Read and validate file size
    
#     Returns:
#         (file_content, size_mb)
#     """
#     try:
#         file_content = await file.read()
#     except Exception as e:
#         logger.error(f"Failed to read file: {e}")
#         raise HTTPException(status_code=400, detail="Failed to read file")
    
#     if not file_content:
#         raise HTTPException(status_code=400, detail="Empty file")
    
#     file_size_mb = len(file_content) / (1024 * 1024)
    
#     if file_size_mb > MAX_FILE_SIZE_MB:
#         raise HTTPException(
#             status_code=413,
#             detail=f"File too large: {file_size_mb:.2f}MB (max: {MAX_FILE_SIZE_MB}MB)"
#         )
    
#     logger.info(f"File size: {file_size_mb:.2f}MB")
    
#     return (file_content, file_size_mb)


# # ========================================
# # HELPER: ENSURE UNITS
# # ========================================
# def ensure_parameter_units(parameters: Dict[str, Any]) -> Dict[str, Any]:
#     """Ensure all parameters have unit field (even if empty string)"""
#     for param_name, param_data in parameters.items():
#         if isinstance(param_data, dict):
#             if "unit" not in param_data or param_data["unit"] is None:
#                 param_data["unit"] = ""
#     return parameters


# # ========================================
# # ENDPOINT 1: EXTRACT ONLY - FIXED
# # ========================================
# @router.post("/water/extract")
# async def extract_parameters_only(
#     file: UploadFile = File(...),
#     sample_location: Optional[str] = Query(None),
#     sample_date: Optional[str] = Query(None)
# ):
#     """
#     **STEP 1: Extract parameters from PDF/Image ONLY**
    
#     - NO calculations
#     - NO PHREEQC
#     - NO graphs
#     - ONLY raw extracted data with validation
    
#     **Use this to verify extraction before running expensive calculations**
#     """
#     ocr_service = None
    
#     try:
#         logger.info(f"📄 Starting extraction: {file.filename}")
        
#         # Validate file type
#         content_type, file_type = validate_upload_file(file)
        
#         # Read and validate size
#         file_content, file_size_mb = await read_and_validate_file(file)
        
#         logger.info(f"✅ File validated: {file.filename} ({file_type}, {file_size_mb:.2f}MB)")
        
#         # Initialize OCR service
#         try:
#             ocr_service = OCRService()
#         except Exception as e:
#             logger.error(f"Failed to initialize OCR service: {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail="OCR service initialization failed. Check OPENAI_API_KEY."
#             )
        
#         # Extract parameters
#         logger.info(f"🔍 Extracting from {file_type}...")
        
#         try:
#             extracted_data = await ocr_service.extract_from_file(
#                 file_content,
#                 file.filename,
#                 content_type
#             )
#         except Exception as e:
#             logger.error(f"Extraction failed: {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Extraction failed: {str(e)}"
#             )
        
#         # Validate extraction result
#         if not extracted_data:
#             raise HTTPException(
#                 status_code=500,
#                 detail="Extraction returned no data"
#             )
        
#         if not extracted_data.get("parameters"):
#             raise HTTPException(
#                 status_code=400,
#                 detail="No parameters extracted from file"
#             )
        
#         parameters = extracted_data["parameters"]
        
#         # Ensure units
#         parameters = ensure_parameter_units(parameters)
        
#         logger.info(f"✅ Successfully extracted {len(parameters)} parameters")
        
#         # Build response
#         response = {
#             "success": True,
#             "message": f"Successfully extracted {len(parameters)} parameters",
#             "file_info": {
#                 "filename": file.filename,
#                 "type": file_type,
#                 "size_mb": round(file_size_mb, 2),
#                 "content_type": content_type
#             },
#             "parameters": parameters,
#             "metadata": extracted_data.get("metadata", {}),
#             "validation": extracted_data.get("validation", {}),
#             "extracted_at": extracted_data.get("created_at", datetime.utcnow()).isoformat() if isinstance(extracted_data.get("created_at"), datetime) else extracted_data.get("created_at")
#         }
        
#         return response
        
#     except HTTPException:
#         raise
        
#     except Exception as e:
#         logger.exception("❌ Extraction endpoint failed")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected error: {str(e)}"
#         )
    
#     finally:
#         # Cleanup
#         if ocr_service:
#             del ocr_service


# # ========================================
# # ENDPOINT 2: ANALYZE DATA - FIXED
# # ========================================
# @router.post("/water/analyze-data", response_model=WaterAnalysisResponse)
# async def analyze_extracted_data(
#     data: Dict[str, Any] = Body(...)
# ):
#     """
#     **STEP 2: Analyze already-extracted parameters**
    
#     Input format:
# ```json
#     {
#       "parameters": {
#         "pH": {"value": 7.2, "unit": ""},
#         "Calcium": {"value": 9.5, "unit": "mg/L"}
#       },
#       "sample_location": "Lab A",
#       "sample_date": "2026-01-29"
#     }
# ```
    
#     Runs: PHREEQC, graphs, scoring, compliance, risk, report
#     """
#     try:
#         logger.info("⚗️ Starting data analysis")
        
#         # Extract from request body
#         parameters = data.get("parameters", {})
#         sample_location = data.get("sample_location")
#         sample_date = data.get("sample_date")
        
#         # Validate parameters
#         if not parameters or not isinstance(parameters, dict):
#             raise HTTPException(
#                 status_code=400,
#                 detail="No valid parameters provided"
#             )
        
#         if len(parameters) == 0:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Parameters dictionary is empty"
#             )
        
#         logger.info(f"⚗️ Analyzing {len(parameters)} parameters")
        
#         # Ensure units
#         parameters = ensure_parameter_units(parameters)
        
#         # PHREEQC Analysis
#         logger.info("⚗️ Running PHREEQC analysis...")
#         phreeqc_service = PHREEQCService()
#         try:
#             chemical_status = await phreeqc_service.analyze(parameters)
#         except Exception as e:
#             logger.error(f"PHREEQC analysis failed: {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Chemical analysis failed: {str(e)}"
#             )
        
#         # Graph Generation
#         logger.info("📊 Generating parameter graph...")
#         graph_service = GraphService()
#         try:
#             parameter_graph = await graph_service.create_parameter_graph(parameters, chemical_status)
#         except Exception as e:
#             logger.warning(f"Graph generation failed: {e}")
#             parameter_graph = {"error": "Graph generation failed"}
        
#         # Composition Analysis
#         logger.info("🧪 Analyzing chemical composition...")
#         composition_service = CompositionService()
#         try:
#             chemical_composition = await composition_service.analyze(parameters, chemical_status)
#         except Exception as e:
#             logger.error(f"Composition analysis failed: {e}")
#             chemical_composition = {}
        
#         # Biological Analysis
#         logger.info("🦠 Analyzing biological indicators...")
#         biological_service = BiologicalService()
#         try:
#             biological_indicators = await biological_service.analyze(parameters)
#         except Exception as e:
#             logger.warning(f"Biological analysis failed: {e}")
#             biological_indicators = {}
        
#         # Compliance Check
#         logger.info("✓ Checking compliance...")
#         compliance_service = ComplianceService()
#         try:
#             compliance_checklist = await compliance_service.check_compliance(parameters, chemical_status)
#         except Exception as e:
#             logger.error(f"Compliance check failed: {e}")
#             compliance_checklist = {}
        
#         # Risk Analysis
#         logger.info("⚠️ Analyzing contamination risks...")
#         risk_service = RiskAnalysisService()
#         try:
#             contamination_risk = await risk_service.analyze_risks(parameters, chemical_status)
#         except Exception as e:
#             logger.warning(f"Risk analysis failed: {e}")
#             contamination_risk = {}
        
#         # Calculate Total Score
#         logger.info("🎯 Calculating total score...")
#         scoring_service = ScoringService()
#         try:
#             total_score = await scoring_service.calculate_total_score(
#                 chemical_composition, biological_indicators, compliance_checklist, contamination_risk
#             )
#         except Exception as e:
#             logger.error(f"Score calculation failed: {e}")
#             total_score = {"overall_score": 0, "error": str(e)}
        
#         # Generate Quality Report
#         logger.info("📋 Generating quality report...")
#         quality_service = QualityReportService()
#         try:
#             quality_report = await quality_service.generate_report(
#                 parameters, chemical_status, compliance_checklist, contamination_risk
#             )
#         except Exception as e:
#             logger.error(f"Report generation failed: {e}")
#             quality_report = {"error": str(e)}
        
#         # Save to Database
#         logger.info("💾 Saving report to database...")
#         history_service = ReportHistoryService()
#         try:
#             report_id = await history_service.save_report(
#                 extracted_parameters=parameters,
#                 chemical_status=chemical_status,
#                 parameter_graph=parameter_graph,
#                 total_score=total_score,
#                 quality_report=quality_report,
#                 chemical_composition=chemical_composition,
#                 biological_indicators=biological_indicators,
#                 compliance_checklist=compliance_checklist,
#                 contamination_risk=contamination_risk,
#                 sample_location=sample_location,
#                 sample_date=sample_date,
#                 original_filename="manual_analysis"
#             )
            
#             logger.info(f"✅ Analysis complete! Report ID: {report_id}")
            
#         except Exception as e:
#             logger.error(f"Failed to save report: {e}")
#             report_id = "unsaved"
        
#         # Build response
#         return WaterAnalysisResponse(
#             report_id=report_id,
#             extracted_parameters=parameters,
#             parameter_graph=parameter_graph,
#             chemical_status=chemical_status,
#             total_score=total_score,
#             quality_report=quality_report,
#             chemical_composition=chemical_composition,
#             biological_indicators=biological_indicators,
#             compliance_checklist=compliance_checklist,
#             contamination_risk=contamination_risk,
#             sample_location=sample_location,
#             sample_date=sample_date,
#             created_at=datetime.utcnow()
#         )
        
#     except HTTPException:
#         raise
        
#     except Exception as e:
#         logger.exception("❌ Analysis failed")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Analysis failed: {str(e)}"
#         )


# # ========================================
# # ENDPOINT 3: FULL ANALYSIS - FIXED
# # ========================================
# @router.post("/water/analyze", response_model=WaterAnalysisResponse)
# async def analyze_water_sample(
#     file: UploadFile = File(...),
#     sample_location: Optional[str] = Query(None),
#     sample_date: Optional[str] = Query(None)
# ):
#     """
#     **COMBINED: Extract + Analyze in one step**
    
#     For quick testing. For production:
#     1. Use /water/extract first
#     2. Then /water/analyze-data
#     """
#     ocr_service = None
    
#     try:
#         logger.info(f"📄 Starting full analysis: {file.filename}")
        
#         # Validate file
#         content_type, file_type = validate_upload_file(file)
#         file_content, file_size_mb = await read_and_validate_file(file)
        
#         logger.info(f"✅ File validated: {file_type}, {file_size_mb:.2f}MB")
        
#         # Extract parameters
#         logger.info("🔍 Extracting parameters...")
#         ocr_service = OCRService()
        
#         extracted_data = await ocr_service.extract_from_file(
#             file_content,
#             file.filename,
#             content_type
#         )
        
#         if not extracted_data or not extracted_data.get("parameters"):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Failed to extract parameters from file"
#             )
        
#         parameters = extracted_data["parameters"]
#         parameters = ensure_parameter_units(parameters)
        
#         logger.info(f"✅ Extracted {len(parameters)} parameters")
        
#         # Run all analyses (same as analyze-data endpoint)
#         logger.info("⚗️ Running PHREEQC...")
#         phreeqc_service = PHREEQCService()
#         chemical_status = await phreeqc_service.analyze(parameters)
        
#         logger.info("📊 Generating graph...")
#         graph_service = GraphService()
#         parameter_graph = await graph_service.create_parameter_graph(parameters, chemical_status)
        
#         logger.info("🧪 Analyzing composition...")
#         composition_service = CompositionService()
#         chemical_composition = await composition_service.analyze(parameters, chemical_status)
        
#         logger.info("🦠 Biological analysis...")
#         biological_service = BiologicalService()
#         biological_indicators = await biological_service.analyze(parameters)
        
#         logger.info("✓ Compliance check...")
#         compliance_service = ComplianceService()
#         compliance_checklist = await compliance_service.check_compliance(parameters, chemical_status)
        
#         logger.info("⚠️ Risk analysis...")
#         risk_service = RiskAnalysisService()
#         contamination_risk = await risk_service.analyze_risks(parameters, chemical_status)
        
#         logger.info("🎯 Calculating score...")
#         scoring_service = ScoringService()
#         total_score = await scoring_service.calculate_total_score(
#             chemical_composition, biological_indicators, compliance_checklist, contamination_risk
#         )
        
#         logger.info("📋 Generating report...")
#         quality_service = QualityReportService()
#         quality_report = await quality_service.generate_report(
#             parameters, chemical_status, compliance_checklist, contamination_risk
#         )
        
#         logger.info("💾 Saving...")
#         history_service = ReportHistoryService()
#         report_id = await history_service.save_report(
#             extracted_parameters=parameters,
#             chemical_status=chemical_status,
#             parameter_graph=parameter_graph,
#             total_score=total_score,
#             quality_report=quality_report,
#             chemical_composition=chemical_composition,
#             biological_indicators=biological_indicators,
#             compliance_checklist=compliance_checklist,
#             contamination_risk=contamination_risk,
#             sample_location=sample_location,
#             sample_date=sample_date,
#             original_filename=file.filename
#         )
        
#         logger.info(f"✅ Complete! Report: {report_id}")
        
#         return WaterAnalysisResponse(
#             report_id=report_id,
#             extracted_parameters=parameters,
#             parameter_graph=parameter_graph,
#             chemical_status=chemical_status,
#             total_score=total_score,
#             quality_report=quality_report,
#             chemical_composition=chemical_composition,
#             biological_indicators=biological_indicators,
#             compliance_checklist=compliance_checklist,
#             contamination_risk=contamination_risk,
#             sample_location=sample_location,
#             sample_date=sample_date,
#             created_at=datetime.utcnow()
#         )
        
#     except HTTPException:
#         raise
        
#     except Exception as e:
#         logger.exception("❌ Full analysis failed")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Analysis failed: {str(e)}"
#         )
    
#     finally:
#         if ocr_service:
#             del ocr_service


# # ========================================
# # OTHER ENDPOINTS (UNCHANGED)
# # ========================================

# @router.post("/water/graph/modify")
# async def modify_graph_with_prompt(request: GraphModifyRequest):
#     """Modify graph colors with prompt"""
#     try:
#         report = await db.get_water_report(request.report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         graph_service = GraphService()
#         updated_graph = await graph_service.modify_with_prompt(
#             request.report_id,
#             report["extracted_parameters"],
#             request.prompt
#         )
        
#         await db.update_water_report(request.report_id, {"parameter_graph": updated_graph})
        
#         return {
#             "report_id": request.report_id,
#             "updated_graph": updated_graph,
#             "prompt": request.prompt
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/water/recalculate")
# async def recalculate_analysis(request: RecalculateRequest):
#     """Recalculate with adjusted parameters"""
#     try:
#         report = await db.get_water_report(request.report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         updated_parameters = {**report["extracted_parameters"]}
#         for param, value in request.adjusted_parameters.items():
#             if param in updated_parameters:
#                 updated_parameters[param]["value"] = value
        
#         phreeqc_service = PHREEQCService()
#         chemical_status = await phreeqc_service.analyze(updated_parameters)
        
#         return {
#             "report_id": request.report_id,
#             "status": "recalculated",
#             "adjusted": request.adjusted_parameters
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/water/reports", response_model=ReportHistoryResponse)
# async def get_report_history(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100)
# ):
#     """Get paginated report history"""
#     try:
#         skip = (page - 1) * page_size
#         reports = await db.get_all_reports(limit=page_size, skip=skip)
#         total_count = await db.db.water_reports.count_documents({})
        
#         summaries = [
#             {
#                 "report_id": r["report_id"],
#                 "sample_location": r.get("sample_location"),
#                 "sample_date": r.get("sample_date"),
#                 "created_at": r["created_at"],
#                 "overall_score": r["total_score"]["overall_score"],
#                 "wqi_rating": r["quality_report"]["water_quality_index"]["rating"]
#             }
#             for r in reports
#         ]
        
#         return ReportHistoryResponse(
#             reports=summaries,
#             total_count=total_count,
#             page=page,
#             page_size=page_size
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/water/reports/{report_id}")
# async def get_report_by_id(report_id: str):
#     """Get specific report"""
#     try:
#         report = await db.get_water_report(report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
#         return report
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/water/reports/{report_id}")
# async def delete_report(report_id: str):
#     """Delete report"""
#     try:
#         deleted = await db.delete_water_report(report_id)
#         if not deleted:
#             raise HTTPException(status_code=404, detail="Report not found")
#         return {"status": "deleted", "report_id": report_id}
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))






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
        ocr = OCRService()
        parameters = await ocr.extract_parameters(file)

        return {
            "status":     "success",
            "parameters": parameters,
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
    """
    try:
        logger.info("🔬 Single-point analysis started")

        phreeqc = PHREEQCService()
        result  = await phreeqc.analyze(
            data.get("parameters", {}),
            balance_cation=data.get("balance_cation", "Na"),
            balance_anion =data.get("balance_anion",  "Cl")
        )

        # Generate graphs
        graph_svc = GraphService()
        graphs    = graph_svc.generate_si_bar_chart(result.get("saturation_indices", []))

        # Save to DB
        analysis_doc = {
            "analysis_id":  f"STD-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "analysis_type":"standard",
            "input":        data,
            "result":       result,
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
        logger.error(f"❌ Analyze failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT: STANDALONE CALCULATIONS
# ========================================

@router.post("/calculations/standalone")
async def run_standalone_calculations(data: Dict[str, Any]):
    """
    Run standalone calculations (no PHREEQC needed)
    Supports: LSI, Ryznar, Puckorius, Stiff & Davis,
              Larson-Skold, Corrosion Rates

    Request Body:
    {
        "ph": 7.5,
        "temperature_c": 30,
        "calcium_mg_l": 120,
        "alkalinity_mg_l": 200,
        "tds_mg_l": 800,
        "chloride_mg_l": 150,
        "sulfate_mg_l": 100,
        "bicarbonate_mg_l": 180,
        "carbonate_mg_l": 5,
        "dissolved_oxygen_ppm": 6.5,

        "calculations": ["lsi","ryznar","puckorius","stiff_davis","larson_skold",
                         "mild_steel","copper","admiralty_brass"]

        // Corrosion-specific (optional)
        "si_caco3": 0.3,
        "pma_ppm": 20,
        "chloride_ppm": 150,
        "free_chlorine_ppm": 0.3,
        "total_chlorine_ppm": 1.0,
        "tta_ppm": 2.0,
        "bta_ppm": 1.5,
        "mbt_ppm": 0,
        "copper_free_ppm": 0.05,
        "ammonia_ppm": 0.3
    }
    """
    try:
        logger.info("🧮 Standalone calculations requested")

        # --- Pull common values ---
        ph              = data.get("ph")
        temp_c          = data.get("temperature_c")
        calcium         = data.get("calcium_mg_l", 0)
        alkalinity      = data.get("alkalinity_mg_l", 0)
        tds             = data.get("tds_mg_l", 0)
        chloride        = data.get("chloride_mg_l", 0)
        sulfate         = data.get("sulfate_mg_l", 0)
        bicarbonate     = data.get("bicarbonate_mg_l", 0)
        carbonate       = data.get("carbonate_mg_l", 0)
        do_ppm          = data.get("dissolved_oxygen_ppm", 5.0)
        calculations    = data.get("calculations", [
            "lsi","ryznar","puckorius","stiff_davis","larson_skold"
        ])

        # --- Validate required fields ---
        if ph is None or temp_c is None:
            raise HTTPException(status_code=400, detail="ph and temperature_c are required")

        results = {}

        # --- LSI ---
        if "lsi" in calculations:
            results["lsi"] = StandaloneCalculations.calculate_lsi(
                ph=ph, temperature_c=temp_c,
                calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                tds_mg_l=tds
            )

        # --- Ryznar ---
        if "ryznar" in calculations:
            results["ryznar"] = StandaloneCalculations.calculate_ryznar(
                ph=ph, temperature_c=temp_c,
                calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                tds_mg_l=tds
            )

        # --- Puckorius ---
        if "puckorius" in calculations:
            results["puckorius"] = StandaloneCalculations.calculate_puckorius(
                temperature_c=temp_c,
                calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                tds_mg_l=tds
            )

        # --- Stiff & Davis ---
        if "stiff_davis" in calculations:
            results["stiff_davis"] = StandaloneCalculations.calculate_stiff_davis(
                ph=ph, calcium_mg_l=calcium, alkalinity_mg_l=alkalinity,
                temperature_c=temp_c, tds_mg_l=tds
            )

        # --- Larson-Skold ---
        if "larson_skold" in calculations:
            results["larson_skold"] = StandaloneCalculations.calculate_larson_skold(
                chloride_mg_l=chloride, sulfate_mg_l=sulfate,
                bicarbonate_mg_l=bicarbonate, carbonate_mg_l=carbonate
            )

        # --- Mild Steel Corrosion ---
        if "mild_steel" in calculations:
            results["mild_steel_corrosion"] = StandaloneCalculations.estimate_mild_steel_corrosion(
                ph=ph,
                dissolved_oxygen_ppm=do_ppm,
                temperature_c=temp_c,
                si_caco3=data.get("si_caco3", 0.0),
                pma_ppm =data.get("pma_ppm",  0.0),
                si_alsi =data.get("si_alsi",  -999),
                si_snsi =data.get("si_snsi",  -999),
                si_tcp  =data.get("si_tcp",   -999),
                si_zp   =data.get("si_zp",    -999)
            )

        # --- Copper Corrosion ---
        if "copper" in calculations:
            results["copper_corrosion"] = StandaloneCalculations.estimate_copper_corrosion(
                ph=ph,
                dissolved_oxygen_ppm=do_ppm,
                temperature_c=temp_c,
                si_caco3=data.get("si_caco3", 0.0),
                chloride_ppm=data.get("chloride_ppm", chloride),
                free_chlorine_ppm =data.get("free_chlorine_ppm",  0.0),
                total_chlorine_ppm=data.get("total_chlorine_ppm", 0.0),
                tta_ppm=data.get("tta_ppm", 0.0),
                bta_ppm=data.get("bta_ppm", 0.0),
                mbt_ppm=data.get("mbt_ppm", 0.0),
                copper_free_ppm=data.get("copper_free_ppm", 0.0)
            )

        # --- Admiralty Brass Corrosion ---
        if "admiralty_brass" in calculations:
            results["admiralty_brass_corrosion"] = StandaloneCalculations.estimate_admiralty_brass_corrosion(
                ph=ph,
                dissolved_oxygen_ppm=do_ppm,
                temperature_c=temp_c,
                si_caco3=data.get("si_caco3", 0.0),
                chloride_ppm=data.get("chloride_ppm", chloride),
                ammonia_ppm =data.get("ammonia_ppm",  0.0),
                free_chlorine_ppm =data.get("free_chlorine_ppm",  0.0),
                total_chlorine_ppm=data.get("total_chlorine_ppm", 0.0),
                tta_ppm=data.get("tta_ppm", 0.0),
                bta_ppm=data.get("bta_ppm", 0.0),
                mbt_ppm=data.get("mbt_ppm", 0.0),
                copper_free_ppm=data.get("copper_free_ppm", 0.0)
            )

        logger.info(f"✅ Standalone calculations done: {list(results.keys())}")

        return {
            "status":      "success",
            "calculations": results,
            "computed_at":  datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Standalone calculations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# NEW ENDPOINT: COOLING TOWER CALCULATIONS
# ========================================

@router.post("/calculations/cooling-tower")
async def run_cooling_tower_calculations(data: Dict[str, Any]):
    """
    Cooling tower system calculations

    Request Body:
    {
        "recirculation_rate_gpm": 5000,
        "hot_water_temp_f": 105,
        "cold_water_temp_f": 85,
        "wet_bulb_temp_f": 78,
        "makeup_silica_mg_l": 40,
        "recirculating_silica_mg_l": 160,
        "drift_percent": 0.1,
        "evaporation_factor_percent": 85,
        "cooling_tons": null          // optional, auto-calc from temps
    }
    """
    try:
        logger.info("🏭 Cooling tower calculations requested")

        ct = CoolingTowerService()
        results = {}

        recirc_gpm     = data.get("recirculation_rate_gpm")
        hot_temp_f     = data.get("hot_water_temp_f")
        cold_temp_f    = data.get("cold_water_temp_f")
        wet_bulb_f     = data.get("wet_bulb_temp_f")
        makeup_sio2    = data.get("makeup_silica_mg_l")
        recirc_sio2    = data.get("recirculating_silica_mg_l")
        drift_pct      = data.get("drift_percent", 0.1)
        evap_factor    = data.get("evaporation_factor_percent", 85.0)

        # --- CoC ---
        if makeup_sio2 and recirc_sio2:
            results["coc"] = ct.calculate_coc(makeup_sio2, recirc_sio2)

        # --- Range & Approach ---
        if hot_temp_f is not None and cold_temp_f is not None:
            range_f = ct.calculate_tower_range(hot_temp_f, cold_temp_f)
            results["range_f"] = range_f

            if wet_bulb_f is not None:
                approach_f = ct.calculate_approach_temperature(cold_temp_f, wet_bulb_f)
                results["approach_f"] = approach_f

                # --- Efficiency ---
                results["efficiency"] = ct.calculate_tower_efficiency(range_f, approach_f)

            # --- Evaporation ---
            if recirc_gpm is not None:
                evap = ct.calculate_evaporation_rate(recirc_gpm, range_f, evap_factor)
                results["evaporation"] = evap

                # --- Blowdown ---
                coc = results.get("coc", 3.0)
                bd  = ct.calculate_blowdown_rate(evap["evaporation_rate_gpm"], coc)
                results["blowdown"] = bd

                # --- Makeup ---
                makeup = ct.calculate_makeup_rate(
                    evap["evaporation_rate_gpm"],
                    bd["blowdown_rate_gpm"],
                    recirc_gpm, drift_pct
                )
                results["makeup"] = makeup

                # --- Heat Load ---
                results["heat_load"] = ct.calculate_heat_load(recirc_gpm, range_f)

                # --- Cooling Tons ↔ Recirc conversion ---
                results["cooling_tons"] = ct.recirculation_to_tons(recirc_gpm, range_f)

        # --- Dissolved Oxygen (needs °C) ---
        water_temp_c = data.get("water_temp_c")
        wet_bulb_c   = data.get("wet_bulb_temp_c")
        if water_temp_c is not None and wet_bulb_c is not None:
            results["dissolved_oxygen"] = ct.calculate_dissolved_oxygen(water_temp_c, wet_bulb_c)

        logger.info(f"✅ Cooling tower calculations done: {list(results.keys())}")

        return {
            "status":  "success",
            "results": results,
            "computed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cooling tower calculations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        "formulation": {"Phosphonate": 15, "Polymer": 5, "Azole": 2.5}  // optional
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
            results["usage"]      = ChemicalDosageService.calculate_chemical_usage_per_day(dosage_ppm, bd_gpm)

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

@router.get("/analysis/{analysis_id}/3d-graph")
async def get_3d_graph(
    analysis_id: str,
    salt_name:   str   = Query(...,       description="Mineral (e.g. Calcite)"),
    x_axis:      str   = Query("pH",      description="X axis: pH | CoC | temp"),
    y_axis:      str   = Query("CoC",     description="Y axis: pH | CoC | temp"),
    format:      str   = Query("json",    description="json | png")
):
    """
    Get 3D graph for a specific salt from stored analysis results.
    format=json  → raw data for frontend Plotly rendering
    format=png   → server-rendered PNG image
    """
    try:
        logger.info(f"📈 3D graph: analysis={analysis_id}, salt={salt_name}, format={format}")

        # Fetch stored analysis
        analysis = await db.get_analysis_result(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

        graph_svc = GraphService()

        if format == "json":
            graph_data = graph_svc.prepare_3d_graph_data(
                results=analysis.get("results", []),
                salt_name=salt_name,
                x_axis=x_axis,
                y_axis=y_axis
            )
            return {"status": "success", "graph_data": graph_data}

        elif format == "png":
            png_base64 = graph_svc.generate_3d_surface_png(
                results=analysis.get("results", []),
                salt_name=salt_name,
                x_axis=x_axis,
                y_axis=y_axis
            )
            return {"status": "success", "image_base64": png_base64}

        else:
            raise HTTPException(status_code=400, detail="format must be 'json' or 'png'")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 3D graph failed: {e}")
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