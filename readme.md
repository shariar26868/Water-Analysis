# 💧 Water Quality Analysis System

Enterprise-grade cooling-tower water-quality analysis platform powered by **PHREEQC** and **GPT-4o Vision**.

---

## 🏗️ Architecture Overview

```
┌─────────────┐      ┌──────────────────┐      ┌───────────┐
│  Frontend   │─────▶│   FastAPI Backend │─────▶│  MongoDB  │
│ (Plotly.js) │◀─────│                  │      │           │
└─────────────┘      │  ┌────────────┐  │      └───────────┘
                     │  │  PHREEQC   │  │
                     │  │ (subprocess)│  │
                     │  └────────────┘  │
                     └──────────────────┘
```

### Request Flow

```
PDF / Image
    │
    ▼
OCR Service (GPT-4o)          ← extracts ion concentrations
    │
    ▼
Ion Balancing                  ← iterative Na/K or Cl/SO4 adjustment
    │
    ▼
DB Selection                   ← IS ≤ 0.5 → phreeqc.dat | IS > 0.5 → pitzer.dat
    │
    ▼
PHREEQC Engine                 ← single-point OR SOLUTION_SPREAD batch
    │
    ▼
Standalone Calculations        ← LSI, Ryznar, Puckorius, Corrosion Rates …
    │
    ▼
Graph Service                  ← 2D bar chart | 3D surface | multi-salt heatmap
    │
    ▼
MongoDB Storage                ← analysis results, customers, products …
```

---

## 📁 Project Structure

```
water_quality_backend/
├── main.py                              # FastAPI app factory, router mount
│
├── app/
│   ├── models/
│   │   └── schemas.py                   # All Pydantic models
│   │
│   ├── services/
│   │   ├── ocr_service.py               # GPT-4o Vision PDF/image OCR
│   │   ├── phreeqc_service.py           # PHREEQC wrapper + ion balance + batch
│   │   ├── graph_service.py             # 2D bars, 3D surface, heatmaps
│   │   ├── standalone_calculations.py   # LSI, Ryznar, Corrosion Rates …
│   │   ├── cooling_tower_service.py     # CoC, Evaporation, Blowdown …
│   │   ├── chemical_dosage_service.py   # PPM, lbs/day, annual cost …
│   │   ├── analysis_engine.py           # Orchestrator (Simple Sat, WCIT, Compare)
│   │   ├── grid_calculator.py           # 3D grid gen + water concentration
│   │   ├── customer_service.py          # Customer / Asset CRUD
│   │   ├── product_service.py           # Raw Material / Product CRUD
│   │   ├── compliance_service.py        # Compliance checks
│   │   ├── biological_service.py        # Biological risk
│   │   ├── composition_service.py       # Water composition
│   │   ├── quality_report_service.py    # Report generation
│   │   ├── report_history_service.py    # Historical reports
│   │   ├── scoring_service.py           # Water scoring
│   │   └── risk_analysis_service.py     # Risk analysis
│   │
│   ├── controllers/
│   │   ├── water_routes.py              # Core endpoints + standalone + 3D graph
│   │   ├── analysis_routes.py           # Simple Saturation, WCIT, Compare
│   │   ├── customer_routes.py           # Customer / Asset REST (backend dev)
│   │   └── product_routes.py            # Raw Material / Product REST (backend dev)
│   │
│   ├── db/
│   │   └── mongo.py                     # Motor async driver + all CRUD helpers
│   │
│   └── utils/
│       ├── unit_converter.py            # °C↔°F, mg/L↔ppm↔meq/L, GPM↔m³/h …
│       └── salt_data_table.py           # Green / Yellow / Red SI thresholds
│
├── requirements.txt
├── .env                                 # secrets (MONGO_URL, OPENAI_KEY, PHREEQC_PATH …)
├── Dockerfile
└── docker-compose.yml
```

---

## 🔧 Setup & Run

### 1. Environment Variables (`.env`)

```env
# MongoDB
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=water_quality_db

# OpenAI (GPT-4o Vision)
OPENAI_API_KEY=sk-…

# PHREEQC
PHREEQC_PATH=./phreeqc/phreeqc.exe        # Windows
# PHREEQC_PATH=/usr/local/bin/phreeqc     # Linux
PHREEQC_DAT_PATH=./phreeqc/phreeqc.dat
PITZER_DAT_PATH=./phreeqc/pitzer.dat
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Server

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production (Docker)
docker-compose up -d
```

### 4. Verify

```bash
curl http://localhost:8000/docs   # Swagger UI
```

---

## 📡 API Endpoints

### Core Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/extract` | OCR → extract parameters from PDF/image |
| POST | `/analyze` | Single-point PHREEQC analysis |

### Standalone Calculations (no PHREEQC)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/calculations/standalone` | LSI, Ryznar, Puckorius, Stiff & Davis, Larson-Skold, Corrosion Rates |
| POST | `/calculations/cooling-tower` | CoC, Evaporation, Blowdown, Makeup, Heat Load, DO |
| POST | `/calculations/chemical-dosage` | PPM, lbs/day, annual cost, active components |

### Grid / 3D Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analysis/simple-saturation` | 3D grid (pH × CoC × Temp) full SI map |
| POST | `/analysis/where-can-i-treat-fixed` | Fixed-dosage treatment zones (green/yellow/red) |
| POST | `/analysis/where-can-i-treat-auto` | Auto-dosage *(coming soon)* |
| POST | `/analysis/compare` | Side-by-side comparison of 2 analyses |
| GET | `/analysis/{id}` | Fetch stored analysis |
| GET | `/analysis/{id}/3d-graph` | 3D graph data (`?format=json` or `png`) |
| GET | `/analysis/history` | List past analyses |

### Customer & Product (backend dev – no AI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/customers` | Create customer |
| GET | `/customers/{id}` | Get customer |
| PUT | `/customers/{id}` | Update customer |
| DELETE | `/customers/{id}` | Full GDPR delete |
| POST | `/customers/{id}/assets` | Add asset |
| GET | `/customers/{id}/assets` | List assets |
| POST | `/raw-materials` | Create raw material |
| GET | `/raw-materials` | List (access-controlled) |
| POST | `/products` | Create product |
| GET | `/products` | List products |

---

## 🧮 Calculation Reference

### Standalone Indices

| Index | Formula |
|-------|---------|
| **LSI** | `pH_actual − pH_s` |
| **Ryznar** | `2 × pH_s − pH_actual` |
| **Puckorius (PSI)** | `2 × pHs − pHeq` |
| **Stiff & Davis** | `pH − pCa − pAlk − K` |
| **Larson-Skold** | `([Cl⁻]+[SO₄²⁻]) / ([HCO₃⁻]+[CO₃²⁻])` (meq/L) |

### Corrosion Rate Estimation

| Metal | Base Coefficient | Key Inhibitors |
|-------|-----------------|----------------|
| Mild Steel | 0.1 | PMA, Phosphates, Silicates |
| Copper | 0.05 | TTA, BTA, MBT (azoles) |
| Admiralty Brass | 0.08 | TTA, BTA, MBT + NH₃ factor |

### Cooling Tower

| Parameter | Formula |
|-----------|---------|
| CoC | `Conc_Ion / Base_Ion` |
| Evaporation | `0.01 × Recirc × (ΔT/10) × EvapFactor` |
| Blowdown | `Evap / (CoC − 1)` |
| Makeup | `Evap + BD + Drift` |
| Efficiency | `Range / (Range + Approach) × 100` |

---

## 🎨 3D Graph Rendering

Two modes available via `?format=` query parameter:

| Mode | How | Use |
|------|-----|-----|
| `json` | Backend returns `{x, y, z, color_zones}` | Frontend renders with **Plotly.js** (interactive) |
| `png` | Backend renders with **matplotlib 3D** | Embed directly as `<img>` (static) |

**Recommendation:** use `json` mode for the main UI (interactive zoom/rotate). Use `png` for PDF reports or emails.

---

## 🗄️ MongoDB Collections

| Collection | Purpose |
|------------|---------|
| `water_analyses` | Legacy single-point results |
| `analysis_results` | 3D grid / WCIT / compare results |
| `customers` | Customer records |
| `assets` | Cooling-tower assets (linked to customer) |
| `raw_materials` | Chemical raw materials |
| `products` | Blended products (formulations) |
| `phreeqc_config` | PHREEQC runtime config |

---

## 📋 Implementation Phases

| Phase | Week | Deliverable |
|-------|------|-------------|
| **1 – Foundation** | 1-2 | Customer/Asset/Product management |
| **2 – Calculations** | 3-4 | Standalone + Cooling Tower + Ion Balance |
| **3 – Analysis Engine** | 5-6 | Simple Saturation, Where Can I Treat |
| **4 – Visualisation** | 7-8 | 3D graphs, Comparison, Polish |

---

## ⚠️ Notes

- **Windows PHREEQC:** `--version` check is skipped on Windows to avoid subprocess timeout.
- **Ion Balancing:** max 2 iterations; throws if charge-balance error > 5 %.
- **Database auto-select:** Ionic-strength calculated at grid corners; entire run uses one DB file.
- **GDPR:** `DELETE /customers/{id}` hard-deletes customer + all linked assets and analyses.
- **Access Control:** Raw materials & products support `global | company | user` visibility (auth layer TBD).