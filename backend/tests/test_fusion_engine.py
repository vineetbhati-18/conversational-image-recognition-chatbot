import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.conversational_engine import MultiModalFusionEngine, DialogueTurn, QuestionIntent


@pytest.fixture
def ptp_telemetry():
    """Simulates actual YOLO detection telemetry from PTP.jpg."""
    return [
        {"class_name": "car", "confidence": 0.904, "spatial_sector": "bottom-center"},
        {"class_name": "car", "confidence": 0.848, "spatial_sector": "bottom-right"},
        {"class_name": "traffic light", "confidence": 0.837, "spatial_sector": "center"},
        {"class_name": "car", "confidence": 0.836, "spatial_sector": "bottom-center"},
        {"class_name": "traffic light", "confidence": 0.832, "spatial_sector": "top-left"},
        {"class_name": "traffic light", "confidence": 0.829, "spatial_sector": "top-right"},
        {"class_name": "traffic light", "confidence": 0.821, "spatial_sector": "top-center"},
        {"class_name": "car", "confidence": 0.802, "spatial_sector": "bottom-left"},
        {"class_name": "traffic light", "confidence": 0.786, "spatial_sector": "center"},
        {"class_name": "traffic light", "confidence": 0.778, "spatial_sector": "middle-left"},
        {"class_name": "car", "confidence": 0.772, "spatial_sector": "bottom-left"},
        {"class_name": "traffic light", "confidence": 0.741, "spatial_sector": "middle-left"},
        {"class_name": "traffic light", "confidence": 0.676, "spatial_sector": "middle-left"},
        {"class_name": "traffic light", "confidence": 0.669, "spatial_sector": "center"},
        {"class_name": "car", "confidence": 0.653, "spatial_sector": "bottom-right"},
        {"class_name": "truck", "confidence": 0.353, "spatial_sector": "bottom-right"},
    ]


def test_fusion_object_inventory_query(ptp_telemetry):
    """Verifies: 'What objects are detected in this image?' returns all classes, visible counts at 40%, and total detections."""
    engine = MultiModalFusionEngine()
    query = "What objects are detected in this image?"
    res = engine.generate_fused_response(query, vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)

    content = res["content"]
    assert "15 visible objects" in content
    assert "2 categories" in content
    assert "6 cars" in content
    assert "9 traffic lights" in content
    assert "16 total detections found prior to filtering" in content
    assert "1 truck below threshold" in content
    assert res["intent"] == "object_inventory"


def test_fusion_specific_count_queries(ptp_telemetry):
    """Verifies counting individual classes, vehicle categories, and zero-detection classes."""
    engine = MultiModalFusionEngine()

    # 1. Cars count
    res_car = engine.generate_fused_response("How many cars are in this image?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "6 cars" in res_car["content"]
    assert "40% confidence" in res_car["content"]

    # 2. Traffic lights count
    res_tl = engine.generate_fused_response("How many traffic lights?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "9 traffic lights" in res_tl["content"]

    # 3. Trucks count (0 visible at 40%, 1 total)
    res_truck = engine.generate_fused_response("How many trucks?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "0 trucks at 40% confidence" in res_truck["content"]
    assert "1 truck detected at lower confidence" in res_truck["content"]

    # 4. Zero detection class (persons)
    res_person = engine.generate_fused_response("How many persons?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "did not detect any persons" in res_person["content"]


def test_fusion_spatial_queries(ptp_telemetry):
    """Verifies location queries using YOLO bounding-box sectors."""
    engine = MultiModalFusionEngine()

    # Where are cars located?
    res_loc = engine.generate_fused_response("Where are the cars located?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "cars" in res_loc["content"].lower()
    assert "bottom-center" in res_loc["content"]

    # What is on the left?
    res_left = engine.generate_fused_response("What is on the left?", vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "left" in res_left["content"].lower()
    assert "traffic lights" in res_left["content"]


def test_fusion_visual_attribute_blip(ptp_telemetry):
    """Verifies routing color / appearance queries to BLIP VQA."""
    engine = MultiModalFusionEngine()
    query = "What color is the car in front?"
    res = engine.generate_fused_response(query, vqa_answer="black", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    assert "black" in res["content"].lower()
    assert "car" in res["content"].lower()


def test_fusion_multi_turn_follow_up_conversation(ptp_telemetry):
    """Verifies multi-turn contextual continuity across mixed question types."""
    engine = MultiModalFusionEngine()

    # Turn 1: Object inventory
    t1_q = "What objects are detected in this image?"
    t1_res = engine.generate_fused_response(t1_q, vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=[], conf_threshold=0.40)
    history = [
        DialogueTurn("user", t1_q),
        DialogueTurn("assistant", t1_res["content"], {"primary_subject": t1_res["primary_subject"]}),
    ]

    # Turn 2: Follow-up spatial query referencing "they"
    t2_q = "Where are they located?"
    t2_res = engine.generate_fused_response(t2_q, vqa_answer="", yolo_detections=ptp_telemetry, dialogue_history=history, conf_threshold=0.40)
    assert "Regarding your follow-up:" in t2_res["content"]
    assert "cars" in t2_res["content"]
    assert "traffic lights" in t2_res["content"]
    history.extend([
        DialogueTurn("user", t2_q),
        DialogueTurn("assistant", t2_res["content"], {"primary_subject": t2_res["primary_subject"]}),
    ])

    # Turn 3: Follow-up asking about car color using "it"
    history.append(DialogueTurn("user", "How many cars?"))
    history.append(DialogueTurn("assistant", "I detected 6 cars in the image.", {"primary_subject": "car"}))

    t4_q = "What color is it?"
    t4_res = engine.generate_fused_response(t4_q, vqa_answer="silver", yolo_detections=ptp_telemetry, dialogue_history=history, conf_threshold=0.40)
    assert "Regarding your follow-up:" in t4_res["content"]
    assert "silver" in t4_res["content"].lower()
    assert "car" in t4_res["content"].lower()


def test_fusion_road_sidewalk_spatial_query():
    """Verifies queries like 'Is the truck parked on the road or on the sidewalk?' return explicit surface location."""
    engine = MultiModalFusionEngine()
    pap_telemetry = [
        {"class_name": "car", "confidence": 0.67, "spatial_sector": "middle-right"},
        {"class_name": "car", "confidence": 0.56, "spatial_sector": "top-right"},
        {"class_name": "truck", "confidence": 0.50, "spatial_sector": "center"},
    ]

    # Query 1: road vs sidewalk
    res = engine.generate_fused_response(
        "Is the truck parked on the road or on the sidewalk?",
        vqa_answer="",
        yolo_detections=pap_telemetry,
        dialogue_history=[],
        conf_threshold=0.40,
    )
    assert res["intent"] == "spatial_location"
    assert "road (street)" in res["content"]
    assert "not on the sidewalk" in res["content"]
    assert "center" in res["content"]

    # Query 2: parked on sidewalk
    res_sw = engine.generate_fused_response(
        "Is it parked on the sidewalk?",
        vqa_answer="",
        yolo_detections=pap_telemetry,
        dialogue_history=[
            DialogueTurn("user", "Where is the truck?"),
            DialogueTurn("assistant", "The truck is in the center.", {"primary_subject": "truck"}),
        ],
        conf_threshold=0.40,
    )
    assert "not on the sidewalk" in res_sw["content"]

