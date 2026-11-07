import torch
from ultralytics import YOLO
import logging
import asyncio
from typing import Optional
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger("bel_chatbot.yolo_service")
settings = get_settings()


class YOLOService:
    """
    YOLOv8 Deep-Learning Object Detection Engine.
    Configured for single-threaded CPU or Apple Silicon MPS execution with strict memory guards.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.YOLO_MODEL_NAME
        self.device = settings.INFERENCE_DEVICE
        self.model: Optional[YOLO] = None
        self._is_loaded = False
        self._lock = asyncio.Lock()

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
            try:
                self.model.fuse()
            except Exception:
                pass
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
        orig_dimensions: Optional[tuple] = None,
    ) -> dict:
        """
        Executes deep-learning object detection on an image.
        Returns detected classes, confidence scores, bounding boxes, normalized coordinates,
        spatial sector tags, and execution metrics.
        Coordinates are accurately mapped to the target/original image dimensions.
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
                imgsz=640,
                device=self.device,
                verbose=False,
            )
        latency_ms = (time.perf_counter() - start_time) * 1000

        detections = []
        result = results[0]  # First image in batch
        boxes = result.boxes
        orig_shape = result.orig_shape  # (height, width) of image_source
        img_h, img_w = orig_shape[0], orig_shape[1]

        target_w = int(orig_dimensions[0]) if orig_dimensions and orig_dimensions[0] > 0 else img_w
        target_h = int(orig_dimensions[1]) if orig_dimensions and orig_dimensions[1] > 0 else img_h

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls[0].item())
                class_name = result.names[cls_id]

                if classes_filter and class_name not in classes_filter:
                    continue

                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()  # [x_min, y_min, x_max, y_max] in image_source coordinates

                src_x_min, src_y_min, src_x_max, src_y_max = xyxy[0], xyxy[1], xyxy[2], xyxy[3]

                # 1. Compute true normalized coordinates in [0, 1] relative to image dimensions
                norm_x_min = max(0.0, min(1.0, src_x_min / img_w)) if img_w > 0 else 0.0
                norm_y_min = max(0.0, min(1.0, src_y_min / img_h)) if img_h > 0 else 0.0
                norm_x_max = max(0.0, min(1.0, src_x_max / img_w)) if img_w > 0 else 0.0
                norm_y_max = max(0.0, min(1.0, src_y_max / img_h)) if img_h > 0 else 0.0

                # 2. Scale back to target (original image) pixel coordinates
                target_x_min = norm_x_min * target_w
                target_y_min = norm_y_min * target_h
                target_x_max = norm_x_max * target_w
                target_y_max = norm_y_max * target_h

                bbox_w = target_x_max - target_x_min
                bbox_h = target_y_max - target_y_min
                area_ratio = round((bbox_w * bbox_h) / (target_w * target_h), 4) if (target_w * target_h) > 0 else 0.0

                spatial_sector = self.calculate_spatial_position(target_x_min, target_y_min, target_x_max, target_y_max, target_w, target_h)

                detections.append({
                    "id": str(uuid4()),
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(conf, 4),
                    "confidence_percentage": round(conf * 100, 1),
                    "spatial_sector": spatial_sector,
                    "area_ratio": area_ratio,
                    "bbox": {
                        "x_min": round(target_x_min, 2),
                        "y_min": round(target_y_min, 2),
                        "x_max": round(target_x_max, 2),
                        "y_max": round(target_y_max, 2),
                    },
                    "normalized_bbox": {
                        "x_min": round(norm_x_min, 4),
                        "y_min": round(norm_y_min, 4),
                        "x_max": round(norm_x_max, 4),
                        "y_max": round(norm_y_max, 4),
                    },
                })

        logger.info(
            f"YOLO detected {len(detections)} objects on {self.device.upper()} in {latency_ms:.2f}ms"
        )
        del boxes
        del result
        del results
        from app.utils.memory import trim_process_memory
        trim_process_memory()

        return {
            "detections": detections,
            "count": len(detections),
            "image_dimensions": {"width": target_w, "height": target_h},
            "latency_ms": round(latency_ms, 2),
            "device": self.device,
            "model": self.model_name,
        }

    async def detect_objects_async(
        self,
        image_source,
        conf_threshold: float = 0.35,
        classes_filter: Optional[list] = None,
        orig_dimensions: Optional[tuple] = None,
    ) -> dict:
        """
        Concurrency-controlled async wrapper for YOLO detection.
        Guarantees only ONE inference runs at a time to prevent memory spikes in 512MB RAM environments.
        """
        async with self._lock:
            return await asyncio.to_thread(
                self.detect_objects,
                image_source=image_source,
                conf_threshold=conf_threshold,
                classes_filter=classes_filter,
                orig_dimensions=orig_dimensions,
            )


_yolo_instance: Optional[YOLOService] = None


def get_yolo_service() -> YOLOService:
    """
    Singleton accessor for the YOLO inference service.
    """
    global _yolo_instance
    if _yolo_instance is None:
        _yolo_instance = YOLOService()
    return _yolo_instance
