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
    Salesforce BLIP Visual Question Answering (VQA) Service.
    
    Architectural Guarantee for Free-Tier Cloud Deployments:
    - Never loads 1.6GB local BLIP model weights into container RAM (guaranteeing
      zero risk of Render 512MB RAM OOM-kills).
    - Uses genuine external VQA inference via Hugging Face Serverless Inference API
      configured with environment variable HF_TOKEN.
    - If external VQA is unconfigured or unavailable, returns a clear, honest error
      instead of inventing answers.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.VQA_MODEL_NAME
        self.hf_token = os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None)
        self.hf_endpoints = [
            f"https://router.huggingface.co/hf-inference/models/{self.model_name}",
            f"https://api-inference.huggingface.co/models/{self.model_name}",
        ]

    def is_configured(self) -> bool:
        """Returns True if external inference credentials are configured."""
        return bool(self.hf_token and self.hf_token.strip())

    def _query_hf_api(self, pil_image: Image.Image, question: str) -> Optional[Dict[str, Any]]:
        """
        Executes genuine external VQA inference using Hugging Face Serverless API.
        """
        if not self.is_configured():
            logger.info("External VQA skipped: HF_TOKEN not configured.")
            return None

        # Convert PIL image to optimized base64 JPEG
        buf = io.BytesIO()
        # Resize to max 640px to reduce payload size and latency
        img_copy = pil_image.copy()
        if max(img_copy.size) > 640:
            img_copy.thumbnail((640, 640), Image.Resampling.BILINEAR)
        img_copy.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        del img_copy
        buf.close()
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
                res = requests.post(endpoint, headers=headers, json=payload, timeout=20)
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

        # 1. Query external Hugging Face inference API
        api_result = self._query_hf_api(pil_image, question)
        if api_result is not None and api_result.get("answer"):
            return api_result

        # 2. If external VQA is unconfigured or failed, return clear error without inventing answers
        latency_ms = (time.perf_counter() - start_time) * 1000
        error_msg = (
            "External Visual Question Answering is currently unavailable (HF_TOKEN not configured or service unreachable). "
            "Please configure HF_TOKEN in the environment, or ask questions about detected objects, counts, and spatial positions."
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
