import pytest
import numpy as np
from PIL import Image
import io
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.yolo_service import YOLOService


def test_yolo_inference_pipeline():
    # Use lightweight nano model for unit testing
    service = YOLOService(model_name="yolov8n.pt")

    # Create synthetic RGB image (300x300 numpy array)
    test_img = Image.new("RGB", (300, 300), color=(128, 128, 128))

    output = service.detect_objects(test_img, conf_threshold=0.25)
    assert "detections" in output
    assert "latency_ms" in output
    assert "device" in output
    assert output["device"] in ("mps", "cuda", "cpu")
    assert isinstance(output["detections"], list)
