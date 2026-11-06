import pytest
import torch
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.blip_service import BLIPService, get_blip_service


def test_blip_service_initialization():
    service = BLIPService()
    assert service.model_name == "Salesforce/blip-vqa-base"
    if torch.backends.mps.is_available():
        assert service.device == "mps"
    else:
        assert service.device in ("cuda", "cpu")


def test_blip_singleton():
    b1 = get_blip_service()
    b2 = get_blip_service()
    assert b1 is b2
