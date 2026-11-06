# API Specification (FastAPI REST v1)

**Base URL:** `/api/v1`

---

## 1. Health & System
- `GET /health`
  - Response: `{"status": "healthy", "device": "mps", "yolo_ready": true, "vqa_ready": true, "database": "connected"}`

---

## 2. Session Management
- `POST /sessions`
  - Creates a new chat session.
  - Request: `{"title": "Optional session title"}`
  - Response: `{"id": "uuid", "title": "New Session", "created_at": "ISO-8601"}`

- `GET /sessions`
  - Lists all existing conversation sessions sorted by most recent.

- `GET /sessions/{session_id}`
  - Retrieves a specific session with its full message history and associated images.

- `DELETE /sessions/{session_id}`
  - Deletes a session and cascades to all associated messages, images, and telemetry.

---

## 3. Image Upload & Vision Telemetry
- `POST /images/upload`
  - Multipart form-data: `file` (image binary), `session_id` (UUID).
  - Validation: Magic byte inspection (JPEG, PNG, WebP), file size limit (15MB).
  - Processing: Computes dimensions, persists locally under `backend/uploads/`, triggers YOLOv8s detection pass.
  - Response:
    ```json
    {
      "image_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "filename": "recon_sample.jpg",
      "url": "/api/v1/images/3fa85f64-5717-4562-b3fc-2c963f66afa6/file",
      "width": 1920,
      "height": 1080,
      "detected_objects": [
        {
          "id": "uuid",
          "class_name": "truck",
          "confidence": 0.924,
          "bbox": {
            "x_min": 120.5,
            "y_min": 240.0,
            "x_max": 450.2,
            "y_max": 680.1
          }
        }
      ]
    }
    ```

- `GET /images/{image_id}/file`
  - Streams the raw image bytes.

- `POST /images/{image_id}/detect`
  - Re-runs object detection with an updated confidence threshold slider (e.g., `confidence=0.5`).

---

## 4. Conversational Chat & VQA
- `POST /chat/message`
  - Sends a user message and returns context-aware multi-turn assistant answer.
  - Request:
    ```json
    {
      "session_id": "uuid",
      "image_id": "uuid",
      "content": "What is the vehicle on the left side?"
    }
    ```
  - Response:
    ```json
    {
      "id": "uuid",
      "session_id": "uuid",
      "sender_type": "assistant",
      "content": "The vehicle on the left is a green military-style truck detected with 92.4% confidence.",
      "created_at": "ISO-8601",
      "metadata": {
        "vqa_answer": "truck",
        "detected_classes": ["truck", "person"],
        "latency_ms": 48
      }
    }
    ```
