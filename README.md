# 🚁 Cargo-Aware Drone Selection DSS

> **Intelligent Decision Support System for Port Drone Operations**
>
> Group 6 — BTH University Project

A web-based Decision Support System (DSS) that helps port operators select the most suitable drone for cargo inspection, surveillance, and monitoring missions. The system applies rule-based filtering, weighted multi-criteria scoring, and provides transparent recommendations with full audit logging.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the Project](#-running-the-project)
- [Usage Guide](#-usage-guide)
- [API Documentation](#-api-documentation)
- [Sample Data](#-sample-data)
- [Decision Engine](#-decision-engine)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Rule-Based Filtering** | 10 hard filter rules (R-01 to R-10) automatically reject unsafe or infeasible drones |
| **Weighted Scoring** | 19 configurable criteria across 5 categories rank suitable drones |
| **Recommendation Display** | Top drone highlighted with score breakdown and explanation |
| **Operator Override** | Operators can override recommendations with a mandatory reason |
| **Safety Alerts** | Automatic warnings when wind, visibility, or battery thresholds are exceeded |
| **Decision Logging** | Full audit trail of every decision, score, rejection, and override |
| **Fleet Management** | Add, edit, and view drone records with status tracking |
| **Mission Management** | Create missions, assign drones, and track mission status |
| **Configurable Weights** | Administrators can adjust criterion weights from the Settings page |
| **Role Selection** | Simple role-based access: Operator, Supervisor, Maintenance, Admin |

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend API** | Python 3.10+, FastAPI | REST API, decision engine, data processing |
| **Database** | SQLite + SQLAlchemy ORM | Persistent storage for all data |
| **Data Processing** | Pandas, NumPy | Normalisation, scoring calculations |
| **Frontend UI** | Streamlit (multi-page) | Dashboard and all user-facing pages |
| **Charts** | Plotly | Score breakdown visualisations |

---

## 📁 Project Structure

```
dss-project/
│
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── database.py              # SQLAlchemy engine & session config
│   ├── models.py                # ORM models (Drone, Mission, CargoZone, etc.)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── seed_data.py             # Seed data (25 drones, 12 cargo zones, etc.)
│   ├── decision_engine.py       # Hard filters + weighted scoring logic
│   └── routers/
│       ├── __init__.py
│       ├── drones.py            # GET/POST/PUT /drones
│       ├── missions.py          # GET/POST/PUT /missions
│       ├── cargo_zones.py       # GET/POST /cargo-zones
│       ├── environment.py       # GET/POST /environment
│       ├── decisions.py         # POST /decisions/evaluate, /confirm, /override
│       └── settings.py          # GET/PUT /settings/weights
│
├── frontend/
│   ├── app.py                   # Streamlit home page with theme & navigation
│   └── pages/
│       ├── 1_Dashboard.py       # Fleet metrics, alerts, recent decisions
│       ├── 2_Drone_Inventory.py # View, filter, add, edit drones
│       ├── 3_Create_Mission.py  # Mission creation form → triggers evaluation
│       ├── 4_Recommendation.py  # Best drone card, score chart, confirm/override
│       ├── 5_Mission_Schedule.py# Mission timeline with status badges
│       ├── 6_Alerts.py          # Safety alerts with severity filtering
│       ├── 7_Decision_Logs.py   # Searchable audit trail with detail view
│       └── 8_Settings.py        # Adjustable criterion weights
│
├── requirements.txt             # Python dependencies
├── .gitignore
├── DSS_PRD_Cargo_Drone_Selection.pdf  # Product Requirements Document
└── README.md
```

---

## 📦 Prerequisites

- **Python 3.10 or higher** — [Download Python](https://www.python.org/downloads/)
- **pip** — Python package manager (comes with Python)
- **Git** — [Download Git](https://git-scm.com/downloads)

To verify your Python version:
```bash
python3 --version
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/siddharth250305/dss-project.git
cd dss-project
```

### 2. (Optional) Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: FastAPI, Uvicorn, SQLAlchemy, Pandas, NumPy, Streamlit, Plotly, and Requests.

---

## ▶️ Running the Project

You need **two terminals** running simultaneously — one for the backend and one for the frontend.

### Terminal 1 — Start the Backend (FastAPI)

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
✅  Seed data loaded successfully.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

> On first run, the database (`drone_dss.db`) is created automatically and seeded with sample data.

### Terminal 2 — Start the Frontend (Streamlit)

```bash
cd frontend
python3 -m streamlit run app.py --server.port 8501
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### 4. Open in Browser

| Service | URL |
|---|---|
| **Frontend (Streamlit UI)** | http://localhost:8501 |
| **Backend API** | http://localhost:8000 |
| **API Documentation (Swagger)** | http://localhost:8000/docs |
| **API Documentation (ReDoc)** | http://localhost:8000/redoc |

> ⚠️ **Important:** Start the backend FIRST — the Streamlit frontend makes HTTP calls to the FastAPI backend.

---

## 📖 Usage Guide

### Step-by-Step Workflow

1. **Select your role** from the sidebar dropdown (Operator, Supervisor, Maintenance, Admin)

2. **Dashboard** — View fleet status, recent alerts, and recent decisions at a glance

3. **Drone Inventory** — Browse the fleet, filter by status/sensors, add new drones, or edit existing records

4. **Create Mission** — Fill in mission parameters:
   - Mission type (Inspection, Surveillance, Monitoring, Emergency)
   - Urgency level
   - Cargo zone (auto-fills distance)
   - Required flight height
   - Sensor requirements (night vision, thermal)
   - Weather conditions (manual input)
   - Click **"Evaluate Drones"** to trigger the decision engine

5. **Recommendation** — Review the DSS result:
   - 🏆 Recommended drone with total score
   - 📊 Score breakdown chart (per criterion)
   - 📋 Ranked list of all suitable drones
   - ❌ Rejected drones with specific reasons
   - 🚨 Safety alerts
   - ✅ **Confirm** the recommendation or 🔄 **Override** with a different drone (reason required)

6. **Mission Schedule** — View all missions with status badges (Draft → Scheduled → Active → Completed)

7. **Alerts** — Review all safety warnings filtered by severity (Info, Warning, Critical)

8. **Decision Logs** — Search and expand past decisions to see full details including score breakdowns, rejections, and override reasons

9. **Settings** — Adjust the weight of each scoring criterion (must sum to 100%) to reflect current operational priorities

---

## 🔌 API Documentation

Once the backend is running, interactive API documentation is available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/drones/` | List all drones |
| `POST` | `/drones/` | Add a new drone |
| `PUT` | `/drones/{drone_id}` | Update a drone |
| `GET` | `/missions/` | List all missions |
| `POST` | `/missions/` | Create a new mission |
| `GET` | `/cargo-zones/` | List all cargo zones |
| `POST` | `/decisions/evaluate` | Run the decision engine for a mission |
| `POST` | `/decisions/confirm` | Confirm a recommendation |
| `POST` | `/decisions/override` | Override with a different drone |
| `GET` | `/decisions/logs` | Get all decision logs |
| `GET` | `/decisions/alerts` | Get all safety alerts |
| `GET` | `/settings/weights` | Get criterion weights |
| `PUT` | `/settings/weights` | Update criterion weights |

---

## 📊 Sample Data

The system is pre-loaded with realistic simulated data:

- **25 drones** with varied capabilities (SkyHawk X1, CargoEye 500, TitanCargo X5, etc.)
- **12 cargo zones** (Container Terminal, Hazardous Materials Zone, Oil & Gas Terminal, etc.)
- **19 decision criteria** with default weights matching the PRD
- **4 user accounts** (operator1, supervisor1, maintenance1, admin1)

---

## 🧠 Decision Engine

### Phase 1: Hard Filtering (10 Rules)

| Rule | Condition | Rejection |
|---|---|---|
| R-01 | Battery endurance < required flight time × 1.2 | Insufficient battery |
| R-02 | Wind speed > drone wind resistance | Wind too high |
| R-03 | Night vision required but unavailable | Missing sensor |
| R-04 | Thermal sensor required but unavailable | Missing sensor |
| R-05 | Maintenance status = Poor or Grounded | Not cleared |
| R-06 | Zone distance > drone flight radius | Out of range |
| R-07 | Safety risk = Critical (no approval) | Needs supervisor |
| R-08 | Regulatory compliance = False | Not compliant |
| R-09 | No operator available | No supervision |
| R-10 | Weather = Storm or Heavy Rain | Unsafe weather |

### Phase 2: Weighted Scoring (19 Criteria)

| Category | Criteria | Weight |
|---|---|---|
| **Capability** (52%) | Flight Radius, Battery, Payload, Camera, Night Vision, Thermal, Height, Wind Resistance, Charging Time | 8%, 11%, 6%, 5%, 4%, 4%, 4%, 8%, 2% |
| **Mission** (20%) | Urgency, Zone Distance, Reliability | 8%, 6%, 6% |
| **Environmental** (15%) | Weather, Wind Speed, Obstacles | 5%, 7%, 3% |
| **Safety** (10%) | Risk Level, Regulatory | 6%, 4% |
| **Operational** (3%) | Daily Missions, Budget | 2%, 1% |

**Formula:** `Total Score = Σ (Criterion Weight × Normalised Score)` → Range: 0.0 to 1.0

---

## 🛑 Troubleshooting

| Issue | Solution |
|---|---|
| `Cannot connect to backend API` | Make sure the FastAPI server is running on port 8000 |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Port already in use` | Kill the process: `lsof -ti:8000 \| xargs kill` |
| Database issues | Delete `backend/drone_dss.db` and restart — it will be recreated with seed data |

---

## 📄 License

This is a university project developed for the DSS course at BTH (Blekinge Institute of Technology).

---

> **Group 6 — BTH University Project** | Cargo-Aware Drone Selection DSS
