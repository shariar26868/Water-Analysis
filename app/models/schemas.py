
# """
# Pydantic Models for Request/Response Validation
# Fully dynamic - no hard-coded parameter lists
# WITH Chemical Formula Support
# """

# from pydantic import BaseModel, Field, validator
# from typing import Dict, List, Optional, Any, Union
# from datetime import datetime
# from enum import Enum


# # ========== ENUMS ==========

# class StatusEnum(str, Enum):
#     optimal = "optimal"
#     good = "good"
#     warning = "warning"
#     critical = "critical"
#     unknown = "unknown"


# class ComplianceStatusEnum(str, Enum):
#     passed = "Passed"
#     failed = "Failed"
#     pending = "Pending"
#     not_applicable = "N/A"


# # ========== EXTRACTED PARAMETER ==========

# class ExtractedParameter(BaseModel):
#     """Single extracted parameter from PDF"""
#     value: Union[float, int, str]
#     unit: Optional[str] = None
#     detection_limit: Optional[float] = None
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "value": 7.8,
#                 "unit": None,
#                 "detection_limit": None
#             }
#         }


# # ========== CHEMICAL STATUS ==========

# class SaturationIndex(BaseModel):
#     """Saturation index for a mineral"""
#     mineral_name: str
#     si_value: float
#     status: str


# class ChemicalStatus(BaseModel):
#     """Chemical status from PHREEQC"""
#     input_parameters: Dict[str, Any]
#     solution_parameters: Dict[str, Any]
#     saturation_indices: List[SaturationIndex]
#     ionic_strength: float
#     charge_balance_error: float
#     database_used: str


# # ========== GRAPH ==========

# class GraphResponse(BaseModel):
#     """Graph generation response"""
#     graph_url: str
#     graph_type: str
#     color_mapping: Dict[str, str]
#     created_at: datetime


# class GraphModifyRequest(BaseModel):
#     """Request to modify graph with prompt"""
#     report_id: str
#     prompt: str
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "report_id": "WQR-2024-001",
#                 "prompt": "Make pH bar green and TDS bar red"
#             }
#         }


# # ========== SCORING ==========

# class ScoreComponent(BaseModel):
#     """Individual score component"""
#     name: str
#     score: float
#     max_score: float
#     weight: float


# class TotalScore(BaseModel):
#     """Total analysis score"""
#     overall_score: float
#     max_score: float = 100
#     rating: str
#     components: List[ScoreComponent]


# # ========== WATER QUALITY REPORT ==========

# class WaterQualityIndex(BaseModel):
#     """Water Quality Index"""
#     score: float
#     max_score: float = 100
#     rating: str


# class ComplianceScore(BaseModel):
#     """Compliance score"""
#     score: float
#     percentage: str
#     rating: str


# class RiskFactor(BaseModel):
#     """Risk factor assessment"""
#     score: float
#     max_score: float = 10
#     severity: str


# class QualityReport(BaseModel):
#     """Complete water quality report"""
#     water_quality_index: WaterQualityIndex
#     compliance_score: ComplianceScore
#     risk_factor: RiskFactor


# # ========== CHEMICAL COMPOSITION ========== 
# # ✅ UPDATED: Added chemical formula fields

# class CompositionParameter(BaseModel):
#     """Single composition parameter with chemical formula support"""
#     parameter_name: str
#     value: float
#     unit: Optional[str] = ""  # ✅ Optional with default empty string
#     status: StatusEnum
#     threshold: Optional[Dict[str, Any]] = None
    
#     # ✅ NEW: Chemical formula fields
#     chemical_symbol: Optional[str] = None           # "Ca"
#     chemical_formula: Optional[str] = None          # "Ca²⁺"
#     ionic_form: Optional[str] = None                # "Ca2+"
#     as_compound: Optional[str] = None               # "CaCO₃"
#     as_compound_value: Optional[float] = None       # Converted value as CaCO3
#     molecular_weight: Optional[float] = None        # 40.078
#     charge: Optional[int] = None                    # 2
#     category: Optional[str] = None                  # "major_cation"
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "parameter_name": "Calcium",
#                 "value": 85.5,
#                 "unit": "mg/L",
#                 "status": "good",
#                 "threshold": {"optimal": {"min": 0, "max": 100}},
#                 "chemical_symbol": "Ca",
#                 "chemical_formula": "Ca²⁺",
#                 "ionic_form": "Ca2+",
#                 "as_compound": "CaCO₃",
#                 "as_compound_value": 213.52,
#                 "molecular_weight": 40.078,
#                 "charge": 2,
#                 "category": "major_cation"
#             }
#         }


# class ChemicalComposition(BaseModel):
#     """Chemical composition report"""
#     parameters: List[CompositionParameter]
#     summary: str


# # ========== BIOLOGICAL INDICATORS ==========

# class BiologicalIndicator(BaseModel):
#     """Single biological indicator"""
#     indicator_name: str
#     value: Union[float, str]
#     unit: Optional[str] = None
#     status: str
#     risk_level: str


# class BiologicalReport(BaseModel):
#     """Biological indicators report"""
#     indicators: List[BiologicalIndicator]
#     overall_status: str


# # ========== COMPLIANCE CHECKLIST ==========

# class ComplianceItem(BaseModel):
#     """Single compliance checklist item"""
#     parameter: str
#     standard: str
#     status: ComplianceStatusEnum
#     actual_value: Optional[float] = None
#     required_value: Optional[str] = None
#     remarks: Optional[str] = None


# class ComplianceChecklist(BaseModel):
#     """Compliance checklist"""
#     items: List[ComplianceItem]
#     overall_compliance: float
#     passed_count: int
#     failed_count: int
#     pending_count: int


# # ========== CONTAMINATION RISK ==========

# class ContaminantRisk(BaseModel):
#     """Single contaminant risk"""
#     contaminant_name: str
#     value: float
#     unit: str
#     risk_level: str
#     threshold: Optional[float] = None


# class ContaminationRisk(BaseModel):
#     """Contamination risk analysis"""
#     heavy_metals: List[ContaminantRisk]
#     organic_compounds: List[ContaminantRisk]
#     microbiological: List[ContaminantRisk]
#     overall_severity: str
#     risk_score: float


# # ========== COMPLETE ANALYSIS RESPONSE ========== 

# class WaterAnalysisResponse(BaseModel):
#     """Complete water analysis response (all 10 features)"""
    
#     # Feature 10: Report ID
#     report_id: str
    
#     # Feature 1: Extracted Parameters
#     extracted_parameters: Dict[str, ExtractedParameter]
    
#     # Feature 2: Parameter Comparison Graph
#     parameter_graph: GraphResponse
    
#     # Feature 3: Chemical Status
#     chemical_status: ChemicalStatus
    
#     # Feature 4: Total Analysis Score
#     total_score: TotalScore
    
#     # Feature 5: Water Quality Report
#     quality_report: QualityReport
    
#     # Feature 6: Chemical Composition
#     chemical_composition: ChemicalComposition
    
#     # Feature 7: Biological Indicators
#     biological_indicators: BiologicalReport
    
#     # Feature 8: Compliance Checklist
#     compliance_checklist: ComplianceChecklist
    
#     # Feature 9: Contamination Risk
#     contamination_risk: ContaminationRisk
    
#     # Metadata
#     sample_location: Optional[str] = None
#     sample_date: Optional[datetime] = None
#     created_at: datetime
    
#     # ✅ Date validator
#     @validator('sample_date', pre=True)
#     def parse_sample_date(cls, v):
#         """Parse sample_date from various string formats"""
#         if v is None:
#             return None
        
#         if isinstance(v, datetime):
#             return v
        
#         if isinstance(v, str):
#             # Try multiple date formats
#             for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
#                 try:
#                     return datetime.strptime(v, fmt)
#                 except ValueError:
#                     continue
            
#             # If all fail, use current time
#             return datetime.utcnow()
        
#         return v
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "report_id": "WQR-2024-001",
#                 "extracted_parameters": {
#                     "pH": {"value": 7.8, "unit": None},
#                     "Calcium": {"value": 85.5, "unit": "mg/L"}
#                 },
#                 "total_score": {
#                     "overall_score": 85.0,
#                     "rating": "Good"
#                 }
#             }
#         }


# # ========== API REQUESTS ==========

# class AnalyzeRequest(BaseModel):
#     """Request for water analysis (file uploaded separately)"""
#     sample_location: Optional[str] = None
#     sample_date: Optional[datetime] = None
#     custom_standards: Optional[List[str]] = None


# class RecalculateRequest(BaseModel):
#     """Request to recalculate with adjusted parameters"""
#     report_id: str
#     adjusted_parameters: Dict[str, float]
    
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "report_id": "WQR-2024-001",
#                 "adjusted_parameters": {
#                     "Calcium": 90.0,
#                     "Magnesium": 45.0
#                 }
#             }
#         }


# # ========== REPORT HISTORY ==========

# class ReportSummary(BaseModel):
#     """Summary for report history list"""
#     report_id: str
#     sample_location: Optional[str]
#     sample_date: Optional[datetime]
#     created_at: datetime
#     overall_score: float
#     wqi_rating: str


# class ReportHistoryResponse(BaseModel):
#     """Report history response"""
#     reports: List[ReportSummary]
#     total_count: int
#     page: int
#     page_size: int


# # ========== ERROR RESPONSES ==========

# class ErrorResponse(BaseModel):
#     """Standard error response"""
#     error: str
#     detail: Optional[str] = None
#     timestamp: datetime = Field(default_factory=datetime.utcnow)


# # ========== PARAMETER STANDARD (Admin) ==========

# class ParameterStandard(BaseModel):
#     """Parameter threshold standard"""
#     parameter_name: str
#     unit: Optional[str] = None
#     thresholds: Dict[str, Dict[str, float]]
#     standards: Optional[Dict[str, Dict[str, float]]] = None
#     description: Optional[str] = None
#     health_impact: Optional[Dict[str, str]] = None


# # ========== CALCULATION FORMULA (Admin) ==========

# class CalculationFormula(BaseModel):
#     """Calculation formula definition"""
#     formula_name: str
#     formula_type: str
#     required_parameters: List[str]
#     formula_expression: str
#     interpretation: Optional[Dict[str, Any]] = None
#     unit: Optional[str] = None
#     description: Optional[str] = None




"""
Pydantic Schemas for Water Quality Analysis
UPDATED: Added Customer, Asset, Product, Analysis schemas
FIXED: Uncommented required classes for water_routes.py
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime
from enum import Enum


# ========================================
# EXISTING SCHEMAS (Keep as-is)
# ========================================

class WaterParameter(BaseModel):
    """Single water quality parameter"""
    name: str
    value: float
    unit: str
    confidence: Optional[float] = None


class WaterAnalysisInput(BaseModel):
    """Input for water analysis"""
    parameters: Dict[str, Any]
    sample_id: Optional[str] = None
    sample_date: Optional[datetime] = None
    location: Optional[str] = None


class SaturationIndex(BaseModel):
    """Saturation index result for a mineral"""
    mineral_name: str
    si_value: float
    interpretation: str


class PHREEQCResult(BaseModel):
    """PHREEQC analysis result"""
    saturation_indices: List[SaturationIndex]
    ionic_strength: float
    charge_balance_error: float
    database_used: str
    warnings: Optional[List[str]] = None


# ========================================
# ENUMS
# ========================================

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


# ========================================
# EXTRACTED PARAMETER
# ========================================

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


# ========================================
# CHEMICAL STATUS
# ========================================

class ChemicalStatus(BaseModel):
    """Chemical status from PHREEQC"""
    input_parameters: Dict[str, Any]
    solution_parameters: Dict[str, Any]
    saturation_indices: List[SaturationIndex]
    ionic_strength: float
    charge_balance_error: float
    database_used: str


# ========================================
# GRAPH
# ========================================

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


# ========================================
# SCORING
# ========================================

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


# ========================================
# WATER QUALITY REPORT
# ========================================

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


# ========================================
# CHEMICAL COMPOSITION
# ========================================

class CompositionParameter(BaseModel):
    """Single composition parameter with chemical formula support"""
    parameter_name: str
    value: float
    unit: Optional[str] = ""
    status: StatusEnum
    threshold: Optional[Dict[str, Any]] = None
    
    # Chemical formula fields
    chemical_symbol: Optional[str] = None
    chemical_formula: Optional[str] = None
    ionic_form: Optional[str] = None
    as_compound: Optional[str] = None
    as_compound_value: Optional[float] = None
    molecular_weight: Optional[float] = None
    charge: Optional[int] = None
    category: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "parameter_name": "Calcium",
                "value": 85.5,
                "unit": "mg/L",
                "status": "good",
                "threshold": {"optimal": {"min": 0, "max": 100}},
                "chemical_symbol": "Ca",
                "chemical_formula": "Ca²⁺",
                "ionic_form": "Ca2+",
                "as_compound": "CaCO₃",
                "as_compound_value": 213.52,
                "molecular_weight": 40.078,
                "charge": 2,
                "category": "major_cation"
            }
        }


class ChemicalComposition(BaseModel):
    """Chemical composition report"""
    parameters: List[CompositionParameter]
    summary: str


# ========================================
# BIOLOGICAL INDICATORS
# ========================================

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


# ========================================
# COMPLIANCE CHECKLIST
# ========================================

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


# ========================================
# CONTAMINATION RISK
# ========================================

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


# ========================================
# COMPLETE ANALYSIS RESPONSE
# ========================================

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
    
    @validator('sample_date', pre=True)
    def parse_sample_date(cls, v):
        """Parse sample_date from various string formats"""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    return datetime.strptime(v, fmt)
                except ValueError:
                    continue
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


# ========================================
# API REQUESTS
# ========================================

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


# ========================================
# REPORT HISTORY
# ========================================

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


# ========================================
# ERROR RESPONSES
# ========================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ========================================
# PARAMETER STANDARD (Admin)
# ========================================

class ParameterStandard(BaseModel):
    """Parameter threshold standard"""
    parameter_name: str
    unit: Optional[str] = None
    thresholds: Dict[str, Dict[str, float]]
    standards: Optional[Dict[str, Dict[str, float]]] = None
    description: Optional[str] = None
    health_impact: Optional[Dict[str, str]] = None


# ========================================
# CALCULATION FORMULA (Admin)
# ========================================

class CalculationFormula(BaseModel):
    """Calculation formula definition"""
    formula_name: str
    formula_type: str
    required_parameters: List[str]
    formula_expression: str
    interpretation: Optional[Dict[str, Any]] = None
    unit: Optional[str] = None
    description: Optional[str] = None


# ========================================
# NEW SCHEMAS - CUSTOMER & ASSET MANAGEMENT
# ========================================

class AddressSchema(BaseModel):
    """Physical address"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None


class ContactInfoSchema(BaseModel):
    """Contact information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None


class CustomerSchema(BaseModel):
    """Customer/Company information"""
    customer_id: str = Field(..., description="Unique customer ID")
    company_name: str = Field(..., description="Company name")
    industry: Optional[str] = None
    address: Optional[AddressSchema] = None
    primary_contact: Optional[ContactInfoSchema] = None
    billing_contact: Optional[ContactInfoSchema] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: Literal["active", "inactive", "pending"] = "active"
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetSchema(BaseModel):
    """Cooling tower or cooling water system asset"""
    asset_id: str = Field(..., description="Unique asset ID")
    customer_id: str = Field(..., description="Owner customer ID")
    asset_name: str = Field(..., description="Asset name/identifier")
    asset_type: Literal["cooling_tower", "chiller", "boiler", "closed_loop", "other"] = "cooling_tower"
    location: Optional[str] = None
    
    # Operating parameters
    recirculation_rate_gpm: Optional[float] = None
    design_coc: Optional[float] = None
    operating_temp_range_f: Optional[List[float]] = None
    heat_load_tons: Optional[float] = None
    
    # Metadata
    installed_date: Optional[datetime] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    capacity: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: Literal["active", "inactive", "maintenance"] = "active"
    notes: Optional[str] = None


# ========================================
# NEW SCHEMAS - RAW MATERIALS & PRODUCTS
# ========================================

class AccessLevelEnum(str, Enum):
    """Access control levels"""
    GLOBAL = "global"
    COMPANY = "company"
    USER = "user"


class RawMaterialSchema(BaseModel):
    """Raw material/chemical component"""
    material_id: str = Field(..., description="Unique material ID")
    material_name: str = Field(..., description="Chemical name")
    cas_number: Optional[str] = None
    chemical_formula: Optional[str] = None
    
    molecular_weight: Optional[float] = None
    density_lbs_per_gal: Optional[float] = None
    active_percent: float = Field(100.0, description="Active ingredient %")
    
    category: Optional[str] = None
    function: Optional[str] = None
    
    access_level: AccessLevelEnum = AccessLevelEnum.GLOBAL
    owner_company_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    
    safety_data_sheet_url: Optional[str] = None
    hazard_classification: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    notes: Optional[str] = None


class ProductFormulation(BaseModel):
    """Product formulation - raw materials with percentages"""
    raw_material_id: str
    active_percent: float = Field(..., ge=0, le=100, description="Active % in product")


class ProductSchema(BaseModel):
    """Finished product (blend of raw materials)"""
    product_id: str = Field(..., description="Unique product ID")
    product_name: str = Field(..., description="Product name")
    product_code: Optional[str] = None
    
    formulation: List[ProductFormulation] = Field(..., description="Raw material composition")
    
    density_lbs_per_gal: Optional[float] = None
    ph: Optional[float] = None
    color: Optional[str] = None
    
    price_per_lb: Optional[float] = None
    price_per_gal: Optional[float] = None
    
    recommended_dosage_range_ppm: Optional[List[float]] = None
    application_type: Optional[str] = None
    
    access_level: AccessLevelEnum = AccessLevelEnum.COMPANY
    owner_company_id: Optional[str] = None
    owner_user_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: Literal["active", "discontinued", "pending"] = "active"
    notes: Optional[str] = None


# ========================================
# NEW SCHEMAS - ANALYSIS TYPES
# ========================================

class AnalysisTypeEnum(str, Enum):
    """Types of analyses"""
    SIMPLE_SATURATION = "simple_saturation"
    WHERE_CAN_I_TREAT_FIXED = "where_can_i_treat_fixed"
    WHERE_CAN_I_TREAT_AUTO = "where_can_i_treat_auto"
    COMPARE = "compare"
    STANDARD = "standard"


class OperatingConditionsSchema(BaseModel):
    """Operating conditions for analysis"""
    ph_range: Optional[List[float]] = Field(None, description="[min_pH, max_pH]")
    coc_range: Optional[List[float]] = Field(None, description="[min_CoC, max_CoC]")
    temp_range_c: Optional[List[float]] = Field(None, description="[min_temp, max_temp] in °C")
    
    ph_steps: int = Field(10, ge=2, le=50)
    coc_steps: int = Field(10, ge=2, le=50)
    temp_steps: int = Field(10, ge=2, le=50)


class ProductDosageSchema(BaseModel):
    """Product with dosage"""
    product_id: str
    dosage_ppm: float = Field(..., ge=0)


class SimpleSaturationRequest(BaseModel):
    """Request for Simple Saturation Model"""
    base_water_analysis: Dict[str, Any]
    operating_conditions: OperatingConditionsSchema
    salts_of_interest: Optional[List[str]] = None
    balance_cation: Literal["Na", "K"] = "Na"
    balance_anion: Literal["Cl", "SO4"] = "Cl"


class WhereCanITreatFixedRequest(BaseModel):
    """Request for Where Can I Treat (Fixed Dosage)"""
    base_water_analysis: Dict[str, Any]
    products: List[ProductDosageSchema]
    operating_conditions: OperatingConditionsSchema
    target_salts: List[str]


class WhereCanITreatAutoRequest(BaseModel):
    """Request for Where Can I Treat (Auto Dosage)"""
    base_water_analysis: Dict[str, Any]
    products: List[str]
    operating_conditions: OperatingConditionsSchema
    target_salts: List[str]
    optimization_target: Literal["minimize_cost", "maximize_coc", "balanced"] = "balanced"


class CompareAnalysesRequest(BaseModel):
    """Request to compare two analyses"""
    analysis1_id: str
    analysis2_id: str
    include_value_additions: bool = True


# ========================================
# NEW SCHEMAS - STANDALONE CALCULATIONS
# ========================================

class StandaloneCalculationResults(BaseModel):
    """Results from standalone calculations"""
    
    lsi: Optional[float] = None
    ryznar_index: Optional[float] = None
    puckorius_index: Optional[float] = None
    stiff_davis_index: Optional[float] = None
    
    larson_skold_index: Optional[float] = None
    
    mild_steel_corrosion_rate_mpy: Optional[float] = None
    copper_corrosion_rate_mpy: Optional[float] = None
    admiralty_brass_corrosion_rate_mpy: Optional[float] = None
    
    ccpp_mg_l: Optional[float] = None
    
    interpretations: Optional[Dict[str, str]] = None


class StandaloneCalculationRequest(BaseModel):
    """Request for standalone calculations (no PHREEQC)"""
    
    ph: float = Field(..., ge=0, le=14)
    temperature_c: float
    
    calcium_mg_l: Optional[float] = None
    magnesium_mg_l: Optional[float] = None
    sodium_mg_l: Optional[float] = None
    chloride_mg_l: Optional[float] = None
    sulfate_mg_l: Optional[float] = None
    bicarbonate_mg_l: Optional[float] = None
    carbonate_mg_l: Optional[float] = None
    alkalinity_mg_l: Optional[float] = None
    tds_mg_l: Optional[float] = None
    
    dissolved_oxygen_ppm: Optional[float] = None
    ammonia_ppm: Optional[float] = None
    free_chlorine_ppm: Optional[float] = None
    total_chlorine_ppm: Optional[float] = None
    
    pma_ppm: Optional[float] = 0.0
    tta_ppm: Optional[float] = 0.0
    bta_ppm: Optional[float] = 0.0
    mbt_ppm: Optional[float] = 0.0
    copper_free_ppm: Optional[float] = 0.0
    
    si_caco3: Optional[float] = None
    si_alsi: Optional[float] = None
    si_snsi: Optional[float] = None
    si_tcp: Optional[float] = None
    si_zp: Optional[float] = None
    
    calculate_lsi: bool = True
    calculate_ryznar: bool = True
    calculate_puckorius: bool = True
    calculate_stiff_davis: bool = True
    calculate_larson_skold: bool = True
    calculate_mild_steel_corrosion: bool = False
    calculate_copper_corrosion: bool = False
    calculate_admiralty_brass_corrosion: bool = False


# ========================================
# NEW SCHEMAS - 3D GRAPH DATA
# ========================================

class GraphPoint3D(BaseModel):
    """Single point in 3D graph"""
    x: float
    y: float
    z: float
    value: float


class Graph3DDataSchema(BaseModel):
    """3D graph data for visualization"""
    salt_name: str
    x_axis: Literal["pH", "CoC", "temp"]
    y_axis: Literal["pH", "CoC", "temp"]
    z_axis: Literal["pH", "CoC", "temp"]
    
    points: List[GraphPoint3D]
    
    x_range: List[float]
    y_range: List[float]
    z_range: List[float]
    
    value_range: List[float]
    
    total_points: int
    green_zone_count: Optional[int] = None
    yellow_zone_count: Optional[int] = None
    red_zone_count: Optional[int] = None


# ========================================
# NEW SCHEMAS - COOLING TOWER CALCULATIONS
# ========================================

class CoolingTowerRequest(BaseModel):
    """Request for cooling tower calculations"""
    
    recirculation_rate_gpm: Optional[float] = None
    evaporation_rate_gpm: Optional[float] = None
    blowdown_rate_gpm: Optional[float] = None
    makeup_rate_gpm: Optional[float] = None
    
    hot_water_temp_f: Optional[float] = None
    cold_water_temp_f: Optional[float] = None
    wet_bulb_temp_f: Optional[float] = None
    
    makeup_silica_mg_l: Optional[float] = None
    recirculating_silica_mg_l: Optional[float] = None
    
    drift_percent: float = Field(0.1, description="Drift as % of recirculation")
    evaporation_factor_percent: float = Field(85.0, description="Evaporation efficiency %")
    
    heat_load_btu_hr: Optional[float] = None
    cooling_tons: Optional[float] = None


class CoolingTowerResults(BaseModel):
    """Results from cooling tower calculations"""
    
    coc: Optional[float] = None
    evaporation_rate_gpm: Optional[float] = None
    evaporation_rate_gpd: Optional[float] = None
    blowdown_rate_gpm: Optional[float] = None
    blowdown_rate_gpd: Optional[float] = None
    makeup_rate_gpm: Optional[float] = None
    makeup_rate_gpd: Optional[float] = None
    
    range_f: Optional[float] = None
    approach_f: Optional[float] = None
    efficiency_percent: Optional[float] = None
    
    heat_load_btu_hr: Optional[float] = None
    heat_load_tons: Optional[float] = None
    
    interpretations: Optional[Dict[str, str]] = None


# ========================================
# UPDATED RESPONSE SCHEMAS
# ========================================

class AnalysisResponse(BaseModel):
    """Enhanced analysis response"""
    analysis_id: str
    analysis_type: AnalysisTypeEnum
    status: Literal["completed", "failed", "processing"]
    
    phreeqc_results: Optional[PHREEQCResult] = None
    standalone_calculations: Optional[StandaloneCalculationResults] = None
    cooling_tower_results: Optional[CoolingTowerResults] = None
    
    grid_info: Optional[Dict[str, Any]] = None
    total_points_calculated: Optional[int] = None
    
    created_at: datetime
    processing_time_seconds: Optional[float] = None
    warnings: Optional[List[str]] = None
    
    results_preview: Optional[List[Dict[str, Any]]] = None


# ========================================
# VALIDATORS
# ========================================

class CustomerCreateRequest(BaseModel):
    """Request to create new customer"""
    company_name: str
    industry: Optional[str] = None
    address: Optional[AddressSchema] = None
    primary_contact: Optional[ContactInfoSchema] = None
    notes: Optional[str] = None


class AssetCreateRequest(BaseModel):
    """Request to create new asset"""
    customer_id: str
    asset_name: str
    asset_type: Literal["cooling_tower", "chiller", "boiler", "closed_loop", "other"] = "cooling_tower"
    location: Optional[str] = None
    recirculation_rate_gpm: Optional[float] = None
    design_coc: Optional[float] = None
    notes: Optional[str] = None


class ProductCreateRequest(BaseModel):
    """Request to create new product"""
    product_name: str
    formulation: List[ProductFormulation]
    density_lbs_per_gal: Optional[float] = None
    price_per_lb: Optional[float] = None
    recommended_dosage_range_ppm: Optional[List[float]] = None
    access_level: AccessLevelEnum = AccessLevelEnum.COMPANY
    notes: Optional[str] = None
    
    @validator('formulation')
    def validate_formulation(cls, v):
        """Ensure formulation percentages sum to reasonable value"""
        total_percent = sum(item.active_percent for item in v)
        if total_percent > 100:
            raise ValueError(f"Total formulation exceeds 100% ({total_percent}%)")
        return v


class RawMaterialCreateRequest(BaseModel):
    """Request to create new raw material"""
    material_name: str
    cas_number: Optional[str] = None
    chemical_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    density_lbs_per_gal: Optional[float] = None
    active_percent: float = 100.0
    category: Optional[str] = None
    function: Optional[str] = None
    access_level: AccessLevelEnum = AccessLevelEnum.GLOBAL
    notes: Optional[str] = None