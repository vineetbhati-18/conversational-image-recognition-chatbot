#!/usr/bin/env python3
"""
Model Weight Preloading & Verification Script for Production Deployment.
Pre-caches YOLOv8n model weights during build/Docker image compilation.
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preload_models")

def preload_yolo():
    logger.info("Pre-caching YOLOv8n weights (yolov8n.pt)...")
    from ultralytics import YOLO
    YOLO("yolov8n.pt")
    logger.info("YOLOv8n model successfully loaded and cached.")

if __name__ == "__main__":
    try:
        preload_yolo()
        logger.info("Production YOLOv8n model weights preloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to preload model weights: {e}")
        sys.exit(1)
