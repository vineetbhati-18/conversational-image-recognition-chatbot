import torch
from ultralytics import YOLO
import logging
from typing import Optional
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger("bel_chatbot.yolo_service")
settings = get_settings()


class YOLOService:
    """
    YOLOv8 Deep-Learning Object Detection Engine.
    Configured for local Apple Silicon Metal Performance Shaders (MPS) execution.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.YOLO_MODEL_NAME
        self.device = settings.INFERENCE_DEVICE
        self.model: Optional[YOLO] = None
        self._is_loaded = False

    def load_model(self) -> None:
        """
        Loads YOLO model weights into memory and assigns to acceleration device.
        """
        if self._is_loaded and self.model is not None:
            return

        logger.info(f"Loading YOLOv8 weights ({self.model_name}) on device: {self.device.upper()}...")
        try:
            self.model = YOLO(self.model_name)
            # Verify device compatibility
            if self.device == "mps" and not torch.backends.mps.is_available():
                logger.warning("MPS requested but not available. Falling back to CPU.")
                self.device = "cpu"

            self._is_loaded = True
            logger.info(f"YOLOv8 ({self.model_name}) successfully loaded on {self.device.upper()}.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise e

    def is_ready(self) -> bool:
        return self._is_loaded and self.model is not None


_yolo_instance: Optional[YOLOService] = None


def get_yolo_service() -> YOLOService:
    """
    Singleton accessor for the YOLO inference service.
    """
    global _yolo_instance
    if _yolo_instance is None:
        _yolo_instance = YOLOService()
    return _yolo_instance
