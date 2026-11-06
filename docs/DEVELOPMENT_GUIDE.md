# Development & Engineering Guide

**Project:** Conversational Image Recognition Chatbot  
**Organisation:** Bharat Electronics Limited (BEL)  

---

## 1. Prerequisites
- **macOS:** Apple Silicon (M1/M2/M3/M4) recommended with Metal Performance Shaders (MPS).
- **Python:** Python 3.11.x (via Homebrew: `brew install python@3.11`).
- **Node.js:** Node.js v20+ / v24+ with npm.
- **PostgreSQL:** PostgreSQL 16+ or 18+ (running locally on port 5432).

---

## 2. Environment Setup

### Backend (Python 3.11 Virtual Environment)
```bash
# Create isolated environment using Python 3.11
/opt/homebrew/opt/python@3.11/bin/python3 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

### PostgreSQL Database
```bash
# Verify PostgreSQL is running
brew services list

# Create the application database
createdb bel_chatbot_db
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
```

---

## 3. Running the Application Locally

### Running Backend:
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs are accessible at: `http://127.0.0.1:8000/docs`

### Running Frontend:
```bash
cd frontend
npm run dev
```
Frontend interface is accessible at: `http://localhost:5173`

---

## 4. Hardware Verification & Model Benchmarking
Run the benchmarking script to verify Apple MPS throughput:
```bash
source .venv/bin/activate
python scripts/benchmark_hardware.py
```

---

## 5. Git Commit Protocol
Commit messages must adhere strictly to the 35-commit milestone roadmap outlined in `AGENTS.md`. Never commit credentials, `.env` files, or binary model weights directly.
