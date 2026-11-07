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


def test_suppress_duplicate_nested_truck_boxes():
    """
    Verifies that duplicate sub-boxes of the same class (such as the rear cargo bin of a truck
    being detected as a second truck) are cleanly suppressed via NMS and containment suppression.
    """
    detections = [
        {"class_name": "truck", "confidence": 0.8398, "bbox": {"x_min": 627.41, "y_min": 194.85, "x_max": 1138.77, "y_max": 653.28}},
        {"class_name": "car", "confidence": 0.6636, "bbox": {"x_min": 1520.33, "y_min": 180.68, "x_max": 1631.29, "y_max": 298.81}},
        {"class_name": "car", "confidence": 0.6179, "bbox": {"x_min": 1367.45, "y_min": 352.88, "x_max": 1548.23, "y_max": 559.69}},
        {"class_name": "truck", "confidence": 0.4345, "bbox": {"x_min": 765.35, "y_min": 199.87, "x_max": 1137.79, "y_max": 586.62}},
    ]

    filtered = YOLOService.suppress_duplicate_nested_boxes(detections)
    trucks = [d for d in filtered if d["class_name"] == "truck"]
    cars = [d for d in filtered if d["class_name"] == "car"]

    assert len(trucks) == 1, f"Expected 1 truck, found {len(trucks)}"
    assert trucks[0]["confidence"] == 0.8398
    assert len(cars) == 2, f"Expected 2 cars, found {len(cars)}"

