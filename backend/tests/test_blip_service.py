import pytest
import sys
from pathlib import Path
from PIL import Image

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.blip_service import BLIPService, get_blip_service


def test_blip_service_initialization():
    service = BLIPService()
    assert service.model_name == "Salesforce/blip-vqa-base"
    assert len(service.hf_endpoints) >= 1


def test_blip_singleton():
    b1 = get_blip_service()
    b2 = get_blip_service()
    assert b1 is b2


def test_vqa_unconfigured_error_handling(tmp_path):
    """
    Verifies that when external VQA is unconfigured, it returns a clean error
    and never invents fake answers.
    """
    service = BLIPService()
    service.hf_token = None  # Ensure unconfigured

    # Create dummy test image
    img = Image.new("RGB", (100, 100), color="blue")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)

    res = service.answer_question(img_path, "What color is the image?")
    assert res["answer"] is None
    assert "unavailable" in res["error"].lower()
    assert res["device"] == "external_api"


def test_vqa_mock_external_success(tmp_path, monkeypatch):
    """
    Verifies external VQA response parsing when external service responds 200.
    """
    service = BLIPService()
    service.hf_token = "hf_mock_token_for_testing"

    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test_red.jpg"
    img.save(img_path)

    class MockResponse:
        status_code = 200
        def json(self):
            return [{"answer": "red"}]

    monkeypatch.setattr("requests.post", lambda *args, **kwargs: MockResponse())

    res = service.answer_question(img_path, "What color is this?")
    assert res["answer"] == "red"
    assert res["error"] is None
