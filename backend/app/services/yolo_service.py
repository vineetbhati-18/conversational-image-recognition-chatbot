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
            # Single-thread execution to prevent CPU thrashing on fractional cloud containers
            try:
                torch.set_num_threads(1)
                torch.set_num_interop_threads(1)
            except Exception:
                pass

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

    @staticmethod
    def calculate_spatial_position(x_min: float, y_min: float, x_max: float, y_max: float, img_w: int, img_h: int) -> str:
        """
        Determines the intuitive spatial sector of a detected object within the image.
        """
        cx = (x_min + x_max) / 2.0
        cy = (y_min + y_max) / 2.0

        horiz = "left" if cx < img_w * 0.38 else "right" if cx > img_w * 0.62 else "center"
        vert = "top" if cy < img_h * 0.38 else "bottom" if cy > img_h * 0.62 else "middle"

        if horiz == "center" and vert == "middle":
            return "center"
        return f"{vert}-{horiz}"

    def detect_objects(
        self,
        image_source,
        conf_threshold: float = 0.35,
        classes_filter: Optional[list] = None,
    ) -> dict:
        """
        Executes deep-learning object detection on an image.
        Returns detected classes, confidence scores, bounding boxes, normalized coordinates,
        spatial sector tags, and execution metrics.
        """
        self.load_model()
        import time
        import gc
        from uuid import uuid4

        start_time = time.perf_counter()
        with torch.inference_mode():
            results = self.model.predict(
                source=image_source,
                conf=conf_threshold,
                imgsz=320,
                device=self.device,
                verbose=False,
            )
        latency_ms = (time.perf_counter() - start_time) * 1000

        detections = []
        result = results[0]  # First image in batch
        boxes = result.boxes
        orig_shape = result.orig_shape  # (height, width)
        img_h, img_w = orig_shape[0], orig_shape[1]

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0].item())
                class_name = result.names[cls_id]

                if classes_filter and class_name not in classes_filter:
                    continue

                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()  # [x_min, y_min, x_max, y_max]

                x_min, y_min, x_max, y_max = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
                bbox_w = x_max - x_min
                bbox_h = y_max - y_min
                area_ratio = round((bbox_w * bbox_h) / (img_w * img_h), 4) if (img_w * img_h) > 0 else 0.0

                spatial_sector = self.calculate_spatial_position(x_min, y_min, x_max, y_max, img_w, img_h)

                detections.append({
                    "id": str(uuid4()),
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "confidence_percentage": round(conf * 100, 1),
                    "spatial_sector": spatial_sector,
                    "area_ratio": area_ratio,
                    "bbox": {
                        "x_min": round(x_min, 2),
                        "y_min": round(y_min, 2),
                        "x_max": round(x_max, 2),
                        "y_max": round(y_max, 2),
                    },
                    "normalized_bbox": {
                        "x_min": round(x_min / img_w, 4) if img_w else 0.0,
                        "y_min": round(y_min / img_h, 4) if img_h else 0.0,
                        "x_max": round(x_max / img_w, 4) if img_w else 0.0,
                        "y_max": round(y_max / img_h, 4) if img_h else 0.0,
                    },
                })

        logger.info(
            f"YOLO detected {len(detections)} objects on {self.device.upper()} in {latency_ms:.2f}ms"
        )
        del results
        gc.collect()
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
        except Exception:
            pass

        return {
            "detections": detections,
            "count": len(detections),
            "image_dimensions": {"width": img_w, "height": img_h},
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
