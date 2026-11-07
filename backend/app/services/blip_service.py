import time
import logging
import os
import base64
import io
import requests
from typing import Optional, Union, Dict, Any
from pathlib import Path
from PIL import Image
from app.config import get_settings

logger = logging.getLogger("bel_chatbot.blip_service")
settings = get_settings()


class BLIPService:
    """
    Visual Question Answering (VQA) Service.

    Architectural Guarantee for Free-Tier Cloud Deployments:
    - Never loads local model weights into container RAM (guaranteeing
      zero risk of Render 512MB RAM OOM-kills).
    - Uses genuine external VQA inference via:
      1. Google Gemini API (free tier, preferred — set GEMINI_API_KEY env var)
      2. Hugging Face Serverless Inference API (fallback — set HF_TOKEN env var)
    - If external VQA is unconfigured or unavailable, returns a clear, honest error
      instead of inventing answers.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.VQA_MODEL_NAME
        self.hf_token = os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None)
        self.gemini_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        self.hf_endpoints = [
            f"https://router.huggingface.co/hf-inference/models/{self.model_name}",
            f"https://api-inference.huggingface.co/models/{self.model_name}",
        ]

    def is_configured(self) -> bool:
        """Returns True if any external inference credentials are configured."""
        return bool(
            (self.gemini_key and self.gemini_key.strip())
            or (self.hf_token and self.hf_token.strip())
        )

    def _image_to_base64_jpeg(self, pil_image: Image.Image, max_dim: int = 640) -> str:
        """Convert PIL image to optimized base64 JPEG string."""
        img_copy = pil_image.copy()
        if max(img_copy.size) > max_dim:
            img_copy.thumbnail((max_dim, max_dim), Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        img_copy.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        del img_copy
        buf.close()
        return b64

    def _query_gemini_api(self, pil_image: Image.Image, question: str) -> Optional[Dict[str, Any]]:
        """
        Executes genuine VQA inference using Google Gemini API free tier.
        Uses gemini-2.0-flash model for fast, free visual understanding.
        """
        if not self.gemini_key or not self.gemini_key.strip():
            return None

        img_b64 = self._image_to_base64_jpeg(pil_image)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key.strip()}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"You are a visual analysis assistant for an object detection application. Answer the following question about this image concisely and accurately in 1-2 sentences. Question: {question}"},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_b64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 150,
                "temperature": 0.3,
            },
        }

        start_time = time.perf_counter()
        try:
            res = requests.post(url, json=payload, timeout=4)
            latency_ms = (time.perf_counter() - start_time) * 1000

            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    answer = parts[0].get("text", "").strip() if parts else ""
                    if answer:
                        logger.info(f"Gemini VQA answered '{question}' -> '{answer[:80]}...' in {latency_ms:.0f}ms")
                        return {
                            "question": question,
                            "answer": answer,
                            "error": None,
                            "latency_ms": round(latency_ms, 2),
                            "device": "gemini_api",
                            "model": "gemini-2.0-flash",
                        }
            else:
                logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini API connection error: {e}")

        return None

    def _query_hf_api(self, pil_image: Image.Image, question: str) -> Optional[Dict[str, Any]]:
        """
        Executes genuine external VQA inference using Hugging Face Serverless API.
        """
        if not self.hf_token or not self.hf_token.strip():
            logger.info("External VQA (HF) skipped: HF_TOKEN not configured.")
            return None

        img_b64 = self._image_to_base64_jpeg(pil_image)
        from app.utils.memory import trim_process_memory
        trim_process_memory()

        headers = {
            "Authorization": f"Bearer {self.hf_token.strip()}",
            "Content-Type": "application/json"
        }
        payload = {"inputs": {"image": img_b64, "question": question}}

        start_time = time.perf_counter()

        for endpoint in self.hf_endpoints:
            try:
                res = requests.post(endpoint, headers=headers, json=payload, timeout=3)
                if res.status_code == 200:
                    data = res.json()
                    raw_answer = ""
                    if isinstance(data, list) and len(data) > 0:
                        raw_answer = data[0].get("answer", "")
                    elif isinstance(data, dict):
                        raw_answer = data.get("answer", "")

                    latency_ms = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"External VQA answered '{question}' -> '{raw_answer}' in {latency_ms:.2f}ms via {endpoint}"
                    )
                    return {
                        "question": question,
                        "answer": raw_answer.strip() if raw_answer else None,
                        "error": None,
                        "latency_ms": round(latency_ms, 2),
                        "device": "external_api",
                        "model": self.model_name,
                    }
                else:
                    logger.warning(
                        f"Hugging Face endpoint {endpoint} returned status {res.status_code}: {res.text[:200]}"
                    )
            except Exception as e:
                logger.warning(f"Hugging Face endpoint {endpoint} connection error: {e}")

        return None

    def answer_question(
        self,
        image: Union[Image.Image, str, Path],
        question: str,
    ) -> Dict[str, Any]:
        """
        Performs Visual Question Answering on an image and query text.
        Never loads local model weights into container RAM.
        Tries Gemini API first, then HF API as fallback.
        """
        start_time = time.perf_counter()

        try:
            if isinstance(image, (str, Path)):
                with Image.open(str(image)) as img:
                    pil_image = img.convert("RGB")
            else:
                pil_image = image.convert("RGB")
        except Exception as e:
            return {
                "question": question,
                "answer": None,
                "error": f"Failed to load image for visual analysis: {str(e)}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                "device": "external_api",
                "model": self.model_name,
            }

        # 1. Try Google Gemini API (free tier, preferred)
        gemini_result = self._query_gemini_api(pil_image, question)
        if gemini_result and gemini_result.get("answer"):
            return gemini_result

        # 2. Try Hugging Face Inference API (fallback)
        hf_result = self._query_hf_api(pil_image, question)
        if hf_result and hf_result.get("answer"):
            return hf_result

        # 3. If all external VQA is unconfigured or failed, return clear error
        latency_ms = (time.perf_counter() - start_time) * 1000

        configured_services = []
        if self.gemini_key:
            configured_services.append("Gemini")
        if self.hf_token:
            configured_services.append("HuggingFace")

        if not configured_services:
            error_msg = (
                "Visual question answering is currently unavailable (API key required). "
                "Set GEMINI_API_KEY (free at aistudio.google.com) or HF_TOKEN in environment variables. "
                "You can still ask about detected objects, counts, and spatial positions."
            )
        else:
            error_msg = (
                f"External VQA services ({', '.join(configured_services)}) are temporarily unavailable or returned errors. "
                "You can still ask about detected objects, counts, and spatial positions."
            )

        logger.info(f"VQA unavailable for query '{question}': {error_msg}")

        return {
            "question": question,
            "answer": None,
            "error": error_msg,
            "latency_ms": round(latency_ms, 2),
            "device": "external_api",
            "model": self.model_name,
        }


_blip_instance: Optional[BLIPService] = None


def get_blip_service() -> BLIPService:
    global _blip_instance
    if _blip_instance is None:
        _blip_instance = BLIPService()
    return _blip_instance
