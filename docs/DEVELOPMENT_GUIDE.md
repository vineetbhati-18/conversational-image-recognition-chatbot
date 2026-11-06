# Development Guide
**Project:** Conversational Image Recognition Chatbot  
**Organization:** Bharat Electronics Limited (BEL)

---

## 1. Development Environment

- **Operating System:** macOS (Apple Silicon M-series optimized) / Linux / Windows WSL2
- **Python Version:** 3.11 (`.venv`)
- **Node.js Version:** v20+ / v24+
- **Database:** PostgreSQL 16+ or 18+ on `localhost:5432`

---

## 2. Directory Structure Overview

```
conversational-image-recognition-chatbot/
├── .github/
│   └── workflows/
│       └── ci.yml               # Automated CI pipeline
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/v1/              # REST Endpoints (health, sessions, images, chat)
│   │   ├── core/                # Database engine, base models, exceptions, middleware
│   │   ├── models/              # SQLAlchemy declarative models
│   │   ├── repositories/        # Repository persistence layer
│   │   ├── schemas/             # Pydantic v2 data transfer objects
│   │   ├── services/            # YOLOv8, BLIP VQA, Context Fusion, Image processing
│   │   ├── utils/               # Structured logging
│   │   ├── config.py            # Pydantic BaseSettings
│   │   └── main.py              # FastAPI application factory
│   ├── tests/                   # Pytest automated test suite (31 tests)
│   ├── Dockerfile               # Backend container definition
│   └── requirements.txt         # Production dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/            # ChatContainer, MessageList, MessageInput
│   │   │   ├── common/          # Header, DashboardLayout, ErrorBoundary, Toast
│   │   │   ├── image/           # ImageCanvasViewer, ImageUploader, ObjectDetectionList
│   │   │   └── session/         # SessionSidebar, SessionItem
│   │   ├── context/             # ThemeContext, ChatContext
│   │   ├── services/            # Axios API client
│   │   ├── utils/               # HTML5 canvas bounding box helpers
│   │   ├── App.jsx              # Main App entrypoint
│   │   └── main.jsx
│   ├── Dockerfile               # Frontend multi-stage container
│   ├── nginx.conf               # Production Nginx reverse proxy
│   └── package.json
├── docs/                        # Specifications and architectural blueprints
├── docker-compose.yml           # Multi-container orchestration
└── README.md                    # System documentation
```

---

## 3. Running Backend Locally

```bash
# Activate isolated Python 3.11 virtual environment
source .venv/bin/activate

# Execute migrations
cd backend
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

---

## 4. Running Frontend Locally

```bash
cd frontend
npm run dev
```

---

## 5. Running Automated Tests

```bash
# Run complete backend test suite (31 tests)
source .venv/bin/activate
pytest backend/tests/ -v

# Run single test module
pytest backend/tests/test_e2e_integration.py -v

# Build frontend production bundle
cd frontend
npm run build
```
