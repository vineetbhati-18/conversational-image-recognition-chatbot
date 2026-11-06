# REST API Specification (FastAPI v1)
**Project:** Conversational Image Recognition Chatbot  
**Organization:** Bharat Electronics Limited (BEL)  
**Base URL:** `/api/v1`

---

## 1. System & Health

### `GET /api/v1/health`
Checks backend and model availability.
- **Headers:** None required
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "app": "BEL Conversational Image Recognition Backend",
    "device": "mps",
    "yolo_ready": true,
    "blip_ready": true,
    "timestamp": "2026-11-06T14:15:30.123456"
  }
  ```

---

## 2. Session Management

### `POST /api/v1/sessions`
Initializes a new conversation session.
- **Request Body:**
  ```json
  {
    "title": "Tactical Reconnaissance Mission #1"
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
    "title": "Tactical Reconnaissance Mission #1",
    "created_at": "2026-11-06T14:15:30.123456Z",
    "updated_at": "2026-11-06T14:15:30.123456Z"
  }
  ```

### `GET /api/v1/sessions`
Lists conversation sessions ordered by most recent activity.
- **Query Parameters:**
  - `limit` (integer, default: 50)
  - `offset` (integer, default: 0)
- **Response `200 OK`:**
  ```json
  [
    {
      "id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
      "title": "Tactical Reconnaissance Mission #1",
      "created_at": "2026-11-06T14:15:30.123456Z",
      "updated_at": "2026-11-06T14:15:30.123456Z"
    }
  ]
  ```

### `GET /api/v1/sessions/{session_id}`
Retrieves session details including full message history, associated images, and detected objects.
- **Response `200 OK`:**
  ```json
  {
    "id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
    "title": "Tactical Reconnaissance Mission #1",
    "created_at": "2026-11-06T14:15:30.123456Z",
    "updated_at": "2026-11-06T14:15:30.123456Z",
    "messages": [
      {
        "id": "893c5d64-e5be-443b-8ea9-8d4889c258d4",
        "session_id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
        "image_id": "c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b",
        "sender_type": "user",
        "content": "What vehicles do you see?",
        "metadata": {},
        "created_at": "2026-11-06T14:16:00.123456Z"
      }
    ],
    "images": [
      {
        "id": "c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b",
        "session_id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
        "filename": "perimeter_recon.jpg",
        "file_size_bytes": 1048576,
        "width": 1920,
        "height": 1080,
        "mime_type": "image/jpeg",
        "url": "/uploads/c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b.jpg",
        "detected_objects": [
          {
            "id": "3bf540a8-b648-4cb1-afbc-40d6c5478ce1",
            "class_name": "truck",
            "confidence": 0.942,
            "bbox": {
              "x_min": 120.0,
              "y_min": 250.0,
              "x_max": 450.0,
              "y_max": 680.0
            }
          }
        ],
        "created_at": "2026-11-06T14:15:45.123456Z"
      }
    ]
  }
  ```

### `DELETE /api/v1/sessions/{session_id}`
Deletes session and cascades to all child messages, images, and detections.
- **Response `204 No Content`**

---

## 3. Image Upload & Detection

### `POST /api/v1/images/upload`
Uploads an image, verifies binary magic bytes, runs YOLOv8s deep-learning detection, and returns normalized bounding box telemetry.
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: binary file (JPEG, PNG, WebP; max 15MB)
  - `session_id`: UUID
- **Response `201 Created`:**
  ```json
  {
    "id": "c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b",
    "session_id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
    "filename": "perimeter_recon.jpg",
    "file_size_bytes": 1048576,
    "width": 1920,
    "height": 1080,
    "mime_type": "image/jpeg",
    "url": "/uploads/c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b.jpg",
    "detected_objects": [
      {
        "id": "3bf540a8-b648-4cb1-afbc-40d6c5478ce1",
        "class_name": "truck",
        "confidence": 0.942,
        "bbox": {
          "x_min": 120.0,
          "y_min": 250.0,
          "x_max": 450.0,
          "y_max": 680.0
        }
      }
    ],
    "created_at": "2026-11-06T14:15:45.123456Z"
  }
  ```

### `POST /api/v1/images/{image_id}/detect`
Re-runs detection on an uploaded image with a user-specified confidence threshold.
- **Request Body:**
  ```json
  {
    "confidence_threshold": 0.50
  }
  ```
- **Response `200 OK`:** Updated `ImageResponse`

### `GET /api/v1/images/{image_id}/file`
Streams the stored image file.
- **Response `200 OK`:** Binary stream (`image/jpeg`, `image/png`, or `image/webp`)

---

## 4. Multi-Turn Conversational Chat

### `POST /api/v1/chat/message`
Submits a user message and returns context-aware responses synthesized from YOLO detections, spatial sector telemetry, BLIP VQA, and prior conversation history.
- **Request Body:**
  ```json
  {
    "session_id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
    "image_id": "c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b",
    "content": "Where is the vehicle located?"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "id": "f5120ca2-4811-4ad9-bf95-5858cf85d992",
    "session_id": "e45a2db3-4f93-4a58-86d4-8393e507b97c",
    "image_id": "c1f6b158-9ffb-4a6c-9c3a-8673f84f3c7b",
    "sender_type": "assistant",
    "content": "The truck is located in the center-left quadrant of the image (confidence: 94.2%).",
    "metadata": {
      "detected_classes": ["truck"],
      "vqa_answer": null,
      "latency_ms": 35.4
    },
    "created_at": "2026-11-06T14:16:05.123456Z"
  }
  ```
