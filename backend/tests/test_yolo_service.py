import pytest
import torch
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.yolo_service import YOLOService, get_yolo_service


def test_yolo_service_device_resolution():
    service = YOLOService(model_name="yolov8n.pt")
    assert service.model_name == "yolov8n.pt"
    # Verify device is mps on macOS with Apple Silicon
    if torch.backends.mps.is_available():
        assert service.device == "mps"
    else:
        assert service.device in ("cuda", "cpu")


def test_yolo_singleton():
    s1 = get_yolo_service()
    s2 = get_yolo_service()
    assert s1 is s2
