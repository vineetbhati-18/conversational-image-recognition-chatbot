# System Architecture & Technical Specifications

**Project:** Conversational Image Recognition Chatbot  
**Organisation:** Bharat Electronics Limited (BEL)  
**System Target:** Apple Silicon M4 / Linux Production  

---

## 1. High-Level System Overview

The Conversational Image Recognition Chatbot is a secure, multi-modal AI application designed to run with real deep-learning models. It combines localized computer vision (bounding box object detection) with visual question answering (VQA) and multi-turn conversational context tracking.

### Core Architectural Principles:
1. **Zero External API / Data Privacy:** All deep learning models (YOLOv8 and BLIP VQA) run strictly on local hardware (in-memory inference), ensuring sensitive images and queries never leave the system.
2. **Apple Silicon Hardware Acceleration:** Native PyTorch Metal Performance Shaders (`mps`) support for high-throughput, low-latency inference on Apple M4 hardware.
3. **Decoupled Asynchronous Micro-Architecture:** FastAPI backend handling async I/O while delegating CPU/GPU tensor computation cleanly, paired with a reactive Vite + React frontend.
4. **Structured Object & Conversation Telemetry:** Complete persistence of session dialogues, image metadata, and normalized bounding box coordinates in PostgreSQL.

---

## 2. Multi-Modal Inference Pipeline

```
[ User Image ] ──────► [ Secure Ingestion & MIME Validation ]
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [ YOLOv8s Engine ]              [ Image Store (/uploads) ]
     (Object Detection on MPS)                   │
                 │                               │
                 ▼                               │
      [ Bounding Box Telemetry ]                 │
      [ Class Labels & Scores  ]                 │
                 │                               │
                 └───────────────┬───────────────┘
                                 │
[ User Question ] ───────────────┼───────────────► [ BLIP VQA Engine ]
                                 │              (Visual QA on MPS)
                                 │                       │
                                 ▼                       ▼
                     [ Context Fusion Engine ] ◄─────────┘
                                 ▲
                                 │
                     [ PostgreSQL Dialogue Memory ]
                     (Multi-turn History Window)
                                 │
                                 ▼
                     [ Coherent Conversational ]
                     [      Response Output    ]
```

### Context Fusion Engine Details
BLIP alone answers isolated visual queries (e.g., "What color is the truck? -> green"). It does not inherently preserve conversational context over multi-turn interactions.
The **Context Fusion Engine** bridges this gap:
1. Extracts real-time detection telemetry (object counts, classes, confidence scores, spatial coordinates) from YOLOv8.
2. Fetches the direct visual semantic inference from BLIP VQA.
3. Retrieves the last $N$ dialogue turns for the active session from PostgreSQL.
4. Synthesizes these inputs into a grammatically structured, context-aware response that acknowledges previous questions (e.g., "Earlier you asked about the vehicles. The green truck detected on the left has military markings, and there are 2 other vehicles nearby.").

---

## 3. Hardware Acceleration Strategy (Apple M4 MPS vs Docker)

- **Local Development (macOS M4):**
  - Executes directly via Python 3.11 virtual environment.
  - Automatically selects `torch.device("mps")` when `torch.backends.mps.is_available()` is true.
  - Utilizes 16GB unified memory for shared CPU/GPU tensor operations without PCIe transfer latency.
- **Production / Containerized Deployment (Docker):**
  - Standard Docker on macOS runs inside a Linux hypervisor virtual machine which cannot access macOS Metal APIs directly.
  - The container deployment architecture is therefore configured to default to CPU (or NVIDIA CUDA when deployed on Linux servers) while the native local development runner uses Apple MPS.

---

## 4. PostgreSQL Relational Schema

- **`sessions`**: Manages user conversation threads, timestamps, and titles.
- **`images`**: Stores image metadata, dimensions, storage paths, and session relationships.
- **`detected_objects`**: Relational telemetry storing bounding boxes $(x_{\min}, y_{\min}, x_{\max}, y_{\max})$, classes, and confidence scores for every detection pass.
- **`messages`**: Records multi-turn dialogue history, sender types (`user`, `assistant`, `system`), timestamps, and metadata payloads.
