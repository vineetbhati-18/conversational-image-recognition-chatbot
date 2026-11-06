import pytest
from PIL import Image
import numpy as np
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.yolo_service import YOLOService


@pytest.fixture(scope="module")
def yolo_service():
    service = YOLOService(model_name="yolov8n.pt")
    service.load_model()
    return service


def test_yolo_aspect_ratios(yolo_service):
    # Test landscape, portrait, and extreme aspect ratios
    aspects = [(640, 480), (480, 640), (800, 200)]
    for w, h in aspects:
        img = Image.new("RGB", (w, h), color=(120, 140, 160))
        res = yolo_service.detect_objects(img, conf_threshold=0.3)
        assert res["image_dimensions"]["width"] == w
        assert res["image_dimensions"]["height"] == h
        assert isinstance(res["detections"], list)


def test_confidence_threshold_filtering(yolo_service):
    # Higher threshold must return equal or fewer objects than lower threshold
    img = Image.new("RGB", (400, 400), color=(80, 100, 120))
    low_res = yolo_service.detect_objects(img, conf_threshold=0.1)
    high_res = yolo_service.detect_objects(img, conf_threshold=0.8)

    assert len(high_res["detections"]) <= len(low_res["detections"])


def test_class_filtering(yolo_service):
    img = Image.new("RGB", (400, 400), color=(100, 100, 100))
    target_classes = ["truck", "car"]
    res = yolo_service.detect_objects(img, conf_threshold=0.1, classes_filter=target_classes)

    for obj in res["detections"]:
        assert obj["class_name"] in target_classes


def test_spatial_sectors_coverage(yolo_service):
    img_w, img_h = 1000, 1000
    pos_top_left = yolo_service.calculate_spatial_position(50, 50, 150, 150, img_w, img_h)
    pos_center = yolo_service.calculate_spatial_position(450, 450, 550, 550, img_w, img_h)
    pos_bottom_right = yolo_service.calculate_spatial_position(850, 850, 950, 950, img_w, img_h)

    assert pos_top_left == "top-left"
    assert pos_center == "center"
    assert pos_bottom_right == "bottom-right"
