
"""
Water Analysis API Routes - FIXED VERSION
✅ Better error handling
✅ File validation
✅ Proper response formatting
✅ Memory management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Body
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.models.schemas import (
    WaterAnalysisResponse,
    GraphModifyRequest,
    RecalculateRequest,
    ReportHistoryResponse,
    ErrorResponse
)
from app.services.ocr_service import OCRService
from app.services.phreeqc_service import PHREEQCService
from app.services.graph_service import GraphService
from app.services.scoring_service import ScoringService
from app.services.quality_report_service import QualityReportService
from app.services.composition_service import CompositionService
from app.services.biological_service import BiologicalService
from app.services.compliance_service import ComplianceService
from app.services.risk_analysis_service import RiskAnalysisService
from app.services.report_history_service import ReportHistoryService
from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# ALLOWED FILE TYPES
# ========================================
ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "image/jpeg": "JPEG",
    "image/jpg": "JPG",
    "image/png": "PNG",
    "image/tiff": "TIFF",
    "image/tif": "TIF"
}

MAX_FILE_SIZE_MB = 50


# ========================================
# HELPER: VALIDATE FILE
# ========================================
def validate_upload_file(file: UploadFile) -> tuple[bytes, float, str]:
    """
    Validate uploaded file
    
    Returns:
        (file_content, size_mb, file_type)
    
    Raises:
        HTTPException if invalid
    """
    # Check content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES.values())}"
        )
    
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = file.filename.lower().split('.')[-1]
    if ext not in ['pdf', 'jpg', 'jpeg', 'png', 'tiff', 'tif']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension: .{ext}"
        )
    
    return (file.content_type, ALLOWED_TYPES[file.content_type])


async def read_and_validate_file(file: UploadFile) -> tuple[bytes, float]:
    """
    Read and validate file size
    
    Returns:
        (file_content, size_mb)
    """
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file")
    
    if not file_content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size_mb:.2f}MB (max: {MAX_FILE_SIZE_MB}MB)"
        )
    
    logger.info(f"File size: {file_size_mb:.2f}MB")
    
    return (file_content, file_size_mb)


# ========================================
# HELPER: ENSURE UNITS
# ========================================
def ensure_parameter_units(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all parameters have unit field (even if empty string)"""
    for param_name, param_data in parameters.items():
        if isinstance(param_data, dict):
            if "unit" not in param_data or param_data["unit"] is None:
                param_data["unit"] = ""
    return parameters


# ========================================
# ENDPOINT 1: EXTRACT ONLY - FIXED
# ========================================
@router.post("/water/extract")
async def extract_parameters_only(
    file: UploadFile = File(...),
    sample_location: Optional[str] = Query(None),
    sample_date: Optional[str] = Query(None)
):
    """
    **STEP 1: Extract parameters from PDF/Image ONLY**
    
    - NO calculations
    - NO PHREEQC
    - NO graphs
    - ONLY raw extracted data with validation
    
    **Use this to verify extraction before running expensive calculations**
    """
    ocr_service = None
    
    try:
        logger.info(f"📄 Starting extraction: {file.filename}")
        
        # Validate file type
        content_type, file_type = validate_upload_file(file)
        
        # Read and validate size
        file_content, file_size_mb = await read_and_validate_file(file)
        
        logger.info(f"✅ File validated: {file.filename} ({file_type}, {file_size_mb:.2f}MB)")
        
        # Initialize OCR service
        try:
            ocr_service = OCRService()
        except Exception as e:
            logger.error(f"Failed to initialize OCR service: {e}")
            raise HTTPException(
                status_code=500,
                detail="OCR service initialization failed. Check OPENAI_API_KEY."
            )
        
        # Extract parameters
        logger.info(f"🔍 Extracting from {file_type}...")
        
        try:
            extracted_data = await ocr_service.extract_from_file(
                file_content,
                file.filename,
                content_type
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Extraction failed: {str(e)}"
            )
        
        # Validate extraction result
        if not extracted_data:
            raise HTTPException(
                status_code=500,
                detail="Extraction returned no data"
            )
        
        if not extracted_data.get("parameters"):
            raise HTTPException(
                status_code=400,
                detail="No parameters extracted from file"
            )
        
        parameters = extracted_data["parameters"]
        
        # Ensure units
        parameters = ensure_parameter_units(parameters)
        
        logger.info(f"✅ Successfully extracted {len(parameters)} parameters")
        
        # Build response
        response = {
            "success": True,
            "message": f"Successfully extracted {len(parameters)} parameters",
            "file_info": {
                "filename": file.filename,
                "type": file_type,
                "size_mb": round(file_size_mb, 2),
                "content_type": content_type
            },
            "parameters": parameters,
            "metadata": extracted_data.get("metadata", {}),
            "validation": extracted_data.get("validation", {}),
            "extracted_at": extracted_data.get("created_at", datetime.utcnow()).isoformat() if isinstance(extracted_data.get("created_at"), datetime) else extracted_data.get("created_at")
        }
        
        return response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception("❌ Extraction endpoint failed")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Cleanup
        if ocr_service:
            del ocr_service


# ========================================
# ENDPOINT 2: ANALYZE DATA - FIXED
# ========================================
@router.post("/water/analyze-data", response_model=WaterAnalysisResponse)
async def analyze_extracted_data(
    data: Dict[str, Any] = Body(...)
):
    """
    **STEP 2: Analyze already-extracted parameters**
    
    Input format:
```json
    {
      "parameters": {
        "pH": {"value": 7.2, "unit": ""},
        "Calcium": {"value": 9.5, "unit": "mg/L"}
      },
      "sample_location": "Lab A",
      "sample_date": "2026-01-29"
    }
```
    
    Runs: PHREEQC, graphs, scoring, compliance, risk, report
    """
    try:
        logger.info("⚗️ Starting data analysis")
        
        # Extract from request body
        parameters = data.get("parameters", {})
        sample_location = data.get("sample_location")
        sample_date = data.get("sample_date")
        
        # Validate parameters
        if not parameters or not isinstance(parameters, dict):
            raise HTTPException(
                status_code=400,
                detail="No valid parameters provided"
            )
        
        if len(parameters) == 0:
            raise HTTPException(
                status_code=400,
                detail="Parameters dictionary is empty"
            )
        
        logger.info(f"⚗️ Analyzing {len(parameters)} parameters")
        
        # Ensure units
        parameters = ensure_parameter_units(parameters)
        
        # PHREEQC Analysis
        logger.info("⚗️ Running PHREEQC analysis...")
        phreeqc_service = PHREEQCService()
        try:
            chemical_status = await phreeqc_service.analyze(parameters)
        except Exception as e:
            logger.error(f"PHREEQC analysis failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Chemical analysis failed: {str(e)}"
            )
        
        # Graph Generation
        logger.info("📊 Generating parameter graph...")
        graph_service = GraphService()
        try:
            parameter_graph = await graph_service.create_parameter_graph(parameters, chemical_status)
        except Exception as e:
            logger.warning(f"Graph generation failed: {e}")
            parameter_graph = {"error": "Graph generation failed"}
        
        # Composition Analysis
        logger.info("🧪 Analyzing chemical composition...")
        composition_service = CompositionService()
        try:
            chemical_composition = await composition_service.analyze(parameters, chemical_status)
        except Exception as e:
            logger.error(f"Composition analysis failed: {e}")
            chemical_composition = {}
        
        # Biological Analysis
        logger.info("🦠 Analyzing biological indicators...")
        biological_service = BiologicalService()
        try:
            biological_indicators = await biological_service.analyze(parameters)
        except Exception as e:
            logger.warning(f"Biological analysis failed: {e}")
            biological_indicators = {}
        
        # Compliance Check
        logger.info("✓ Checking compliance...")
        compliance_service = ComplianceService()
        try:
            compliance_checklist = await compliance_service.check_compliance(parameters, chemical_status)
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            compliance_checklist = {}
        
        # Risk Analysis
        logger.info("⚠️ Analyzing contamination risks...")
        risk_service = RiskAnalysisService()
        try:
            contamination_risk = await risk_service.analyze_risks(parameters, chemical_status)
        except Exception as e:
            logger.warning(f"Risk analysis failed: {e}")
            contamination_risk = {}
        
        # Calculate Total Score
        logger.info("🎯 Calculating total score...")
        scoring_service = ScoringService()
        try:
            total_score = await scoring_service.calculate_total_score(
                chemical_composition, biological_indicators, compliance_checklist, contamination_risk
            )
        except Exception as e:
            logger.error(f"Score calculation failed: {e}")
            total_score = {"overall_score": 0, "error": str(e)}
        
        # Generate Quality Report
        logger.info("📋 Generating quality report...")
        quality_service = QualityReportService()
        try:
            quality_report = await quality_service.generate_report(
                parameters, chemical_status, compliance_checklist, contamination_risk
            )
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            quality_report = {"error": str(e)}
        
        # Save to Database
        logger.info("💾 Saving report to database...")
        history_service = ReportHistoryService()
        try:
            report_id = await history_service.save_report(
                extracted_parameters=parameters,
                chemical_status=chemical_status,
                parameter_graph=parameter_graph,
                total_score=total_score,
                quality_report=quality_report,
                chemical_composition=chemical_composition,
                biological_indicators=biological_indicators,
                compliance_checklist=compliance_checklist,
                contamination_risk=contamination_risk,
                sample_location=sample_location,
                sample_date=sample_date,
                original_filename="manual_analysis"
            )
            
            logger.info(f"✅ Analysis complete! Report ID: {report_id}")
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            report_id = "unsaved"
        
        # Build response
        return WaterAnalysisResponse(
            report_id=report_id,
            extracted_parameters=parameters,
            parameter_graph=parameter_graph,
            chemical_status=chemical_status,
            total_score=total_score,
            quality_report=quality_report,
            chemical_composition=chemical_composition,
            biological_indicators=biological_indicators,
            compliance_checklist=compliance_checklist,
            contamination_risk=contamination_risk,
            sample_location=sample_location,
            sample_date=sample_date,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception("❌ Analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


# ========================================
# ENDPOINT 3: FULL ANALYSIS - FIXED
# ========================================
@router.post("/water/analyze", response_model=WaterAnalysisResponse)
async def analyze_water_sample(
    file: UploadFile = File(...),
    sample_location: Optional[str] = Query(None),
    sample_date: Optional[str] = Query(None)
):
    """
    **COMBINED: Extract + Analyze in one step**
    
    For quick testing. For production:
    1. Use /water/extract first
    2. Then /water/analyze-data
    """
    ocr_service = None
    
    try:
        logger.info(f"📄 Starting full analysis: {file.filename}")
        
        # Validate file
        content_type, file_type = validate_upload_file(file)
        file_content, file_size_mb = await read_and_validate_file(file)
        
        logger.info(f"✅ File validated: {file_type}, {file_size_mb:.2f}MB")
        
        # Extract parameters
        logger.info("🔍 Extracting parameters...")
        ocr_service = OCRService()
        
        extracted_data = await ocr_service.extract_from_file(
            file_content,
            file.filename,
            content_type
        )
        
        if not extracted_data or not extracted_data.get("parameters"):
            raise HTTPException(
                status_code=400,
                detail="Failed to extract parameters from file"
            )
        
        parameters = extracted_data["parameters"]
        parameters = ensure_parameter_units(parameters)
        
        logger.info(f"✅ Extracted {len(parameters)} parameters")
        
        # Run all analyses (same as analyze-data endpoint)
        logger.info("⚗️ Running PHREEQC...")
        phreeqc_service = PHREEQCService()
        chemical_status = await phreeqc_service.analyze(parameters)
        
        logger.info("📊 Generating graph...")
        graph_service = GraphService()
        parameter_graph = await graph_service.create_parameter_graph(parameters, chemical_status)
        
        logger.info("🧪 Analyzing composition...")
        composition_service = CompositionService()
        chemical_composition = await composition_service.analyze(parameters, chemical_status)
        
        logger.info("🦠 Biological analysis...")
        biological_service = BiologicalService()
        biological_indicators = await biological_service.analyze(parameters)
        
        logger.info("✓ Compliance check...")
        compliance_service = ComplianceService()
        compliance_checklist = await compliance_service.check_compliance(parameters, chemical_status)
        
        logger.info("⚠️ Risk analysis...")
        risk_service = RiskAnalysisService()
        contamination_risk = await risk_service.analyze_risks(parameters, chemical_status)
        
        logger.info("🎯 Calculating score...")
        scoring_service = ScoringService()
        total_score = await scoring_service.calculate_total_score(
            chemical_composition, biological_indicators, compliance_checklist, contamination_risk
        )
        
        logger.info("📋 Generating report...")
        quality_service = QualityReportService()
        quality_report = await quality_service.generate_report(
            parameters, chemical_status, compliance_checklist, contamination_risk
        )
        
        logger.info("💾 Saving...")
        history_service = ReportHistoryService()
        report_id = await history_service.save_report(
            extracted_parameters=parameters,
            chemical_status=chemical_status,
            parameter_graph=parameter_graph,
            total_score=total_score,
            quality_report=quality_report,
            chemical_composition=chemical_composition,
            biological_indicators=biological_indicators,
            compliance_checklist=compliance_checklist,
            contamination_risk=contamination_risk,
            sample_location=sample_location,
            sample_date=sample_date,
            original_filename=file.filename
        )
        
        logger.info(f"✅ Complete! Report: {report_id}")
        
        return WaterAnalysisResponse(
            report_id=report_id,
            extracted_parameters=parameters,
            parameter_graph=parameter_graph,
            chemical_status=chemical_status,
            total_score=total_score,
            quality_report=quality_report,
            chemical_composition=chemical_composition,
            biological_indicators=biological_indicators,
            compliance_checklist=compliance_checklist,
            contamination_risk=contamination_risk,
            sample_location=sample_location,
            sample_date=sample_date,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception("❌ Full analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    
    finally:
        if ocr_service:
            del ocr_service


# ========================================
# OTHER ENDPOINTS (UNCHANGED)
# ========================================

@router.post("/water/graph/modify")
async def modify_graph_with_prompt(request: GraphModifyRequest):
    """Modify graph colors with prompt"""
    try:
        report = await db.get_water_report(request.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        graph_service = GraphService()
        updated_graph = await graph_service.modify_with_prompt(
            request.report_id,
            report["extracted_parameters"],
            request.prompt
        )
        
        await db.update_water_report(request.report_id, {"parameter_graph": updated_graph})
        
        return {
            "report_id": request.report_id,
            "updated_graph": updated_graph,
            "prompt": request.prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/water/recalculate")
async def recalculate_analysis(request: RecalculateRequest):
    """Recalculate with adjusted parameters"""
    try:
        report = await db.get_water_report(request.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        updated_parameters = {**report["extracted_parameters"]}
        for param, value in request.adjusted_parameters.items():
            if param in updated_parameters:
                updated_parameters[param]["value"] = value
        
        phreeqc_service = PHREEQCService()
        chemical_status = await phreeqc_service.analyze(updated_parameters)
        
        return {
            "report_id": request.report_id,
            "status": "recalculated",
            "adjusted": request.adjusted_parameters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/water/reports", response_model=ReportHistoryResponse)
async def get_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get paginated report history"""
    try:
        skip = (page - 1) * page_size
        reports = await db.get_all_reports(limit=page_size, skip=skip)
        total_count = await db.db.water_reports.count_documents({})
        
        summaries = [
            {
                "report_id": r["report_id"],
                "sample_location": r.get("sample_location"),
                "sample_date": r.get("sample_date"),
                "created_at": r["created_at"],
                "overall_score": r["total_score"]["overall_score"],
                "wqi_rating": r["quality_report"]["water_quality_index"]["rating"]
            }
            for r in reports
        ]
        
        return ReportHistoryResponse(
            reports=summaries,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/water/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """Get specific report"""
    try:
        report = await db.get_water_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/water/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete report"""
    try:
        deleted = await db.delete_water_report(report_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"status": "deleted", "report_id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))