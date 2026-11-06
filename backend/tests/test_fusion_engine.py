import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.conversational_engine import MultiModalFusionEngine, DialogueTurn


def test_fusion_count_query():
    engine = MultiModalFusionEngine()
    yolo_detections = [
        {"class_name": "truck", "spatial_sector": "center"},
        {"class_name": "truck", "spatial_sector": "top-left"},
        {"class_name": "car", "spatial_sector": "bottom-right"},
    ]
    query = "How many trucks are detected?"
    result = engine.generate_fused_response(query, vqa_answer="2", yolo_detections=yolo_detections, dialogue_history=[])

    assert "2 trucks" in result["content"]
    assert "truck" in result["detected_classes"]


def test_fusion_spatial_query():
    engine = MultiModalFusionEngine()
    yolo_detections = [
        {"class_name": "truck", "spatial_sector": "top-left"},
    ]
    query = "What is located on the top left?"
    result = engine.generate_fused_response(query, vqa_answer="truck", yolo_detections=yolo_detections, dialogue_history=[])

    assert "top-left" in result["content"]
    assert "truck" in result["content"]


def test_fusion_color_query_with_vqa():
    engine = MultiModalFusionEngine()
    yolo_detections = [{"class_name": "tank", "spatial_sector": "center"}]
    query = "What color is the tank?"
    result = engine.generate_fused_response(query, vqa_answer="camouflage green", yolo_detections=yolo_detections, dialogue_history=[])

    assert "camouflage green" in result["content"].lower()
