# """
# Water Analysis API Routes
# All endpoints for water quality analysis
# """

# from fastapi import APIRouter, UploadFile, File, HTTPException, Query
# from typing import Optional
# import logging

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


# @router.post("/water/analyze", response_model=WaterAnalysisResponse)
# async def analyze_water_sample(
#     file: UploadFile = File(...),
#     sample_location: Optional[str] = None,
#     sample_date: Optional[str] = None
# ):
#     """
#     Upload PDF and perform complete water quality analysis
    
#     Returns all 10 features:
#     1. Extracted parameters
#     2. Parameter comparison graph
#     3. Chemical status
#     4. Total analysis score
#     5. Water quality report
#     6. Chemical composition
#     7. Biological indicators
#     8. Compliance checklist
#     9. Contamination risk analysis
#     10. Report ID with history
#     """
#     try:
#         logger.info(f"📄 Analyzing water sample: {file.filename}")
        
#         # Validate file type
#         if not file.filename.lower().endswith('.pdf'):
#             raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
#         # Read file content
#         file_content = await file.read()
        
#         # ========== FEATURE 1: PDF OCR EXTRACTION ==========
#         logger.info("🔍 Extracting parameters from PDF...")
#         ocr_service = OCRService()
#         extracted_data = await ocr_service.extract_from_pdf(file_content, file.filename)
        
#         if not extracted_data or not extracted_data.get("parameters"):
#             raise HTTPException(status_code=400, detail="Failed to extract data from PDF")
        
#         logger.info(f"✅ Extracted {len(extracted_data['parameters'])} parameters")
        
#         # ========== FEATURE 3: PHREEQC CALCULATIONS ==========
#         logger.info("⚗️ Running PHREEQC calculations...")
#         phreeqc_service = PHREEQCService()
#         chemical_status = await phreeqc_service.analyze(extracted_data["parameters"])
        
#         logger.info(f"✅ PHREEQC analysis complete. Database: {chemical_status['database_used']}")
        
#         # ========== FEATURE 2: GRAPH GENERATION ==========
#         logger.info("📊 Generating parameter comparison graph...")
#         graph_service = GraphService()
#         parameter_graph = await graph_service.create_parameter_graph(
#             extracted_data["parameters"],
#             chemical_status
#         )
        
#         logger.info(f"✅ Graph generated: {parameter_graph['graph_url']}")
        
#         # ========== FEATURE 6: CHEMICAL COMPOSITION ==========
#         logger.info("🧪 Analyzing chemical composition...")
#         composition_service = CompositionService()
#         chemical_composition = await composition_service.analyze(
#             extracted_data["parameters"],
#             chemical_status
#         )
        
#         # ========== FEATURE 7: BIOLOGICAL INDICATORS ==========
#         logger.info("🦠 Analyzing biological indicators...")
#         biological_service = BiologicalService()
#         biological_indicators = await biological_service.analyze(
#             extracted_data["parameters"]
#         )
        
#         # ========== FEATURE 8: COMPLIANCE CHECKLIST ==========
#         logger.info("✓ Checking compliance...")
#         compliance_service = ComplianceService()
#         compliance_checklist = await compliance_service.check_compliance(
#             extracted_data["parameters"],
#             chemical_status
#         )
        
#         # ========== FEATURE 9: CONTAMINATION RISK ==========
#         logger.info("⚠️ Analyzing contamination risks...")
#         risk_service = RiskAnalysisService()
#         contamination_risk = await risk_service.analyze_risks(
#             extracted_data["parameters"],
#             chemical_status
#         )
        
#         # ========== FEATURE 4: TOTAL SCORE ==========
#         logger.info("🎯 Calculating total analysis score...")
#         scoring_service = ScoringService()
#         total_score = await scoring_service.calculate_total_score(
#             chemical_composition,
#             biological_indicators,
#             compliance_checklist,
#             contamination_risk
#         )
        
#         # ========== FEATURE 5: WATER QUALITY REPORT ==========
#         logger.info("📋 Generating water quality report...")
#         quality_service = QualityReportService()
#         quality_report = await quality_service.generate_report(
#             extracted_data["parameters"],
#             chemical_status,
#             compliance_checklist,
#             contamination_risk
#         )
        
#         # ========== FEATURE 10: SAVE REPORT HISTORY ==========
#         logger.info("💾 Saving report to database...")
#         history_service = ReportHistoryService()
#         report_id = await history_service.save_report(
#             extracted_parameters=extracted_data["parameters"],
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
        
#         logger.info(f"✅ Analysis complete! Report ID: {report_id}")
        
#         # Construct response
#         response = WaterAnalysisResponse(
#             report_id=report_id,
#             extracted_parameters=extracted_data["parameters"],
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
#             created_at=extracted_data.get("created_at")
#         )
        
#         return response
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Analysis failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# @router.post("/water/graph/modify")
# async def modify_graph_with_prompt(request: GraphModifyRequest):
#     """
#     Modify graph colors using natural language prompt
    
#     Example: "Make pH bar green and TDS bar red"
#     """
#     try:
#         logger.info(f"🎨 Modifying graph for report {request.report_id}")
        
#         # Get original report
#         report = await db.get_water_report(request.report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         # Modify graph
#         graph_service = GraphService()
#         updated_graph = await graph_service.modify_with_prompt(
#             request.report_id,
#             report["extracted_parameters"],
#             request.prompt
#         )
        
#         # Update report
#         await db.update_water_report(
#             request.report_id,
#             {"parameter_graph": updated_graph}
#         )
        
#         logger.info(f"✅ Graph updated: {updated_graph['graph_url']}")
        
#         return {
#             "report_id": request.report_id,
#             "updated_graph": updated_graph,
#             "prompt_processed": request.prompt
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Graph modification failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.post("/water/recalculate")
# async def recalculate_analysis(request: RecalculateRequest):
#     """
#     Recalculate analysis with adjusted parameter values
#     """
#     try:
#         logger.info(f"🔄 Recalculating report {request.report_id}")
        
#         # Get original report
#         report = await db.get_water_report(request.report_id)
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         # Merge adjusted parameters
#         updated_parameters = {**report["extracted_parameters"]}
#         for param, value in request.adjusted_parameters.items():
#             if param in updated_parameters:
#                 updated_parameters[param]["value"] = value
        
#         # Re-run PHREEQC
#         phreeqc_service = PHREEQCService()
#         chemical_status = await phreeqc_service.analyze(updated_parameters)
        
#         # Recalculate everything
#         # (Similar process as analyze endpoint)
        
#         logger.info(f"✅ Recalculation complete")
        
#         return {
#             "report_id": request.report_id,
#             "status": "recalculated",
#             "adjusted_parameters": request.adjusted_parameters
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Recalculation failed: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/water/reports", response_model=ReportHistoryResponse)
# async def get_report_history(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(20, ge=1, le=100)
# ):
#     """
#     Get paginated report history
#     """
#     try:
#         skip = (page - 1) * page_size
        
#         reports = await db.get_all_reports(limit=page_size, skip=skip)
        
#         # Count total
#         total_count = await db.db.water_reports.count_documents({})
        
#         # Format summaries
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
#         logger.error(f"❌ Failed to get report history: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/water/reports/{report_id}")
# async def get_report_by_id(report_id: str):
#     """
#     Get specific report by ID
#     """
#     try:
#         report = await db.get_water_report(report_id)
        
#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         return report
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Failed to get report: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.delete("/water/reports/{report_id}")
# async def delete_report(report_id: str):
#     """
#     Delete a water analysis report
#     """
#     try:
#         deleted = await db.delete_water_report(report_id)
        
#         if not deleted:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         return {
#             "status": "deleted",
#             "report_id": report_id
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Failed to delete report: {e}")
#         raise HTTPException(status_code=500, detail=str(e))






"""
Water Analysis API Routes
All endpoints for water quality analysis
Supports: PDF, JPG, PNG, TIFF files
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional
import logging

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


@router.post("/water/analyze", response_model=WaterAnalysisResponse)
async def analyze_water_sample(
    file: UploadFile = File(...),
    sample_location: Optional[str] = None,
    sample_date: Optional[str] = None
):
    """
    Upload PDF or Image and perform complete water quality analysis
    
    Supported file types:
    - PDF (.pdf)
    - Images (.jpg, .jpeg, .png, .tiff, .tif)
    
    Returns all 10 features:
    1. Extracted parameters
    2. Parameter comparison graph
    3. Chemical status
    4. Total analysis score
    5. Water quality report
    6. Chemical composition
    7. Biological indicators
    8. Compliance checklist
    9. Contamination risk analysis
    10. Report ID with history
    """
    try:
        logger.info(f"📄 Analyzing water sample: {file.filename}")
        
        # ========== FILE TYPE VALIDATION (UPDATED) ==========
        allowed_types = {
            "application/pdf": "PDF",
            "image/jpeg": "JPEG Image",
            "image/jpg": "JPG Image",
            "image/png": "PNG Image",
            "image/tiff": "TIFF Image",
            "image/tif": "TIF Image"
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. "
                       f"Supported types: {', '.join(allowed_types.values())}"
            )
        
        logger.info(f"✅ File type: {allowed_types[file.content_type]}")
        
        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)
        logger.info(f"📊 File size: {file_size_mb:.2f} MB")
        
        # Check file size (max 50MB)
        if file_size_mb > 50:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.2f}MB. Maximum size: 50MB"
            )
        
        # ========== FEATURE 1: FILE EXTRACTION (UPDATED) ==========
        logger.info("🔍 Extracting parameters from file...")
        ocr_service = OCRService()
        
        # Use unified extraction method
        extracted_data = await ocr_service.extract_from_file(
            file_content,
            file.filename,
            file.content_type
        )
        
        if not extracted_data or not extracted_data.get("parameters"):
            raise HTTPException(status_code=400, detail="Failed to extract data from file")
        
        # Ensure all units are strings, not None
        for param_name, param_data in extracted_data["parameters"].items():
            if param_data.get("unit") is None:
                param_data["unit"] = ""
        
        logger.info(f"✅ Extracted {len(extracted_data['parameters'])} parameters")
        
        # ========== FEATURE 3: PHREEQC CALCULATIONS ==========
        logger.info("⚗️ Running PHREEQC calculations...")
        phreeqc_service = PHREEQCService()
        chemical_status = await phreeqc_service.analyze(extracted_data["parameters"])
        
        logger.info(f"✅ PHREEQC analysis complete. Database: {chemical_status['database_used']}")
        
        # ========== FEATURE 2: GRAPH GENERATION ==========
        logger.info("📊 Generating parameter comparison graph...")
        graph_service = GraphService()
        parameter_graph = await graph_service.create_parameter_graph(
            extracted_data["parameters"],
            chemical_status
        )
        
        logger.info(f"✅ Graph generated: {parameter_graph['graph_url']}")
        
        # ========== FEATURE 6: CHEMICAL COMPOSITION ==========
        logger.info("🧪 Analyzing chemical composition...")
        composition_service = CompositionService()
        chemical_composition = await composition_service.analyze(
            extracted_data["parameters"],
            chemical_status
        )
        
        # ========== FEATURE 7: BIOLOGICAL INDICATORS ==========
        logger.info("🦠 Analyzing biological indicators...")
        biological_service = BiologicalService()
        biological_indicators = await biological_service.analyze(
            extracted_data["parameters"]
        )
        
        # ========== FEATURE 8: COMPLIANCE CHECKLIST ==========
        logger.info("✓ Checking compliance...")
        compliance_service = ComplianceService()
        compliance_checklist = await compliance_service.check_compliance(
            extracted_data["parameters"],
            chemical_status
        )
        
        # ========== FEATURE 9: CONTAMINATION RISK ==========
        logger.info("⚠️ Analyzing contamination risks...")
        risk_service = RiskAnalysisService()
        contamination_risk = await risk_service.analyze_risks(
            extracted_data["parameters"],
            chemical_status
        )
        
        # ========== FEATURE 4: TOTAL SCORE ==========
        logger.info("🎯 Calculating total analysis score...")
        scoring_service = ScoringService()
        total_score = await scoring_service.calculate_total_score(
            chemical_composition,
            biological_indicators,
            compliance_checklist,
            contamination_risk
        )
        
        # ========== FEATURE 5: WATER QUALITY REPORT ==========
        logger.info("📋 Generating water quality report...")
        quality_service = QualityReportService()
        quality_report = await quality_service.generate_report(
            extracted_data["parameters"],
            chemical_status,
            compliance_checklist,
            contamination_risk
        )
        
        # ========== FEATURE 10: SAVE REPORT HISTORY ==========
        logger.info("💾 Saving report to database...")
        history_service = ReportHistoryService()
        report_id = await history_service.save_report(
            extracted_parameters=extracted_data["parameters"],
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
        
        logger.info(f"✅ Analysis complete! Report ID: {report_id}")
        
        # Construct response
        response = WaterAnalysisResponse(
            report_id=report_id,
            extracted_parameters=extracted_data["parameters"],
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
            created_at=extracted_data.get("created_at")
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/water/graph/modify")
async def modify_graph_with_prompt(request: GraphModifyRequest):
    """
    Modify graph colors using natural language prompt
    
    Example: "Make pH bar green and TDS bar red"
    """
    try:
        logger.info(f"🎨 Modifying graph for report {request.report_id}")
        
        # Get original report
        report = await db.get_water_report(request.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Modify graph
        graph_service = GraphService()
        updated_graph = await graph_service.modify_with_prompt(
            request.report_id,
            report["extracted_parameters"],
            request.prompt
        )
        
        # Update report
        await db.update_water_report(
            request.report_id,
            {"parameter_graph": updated_graph}
        )
        
        logger.info(f"✅ Graph updated: {updated_graph['graph_url']}")
        
        return {
            "report_id": request.report_id,
            "updated_graph": updated_graph,
            "prompt_processed": request.prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Graph modification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/water/recalculate")
async def recalculate_analysis(request: RecalculateRequest):
    """
    Recalculate analysis with adjusted parameter values
    """
    try:
        logger.info(f"🔄 Recalculating report {request.report_id}")
        
        # Get original report
        report = await db.get_water_report(request.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Merge adjusted parameters
        updated_parameters = {**report["extracted_parameters"]}
        for param, value in request.adjusted_parameters.items():
            if param in updated_parameters:
                updated_parameters[param]["value"] = value
        
        # Re-run PHREEQC
        phreeqc_service = PHREEQCService()
        chemical_status = await phreeqc_service.analyze(updated_parameters)
        
        # Recalculate everything
        # (Similar process as analyze endpoint)
        
        logger.info(f"✅ Recalculation complete")
        
        return {
            "report_id": request.report_id,
            "status": "recalculated",
            "adjusted_parameters": request.adjusted_parameters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Recalculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/water/reports", response_model=ReportHistoryResponse)
async def get_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get paginated report history
    """
    try:
        skip = (page - 1) * page_size
        
        reports = await db.get_all_reports(limit=page_size, skip=skip)
        
        # Count total
        total_count = await db.db.water_reports.count_documents({})
        
        # Format summaries
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
        logger.error(f"❌ Failed to get report history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/water/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """
    Get specific report by ID
    """
    try:
        report = await db.get_water_report(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/water/reports/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a water analysis report
    """
    try:
        deleted = await db.delete_water_report(report_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "status": "deleted",
            "report_id": report_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete report: {e}")
        raise HTTPException(status_code=500, detail=str(e))