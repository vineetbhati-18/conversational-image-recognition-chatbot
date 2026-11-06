# Conversational Image Recognition Chatbot
**Developed for Bharat Electronics Limited (BEL)**

A full-stack, enterprise-grade conversational AI application capable of recognizing objects in uploaded images, answering complex natural language queries, maintaining conversational context across multiple dialogue turns, and displaying interactive bounding boxes with confidence scores.

---

## Key Features

- **Real Deep Learning Object Detection:** Powered by Ultralytics YOLOv8 running on local hardware (Apple Silicon MPS / CUDA / CPU) with real-time bounding box annotations.
- **Visual Question Answering (VQA):** Integrated Salesforce BLIP multi-modal transformer for visual comprehension.
- **Context-Aware Dialogue Memory:** Context Fusion Engine retains multi-turn conversational history combined with spatial object telemetry.
- **Interactive Image Canvas:** Visualizes detected bounding boxes, confidence tags, and provides class-filtering capabilities.
- **Enterprise Security & Privacy:** 100% local model execution without dependence on external, paid cloud APIs. Secure image storage and validation.
- **PostgreSQL Persistence:** Complete history tracking for sessions, messages, images, and detection telemetry.

---

## Technology Stack

- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, HTML5 Canvas.
- **Backend:** Python 3.11, FastAPI, Uvicorn (ASGI), Pydantic v2.
- **AI/ML:** PyTorch (with Apple MPS Metal acceleration), Ultralytics YOLOv8, HuggingFace Transformers (BLIP).
- **Database:** PostgreSQL with async SQLAlchemy 2.0 & Alembic.

---

## Quick Start

### 1. Backend Setup
```bash
# Set up Python 3.11 virtual environment
/opt/homebrew/opt/python@3.11/bin/python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Start backend server
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access the chat application and `http://localhost:8000/docs` for the interactive API documentation.

---

## Documentation
- [System Architecture](docs/ARCHITECTURE.md)
- [API Specification](docs/API_SPECIFICATION.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)
- [Agents & Milestones Specification](AGENTS.md)
