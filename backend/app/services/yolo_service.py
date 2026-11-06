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

    def detect_objects(
        self,
        image_source,
        conf_threshold: float = 0.35,
        classes_filter: Optional[list] = None,
    ) -> dict:
        """
        Executes deep-learning object detection on an image.
        Returns detected classes, confidence scores, bounding boxes, and execution metrics.
        """
        self.load_model()
        import time

        start_time = time.perf_counter()
        results = self.model.predict(
            source=image_source,
            conf=conf_threshold,
            device=self.device,
            verbose=False,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        detections = []
        result = results[0]  # First image in batch
        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0].item())
                class_name = result.names[cls_id]

                if classes_filter and class_name not in classes_filter:
                    continue

                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()  # [x_min, y_min, x_max, y_max]

                detections.append({
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "bbox": {
                        "x_min": round(xyxy[0], 2),
                        "y_min": round(xyxy[1], 2),
                        "x_max": round(xyxy[2], 2),
                        "y_max": round(xyxy[3], 2),
                    },
                })

        logger.info(
            f"YOLO detected {len(detections)} objects on {self.device.upper()} in {latency_ms:.2f}ms"
        )

        return {
            "detections": detections,
            "count": len(detections),
            "latency_ms": round(latency_ms, 2),
            "device": self.device,
            "model": self.model_name,
        }


_yolo_instance: Optional[YOLOService] = None


def get_yolo_service() -> YOLOService:
    """
    Singleton accessor for the YOLO inference service.
    """
    global _yolo_instance
    if _yolo_instance is None:
        _yolo_instance = YOLOService()
    return _yolo_instance
