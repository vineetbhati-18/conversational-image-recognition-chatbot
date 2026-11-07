import pytest
import io
import time
from unittest.mock import patch, MagicMock
from PIL import Image
from app.services.blip_service import BLIPService


@pytest.fixture
def test_image(tmp_path):
    img = Image.new("RGB", (200, 200), color="white")
    path = tmp_path / "test_truck.jpg"
    img.save(path)
    return path


def test_vqa_successful_inference(test_image):
    """
    Test genuine VQA inference parsing when external provider succeeds.
    """
    service = BLIPService()
    service.gemini_key = "test-mock-gemini-key"

    mock_gemini_response = MagicMock()
    mock_gemini_response.status_code = 200
    mock_gemini_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "The truck is white and silver."}]
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_gemini_response):
        result = service.answer_question(test_image, "What color is the truck?")
        assert result["answer"] == "The truck is white and silver."
        assert result["error"] is None
        assert result["device"] == "gemini_api"


def test_vqa_invalid_token_handling(test_image):
    """
    Test error handling when HF_TOKEN is invalid or unauthorized (HTTP 401).
    """
    service = BLIPService()
    service.gemini_key = None
    service.hf_token = "hf_invalid_token_xyz"

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"error": "Invalid username or password."}'

    with patch("requests.post", return_value=mock_resp):
        result = service.answer_question(test_image, "What color is the truck?")
        assert result["answer"] is None
        assert "unavailable" in result["error"].lower()


def test_vqa_unavailable_provider_or_credits_exhausted(test_image):
    """
    Test handling when Hugging Face returns 402 Payment Required or 400 Model Not Supported.
    """
    service = BLIPService()
    service.gemini_key = None
    service.hf_token = "hf_valid_but_no_credits"

    mock_resp = MagicMock()
    mock_resp.status_code = 402
    mock_resp.text = '{"error": "Purchase pre-paid credits to continue using Inference Providers."}'

    with patch("requests.post", return_value=mock_resp):
        result = service.answer_question(test_image, "What color is the truck?")
        assert result["answer"] is None
        assert result["error"] is not None
        # Must never fabricate an answer when credits are exhausted
        assert result["answer"] != "white"


def test_vqa_timeout_handling(test_image):
    """
    Test that connection timeouts are safely caught and return within reasonable bounds.
    """
    service = BLIPService()
    service.gemini_key = None
    service.hf_token = "hf_valid"

    import requests
    with patch("requests.post", side_effect=requests.exceptions.Timeout("Connection timed out")):
        start = time.perf_counter()
        result = service.answer_question(test_image, "What color is the truck?")
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0
        assert result["answer"] is None
        assert "unavailable" in result["error"].lower()


def test_vqa_safe_logging_never_exposes_token(test_image, caplog):
    """
    Verifies that secret tokens (HF_TOKEN, GEMINI_API_KEY) are never leaked in application logs.
    """
    secret_token = "hf_SUPER_SECRET_TOKEN_DO_NOT_LEAK_12345"
    service = BLIPService()
    service.gemini_key = None
    service.hf_token = secret_token

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = '{"error": "Model not supported"}'

    with patch("requests.post", return_value=mock_resp):
        import logging
        with caplog.at_level(logging.DEBUG):
            service.answer_question(test_image, "What color is the truck?")

    for record in caplog.records:
        assert secret_token not in record.message
