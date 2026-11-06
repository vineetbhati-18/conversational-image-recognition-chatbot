import pytest
import sys
from pathlib import Path
from PIL import Image

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.yolo_service import YOLOService


def test_spatial_sector_calculation():
    # Top-left box
    pos = YOLOService.calculate_spatial_position(10, 10, 50, 50, 1000, 1000)
    assert pos == "top-left"

    # Bottom-right box
    pos_br = YOLOService.calculate_spatial_position(800, 800, 950, 950, 1000, 1000)
    assert pos_br == "bottom-right"

    # Center box
    pos_center = YOLOService.calculate_spatial_position(450, 450, 550, 550, 1000, 1000)
    assert pos_center == "center"


def test_normalized_bbox_generation():
    service = YOLOService(model_name="yolov8n.pt")
    test_img = Image.new("RGB", (640, 480), color=(100, 150, 200))
    result = service.detect_objects(test_img)

    assert "image_dimensions" in result
    assert result["image_dimensions"]["width"] == 640
    assert result["image_dimensions"]["height"] == 480
