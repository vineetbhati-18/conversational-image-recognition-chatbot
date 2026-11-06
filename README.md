# Conversational Image Recognition Chatbot
**Autonomous AI Project Developed for Bharat Electronics Limited (BEL)**

[![Continuous Integration](https://github.com/vineetbhati-18/conversational-image-recognition-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/vineetbhati-18/conversational-image-recognition-chatbot/actions)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch MPS](https://img.shields.io/badge/PyTorch-2.2.0%20(Apple%20MPS)-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00ffff.svg)](https://ultralytics.com)
[![React Vite](https://img.shields.io/badge/React%2018-Vite%205-61DAFB.svg?logo=react&logoColor=black)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2F%2018-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org)

An enterprise-grade, multi-modal conversational AI reconnaissance system designed to recognize tactical and civilian objects in uploaded imagery, answer complex visual questions in natural language, retain conversational memory across multi-turn dialogues, and visualize detections via an interactive HTML5 canvas with real-time bounding boxes and confidence telemetry.

---

## Table of Contents
1. [Core Capabilities & Requirements](#core-capabilities--requirements)
2. [System Architecture](#system-architecture)
3. [AI/ML Models & Hardware Acceleration](#aiml-models--hardware-acceleration)
4. [Technology Stack](#technology-stack)
5. [Installation & Setup](#installation--setup)
   - [Option A: Local Development Setup](#option-a-local-development-setup)
   - [Option B: Containerized Docker Deployment](#option-b-containerized-docker-deployment)
6. [API Specification](#api-specification)
7. [Database Schema & Migrations](#database-schema--migrations)
8. [Multi-Turn Dialogue & Context Fusion](#multi-turn-dialogue--context-fusion)
9. [Verification & Testing](#verification--testing)
10. [Security, Privacy & Licensing](#security-privacy--licensing)

---

## Core Capabilities & Requirements

| Requirement | Implementation Details | Status |
| :--- | :--- | :---: |
| **Image Upload & Validation** | Magic byte binary inspection (JPEG, PNG, WebP), up to 15 MB payload validation | Verified |
| **Object Detection** | Real Ultralytics YOLOv8s deep-learning model with Apple Silicon MPS Metal acceleration | Verified |
| **Bounding Boxes & Canvas** | HTML5 Canvas with dynamic responsive scaling, confidence tags, and class filtering | Verified |
| **Vision-Language Understanding** | Salesforce BLIP VQA (`Salesforce/blip-vqa-base`) multi-modal transformer | Verified |
| **Multi-Turn Context Retention** | Sliding window context manager with coreference & pronoun resolution | Verified |
| **Multi-Modal Fusion** | Rule & spatial telemetry fusion engine synthesizing YOLO sectors and BLIP answers | Verified |
| **Database Persistence** | PostgreSQL persistence for sessions, images, messages, and detected objects via Alembic | Verified |
| **Edge & Air-Gapped Privacy** | 100% local model execution; zero external cloud API dependencies | Verified |

---

## System Architecture

```mermaid
flowchart TD
    User["Operator / Analyst"] -->|Uploads Image / Queries| WebUI["React 18 + Vite UI (Tailwind CSS)"]
    WebUI -->|Canvas Render / Telemetry| HTML5Canvas["HTML5 Canvas (Bounding Boxes)"]
    WebUI -->|REST / Multipart HTTP| FastAPI["FastAPI Backend (Uvicorn ASGI)"]
    
    FastAPI --> SessionMgr["Session & Context Manager"]
    FastAPI --> ImageProc["Image Processing & Magic Byte Validation"]
    
    ImageProc -->|Local Disk| Storage["Local Image Storage (/uploads)"]
    ImageProc -->|Tensor Feed| YOLO["YOLOv8s Detector (Apple MPS / Metal)"]
    
    SessionMgr -->|Spatial Telemetry + History| FusionEngine["Multi-Modal Fusion Engine"]
    FusionEngine -->|Prompt + Visual Tensor| BLIP["Salesforce BLIP VQA Base"]
    
    FastAPI --> RepoLayer["Repository Pattern Layer"]
    RepoLayer -->|AsyncPG Pool| Postgres[("PostgreSQL 16/18 Database")]
```

---

## AI/ML Models & Hardware Acceleration

### 1. Ultralytics YOLOv8s (Object Detection)
- **Model Checkpoint:** `yolov8s.pt` (Small variant, optimal speed/accuracy trade-off).
- **Execution Target:** Apple Silicon MPS (`torch.device("mps")`) with automatic fallback to CPU.
- **Inference Latency:** $\approx 45.34\text{ ms}$ on Apple M4 Unified Memory.
- **Output:** 80 COCO classes with normalized bounding boxes $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$, confidence scores ($0.0 - 1.0$), and spatial quadrant assignments (`top-left`, `center`, etc.).

### 2. Salesforce BLIP VQA Base (Visual Question Answering)
- **Model Checkpoint:** `Salesforce/blip-vqa-base` via HuggingFace Transformers.
- **Architecture:** Vision Transformer (ViT) image encoder combined with a BERT-based text decoder with cross-attention.
- **Execution Target:** Apple Silicon MPS / CPU with PyTorch 2.2+.

### 3. Apple M4 Unified Memory Benchmark
Benchmarked locally on Apple M4 (10 cores, 16 GB Unified Memory):
- **MPS Device Latency:** $45.34\text{ ms}$ (vs. CPU $81.70\text{ ms}$ — **$1.8\times$ speedup**).
- **Zero-Copy Memory:** CPU and GPU share the unified memory pool, eliminating PCI-e bus transfer overheads.

---

## Technology Stack

- **Frontend:** React 18, Vite 5, Tailwind CSS, Lucide Icons, HTML5 Canvas API.
- **Backend Framework:** Python 3.11, FastAPI 0.111, Uvicorn, Pydantic v2.
- **AI & Deep Learning:** PyTorch 2.2, Ultralytics YOLOv8, HuggingFace Transformers, PIL (Pillow).
- **Database & ORM:** PostgreSQL 16/18, SQLAlchemy 2.0 (Asyncio), Asyncpg, Alembic migrations.
- **Containerization & CI:** Docker, Docker Compose, Nginx Alpine, GitHub Actions.

---

## Installation & Setup

### Option A: Local Development Setup

#### Prerequisites
- macOS, Linux, or Windows with WSL2
- Python 3.11 (`python3.11 --version`)
- Node.js 20+ and npm (`node --version`)
- PostgreSQL 16+ running locally (`psql -h localhost -U postgres`)

#### 1. Clone Repository
```bash
git clone https://github.com/vineetbhati-18/conversational-image-recognition-chatbot.git
cd conversational-image-recognition-chatbot
```

#### 2. Backend Configuration
```bash
# Create isolated Python 3.11 virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env if your PostgreSQL credentials differ from default:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bel_chatbot_db

# Run database migrations
cd backend
alembic upgrade head
cd ..

# Start FastAPI development server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend API interactive documentation is available at `http://localhost:8000/docs`.

#### 3. Frontend Setup
```bash
# In a separate terminal:
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

### Option B: Containerized Docker Deployment

To launch the complete multi-container stack (PostgreSQL + FastAPI Backend + Nginx Frontend):

```bash
docker-compose up --build
```
- **Web Interface:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **API Swagger Docs:** `http://localhost:8000/docs`

---

## API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health check (PostgreSQL status, MPS device, YOLO/BLIP ready) |
| `POST` | `/api/v1/sessions` | Create a new conversation session |
| `GET` | `/api/v1/sessions` | List all conversation sessions |
| `GET` | `/api/v1/sessions/{id}` | Retrieve session detail with messages, images, and detected objects |
| `DELETE` | `/api/v1/sessions/{id}` | Delete session and cascade associated artifacts |
| `POST` | `/api/v1/images/upload` | Upload image binary, validate magic bytes, and run YOLOv8 detection |
| `POST` | `/api/v1/images/{id}/detect`| Re-run detection on an existing image with a modified confidence slider |
| `GET` | `/api/v1/images/{id}/file` | Stream raw image binary |
| `POST` | `/api/v1/chat/message` | Submit user question; executes multi-turn VQA fusion engine |

---

## Database Schema & Migrations

Database schema managed through **Alembic**:
```
sessions
  ├── id: UUID (PK)
  ├── title: VARCHAR(255)
  ├── created_at: TIMESTAMPTZ
  └── updated_at: TIMESTAMPTZ

images
  ├── id: UUID (PK)
  ├── session_id: UUID (FK -> sessions.id, ON DELETE CASCADE)
  ├── filename: VARCHAR(255)
  ├── storage_path: VARCHAR(512)
  ├── mime_type: VARCHAR(64)
  ├── file_size_bytes: INTEGER
  ├── width: INTEGER
  ├── height: INTEGER
  └── created_at: TIMESTAMPTZ

detected_objects
  ├── id: UUID (PK)
  ├── image_id: UUID (FK -> images.id, ON DELETE CASCADE)
  ├── class_name: VARCHAR(100)
  ├── confidence_score: FLOAT
  ├── bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max: FLOAT
  └── created_at: TIMESTAMPTZ

messages
  ├── id: UUID (PK)
  ├── session_id: UUID (FK -> sessions.id, ON DELETE CASCADE)
  ├── image_id: UUID (FK -> images.id, ON DELETE SET NULL)
  ├── sender_type: VARCHAR(20) ('user', 'assistant', 'system')
  ├── content: TEXT
  ├── metadata: JSONB
  └── created_at: TIMESTAMPTZ
```

---

## Multi-Turn Dialogue & Context Fusion

The chatbot handles natural language conversation through a specialized three-tier pipeline:
1. **Dialogue History Sliding Window:** Maintains recent conversational turns to preserve conversational context.
2. **Coreference Resolution:** Automatically rewrites ambiguous pronouns ("it", "they", "that vehicle") using antecedent nouns identified in previous conversational turns.
3. **Multi-Modal Fusion Engine:**
   - **Counting Queries:** Directly evaluates YOLO detections (e.g., *"How many cars are visible?"* -> *"I detected 3 car(s) in the image."*).
   - **Spatial Queries:** Uses bounding box sector coordinates (e.g., *"Where is the truck?"* -> *"The truck is located in the center-left quadrant of the image with 94.2% confidence."*).
   - **Visual Attributes / Questions:** Dispatches the query and image tensor to Salesforce BLIP VQA to answer questions regarding colors, actions, text, or environmental features.

---

## Verification & Testing

### Running Backend Test Suite
```bash
source .venv/bin/activate
pytest backend/tests/ -v
```
**Test Coverage:**
- `test_health.py`: Healthcheck and root endpoints
- `test_schemas.py`: Pydantic model serialization and validation
- `test_yolo_service.py` & `test_yolo_inference.py`: YOLO deep-learning inference pipeline and Apple MPS acceleration
- `test_yolo_regression.py`: Aspect ratio handling, confidence threshold filtering, and COCO classes
- `test_blip_service.py`: BLIP VQA initialization and singleton lifecycle
- `test_context_manager.py`: Sliding window dialogue history and coreference resolution
- `test_fusion_engine.py`: Multi-modal count, spatial, and attribute queries
- `test_repositories.py`: PostgreSQL repository CRUD lifecycle
- `test_e2e_integration.py`: End-to-end multi-modal pipeline with image upload, YOLO detection, multi-turn chat, and session retrieval

### Building & Verifying Frontend
```bash
cd frontend
npm run build
```

---

## Security, Privacy & Licensing

- **Air-Gapped & Offline Ready:** All inference models run entirely locally without requiring internet connectivity or sending sensitive defense/operational imagery to external cloud providers.
- **Ultralytics YOLOv8 Licensing:** AGPL-3.0 open-source licensing.
- **Salesforce BLIP Licensing:** BSD-3-Clause open-source licensing.
- **No Hardcoded Secrets:** Strict environment variable isolation using `.env` files; secrets excluded via `.gitignore`.
- **Magic Byte Validation:** Image upload endpoint verifies raw file headers to prevent malicious file uploads.

---

## Authors & Acknowledgments

- **Organization:** Bharat Electronics Limited (BEL)
- **Project:** Conversational Image Recognition Chatbot
- **Repository:** [https://github.com/vineetbhati-18/conversational-image-recognition-chatbot](https://github.com/vineetbhati-18/conversational-image-recognition-chatbot)
