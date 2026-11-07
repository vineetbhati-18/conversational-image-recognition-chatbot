#!/usr/bin/env python3
"""
Model Weight Preloading & Verification Script for Production Deployment.
Pre-caches YOLOv8 and BLIP VQA model weights during build/Docker image compilation.
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preload_models")

def preload_yolo():
    logger.info("Pre-caching YOLOv8s weights (yolov8s.pt)...")
    from ultralytics import YOLO
    model = YOLO("yolov8s.pt")
    logger.info("YOLOv8s successfully loaded and cached.")

def preload_blip():
    logger.info("Pre-caching Salesforce/blip-vqa-base weights...")
    from transformers import BlipProcessor, BlipForQuestionAnswering
    model_name = "Salesforce/blip-vqa-base"
    BlipProcessor.from_pretrained(model_name)
    BlipForQuestionAnswering.from_pretrained(model_name)
    logger.info("BLIP VQA Base successfully loaded and cached.")

if __name__ == "__main__":
    try:
        preload_yolo()
        preload_blip()
        logger.info("All production model weights preloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to preload model weights: {e}")
        sys.exit(1)
