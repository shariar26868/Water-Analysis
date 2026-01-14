
"""
Pydantic Models for Request/Response Validation
Fully dynamic - no hard-coded parameter lists
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


# ========== ENUMS ========== (Same as before)

class StatusEnum(str, Enum):
    optimal = "optimal"
    good = "good"
    warning = "warning"
    critical = "critical"
    unknown = "unknown"


class ComplianceStatusEnum(str, Enum):
    passed = "Passed"
    failed = "Failed"
    pending = "Pending"
    not_applicable = "N/A"


# ========== EXTRACTED PARAMETER ========== (No change needed)

class ExtractedParameter(BaseModel):
    """Single extracted parameter from PDF"""
    value: Union[float, int, str]
    unit: Optional[str] = None
    detection_limit: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "value": 7.8,
                "unit": None,
                "detection_limit": None
            }
        }


# ========== CHEMICAL STATUS ========== (No change)

class SaturationIndex(BaseModel):
    """Saturation index for a mineral"""
    mineral_name: str
    si_value: float
    status: str


class ChemicalStatus(BaseModel):
    """Chemical status from PHREEQC"""
    input_parameters: Dict[str, Any]
    solution_parameters: Dict[str, Any]
    saturation_indices: List[SaturationIndex]
    ionic_strength: float
    charge_balance_error: float
    database_used: str


# ========== GRAPH ========== (No change)

class GraphResponse(BaseModel):
    """Graph generation response"""
    graph_url: str
    graph_type: str
    color_mapping: Dict[str, str]
    created_at: datetime


class GraphModifyRequest(BaseModel):
    """Request to modify graph with prompt"""
    report_id: str
    prompt: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "WQR-2024-001",
                "prompt": "Make pH bar green and TDS bar red"
            }
        }


# ========== SCORING ========== (No change)

class ScoreComponent(BaseModel):
    """Individual score component"""
    name: str
    score: float
    max_score: float
    weight: float


class TotalScore(BaseModel):
    """Total analysis score"""
    overall_score: float
    max_score: float = 100
    rating: str
    components: List[ScoreComponent]


# ========== WATER QUALITY REPORT ========== (No change)

class WaterQualityIndex(BaseModel):
    """Water Quality Index"""
    score: float
    max_score: float = 100
    rating: str


class ComplianceScore(BaseModel):
    """Compliance score"""
    score: float
    percentage: str
    rating: str


class RiskFactor(BaseModel):
    """Risk factor assessment"""
    score: float
    max_score: float = 10
    severity: str


class QualityReport(BaseModel):
    """Complete water quality report"""
    water_quality_index: WaterQualityIndex
    compliance_score: ComplianceScore
    risk_factor: RiskFactor


# ========== CHEMICAL COMPOSITION ========== 
# 🔧 FIXED: unit is now Optional

class CompositionParameter(BaseModel):
    """Single composition parameter"""
    parameter_name: str
    value: float
    unit: Optional[str] = ""  # ✅ FIXED: Optional with default empty string
    status: StatusEnum
    threshold: Optional[Dict[str, Any]] = None


class ChemicalComposition(BaseModel):
    """Chemical composition report"""
    parameters: List[CompositionParameter]
    summary: str


# ========== BIOLOGICAL INDICATORS ========== (No change)

class BiologicalIndicator(BaseModel):
    """Single biological indicator"""
    indicator_name: str
    value: Union[float, str]
    unit: Optional[str] = None
    status: str
    risk_level: str


class BiologicalReport(BaseModel):
    """Biological indicators report"""
    indicators: List[BiologicalIndicator]
    overall_status: str


# ========== COMPLIANCE CHECKLIST ========== (No change)

class ComplianceItem(BaseModel):
    """Single compliance checklist item"""
    parameter: str
    standard: str
    status: ComplianceStatusEnum
    actual_value: Optional[float] = None
    required_value: Optional[str] = None
    remarks: Optional[str] = None


class ComplianceChecklist(BaseModel):
    """Compliance checklist"""
    items: List[ComplianceItem]
    overall_compliance: float
    passed_count: int
    failed_count: int
    pending_count: int


# ========== CONTAMINATION RISK ========== (No change)

class ContaminantRisk(BaseModel):
    """Single contaminant risk"""
    contaminant_name: str
    value: float
    unit: str
    risk_level: str
    threshold: Optional[float] = None


class ContaminationRisk(BaseModel):
    """Contamination risk analysis"""
    heavy_metals: List[ContaminantRisk]
    organic_compounds: List[ContaminantRisk]
    microbiological: List[ContaminantRisk]
    overall_severity: str
    risk_score: float


# ========== COMPLETE ANALYSIS RESPONSE ========== 
# 🔧 FIXED: Added date validator

class WaterAnalysisResponse(BaseModel):
    """Complete water analysis response (all 10 features)"""
    
    # Feature 10: Report ID
    report_id: str
    
    # Feature 1: Extracted Parameters
    extracted_parameters: Dict[str, ExtractedParameter]
    
    # Feature 2: Parameter Comparison Graph
    parameter_graph: GraphResponse
    
    # Feature 3: Chemical Status
    chemical_status: ChemicalStatus
    
    # Feature 4: Total Analysis Score
    total_score: TotalScore
    
    # Feature 5: Water Quality Report
    quality_report: QualityReport
    
    # Feature 6: Chemical Composition
    chemical_composition: ChemicalComposition
    
    # Feature 7: Biological Indicators
    biological_indicators: BiologicalReport
    
    # Feature 8: Compliance Checklist
    compliance_checklist: ComplianceChecklist
    
    # Feature 9: Contamination Risk
    contamination_risk: ContaminationRisk
    
    # Metadata
    sample_location: Optional[str] = None
    sample_date: Optional[datetime] = None
    created_at: datetime
    
    # ✅ ADDED: Date validator
    @validator('sample_date', pre=True)
    def parse_sample_date(cls, v):
        """Parse sample_date from various string formats"""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            # Try multiple date formats
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
            
            # If all fail, use current time
            return datetime.utcnow()
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "WQR-2024-001",
                "extracted_parameters": {
                    "pH": {"value": 7.8, "unit": None},
                    "Calcium": {"value": 85.5, "unit": "mg/L"}
                },
                "total_score": {
                    "overall_score": 85.0,
                    "rating": "Good"
                }
            }
        }


# ========== API REQUESTS ========== (Same as before)

class AnalyzeRequest(BaseModel):
    """Request for water analysis (file uploaded separately)"""
    sample_location: Optional[str] = None
    sample_date: Optional[datetime] = None
    custom_standards: Optional[List[str]] = None


class RecalculateRequest(BaseModel):
    """Request to recalculate with adjusted parameters"""
    report_id: str
    adjusted_parameters: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "WQR-2024-001",
                "adjusted_parameters": {
                    "Calcium": 90.0,
                    "Magnesium": 45.0
                }
            }
        }


# ========== REPORT HISTORY ========== (Same)

class ReportSummary(BaseModel):
    """Summary for report history list"""
    report_id: str
    sample_location: Optional[str]
    sample_date: Optional[datetime]
    created_at: datetime
    overall_score: float
    wqi_rating: str


class ReportHistoryResponse(BaseModel):
    """Report history response"""
    reports: List[ReportSummary]
    total_count: int
    page: int
    page_size: int


# ========== ERROR RESPONSES ========== (Same)

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ========== PARAMETER STANDARD (Admin) ========== (Same)

class ParameterStandard(BaseModel):
    """Parameter threshold standard"""
    parameter_name: str
    unit: Optional[str] = None
    thresholds: Dict[str, Dict[str, float]]
    standards: Optional[Dict[str, Dict[str, float]]] = None
    description: Optional[str] = None
    health_impact: Optional[Dict[str, str]] = None


# ========== CALCULATION FORMULA (Admin) ========== (Same)

class CalculationFormula(BaseModel):
    """Calculation formula definition"""
    formula_name: str
    formula_type: str
    required_parameters: List[str]
    formula_expression: str
    interpretation: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    description: Optional[str] = None