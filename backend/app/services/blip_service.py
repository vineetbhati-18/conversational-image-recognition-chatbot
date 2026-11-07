import torch
from PIL import Image
import time
import logging
import psutil
import os
import base64
import io
import requests
from typing import Optional, Union, TYPE_CHECKING
from pathlib import Path
from app.config import get_settings

if TYPE_CHECKING:
    from transformers import BlipProcessor, BlipForQuestionAnswering

logger = logging.getLogger("bel_chatbot.blip_service")
settings = get_settings()


class BLIPService:
    """
    Salesforce BLIP Visual Question Answering (VQA) Service.
    Supports:
    1. Hugging Face Serverless Inference API (when HF_TOKEN is configured)
    2. Local Apple Silicon Metal Performance Shaders (MPS) or CPU execution when memory permits
    3. Memory protection on low-RAM container environments (Render 512MB free tier)
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.VQA_MODEL_NAME
        self.device = settings.INFERENCE_DEVICE
        self.processor = None
        self.model = None
        self._is_loaded = False
        self.hf_token = os.getenv("HF_TOKEN") or getattr(settings, "HF_TOKEN", None)

    def _query_hf_api(self, pil_image: Image.Image, question: str) -> Optional[dict]:
        """
        Queries Hugging Face Serverless Inference API for Salesforce/blip-vqa-base.
        Returns None if request fails or token is missing.
        """
        if not self.hf_token:
            return None

        api_url = f"https://router.huggingface.co/hf-inference/models/{self.model_name}"
        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json"
        }

        # Convert PIL image to base64
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        start_time = time.perf_counter()
        try:
            res = requests.post(
                api_url,
                headers=headers,
                json={"inputs": {"image": img_b64, "question": question}},
                timeout=25
            )
            if res.status_code == 200:
                data = res.json()
                # BLIP response format: [{"answer": "..."}] or {"answer": "..."}
                raw_answer = ""
                if isinstance(data, list) and len(data) > 0:
                    raw_answer = data[0].get("answer", "")
                elif isinstance(data, dict):
                    raw_answer = data.get("answer", "")

                latency_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"Hugging Face BLIP API answered '{question}' -> '{raw_answer}' in {latency_ms:.2f}ms")
                return {
                    "question": question,
                    "answer": raw_answer,
                    "latency_ms": round(latency_ms, 2),
                    "device": "huggingface_api",
                    "model": self.model_name,
                }
            else:
                logger.warning(f"Hugging Face API returned status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Hugging Face API call failed: {e}")

        return None

    def load_model(self) -> None:
        if self._is_loaded and self.model is not None:
            return

        # Check total system memory to avoid kernel OOM panic on 512MB containers
        total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        if total_ram_gb < 1.2:
            logger.warning(
                f"System total RAM is {total_ram_gb:.2f}GB (< 1.2GB). "
                "Local BLIP VQA requires ~1.6GB RAM. Local model loading skipped to prevent OOM crash."
            )
            return

        logger.info(f"Loading BLIP VQA model ({self.model_name}) on device {self.device.upper()}...")
        try:
            try:
                torch.set_num_threads(1)
                torch.set_num_interop_threads(1)
            except Exception:
                pass

            from transformers import BlipProcessor, BlipForQuestionAnswering
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            self.model = BlipForQuestionAnswering.from_pretrained(self.model_name)

            # Move model to target device
            if self.device == "mps" and torch.backends.mps.is_available():
                self.model = self.model.to("mps")
            elif self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
            else:
                self.device = "cpu"
                self.model = self.model.to("cpu")

            self.model.eval()
            self._is_loaded = True
            logger.info(f"BLIP VQA successfully loaded on {self.device.upper()}.")
        except Exception as e:
            logger.error(f"Failed to load BLIP VQA model: {e}")
            raise e

    def answer_question(
        self,
        image: Union[Image.Image, str, Path],
        question: str,
    ) -> dict:
        """
        Performs Visual Question Answering on an input image and query text.
        """
        if isinstance(image, (str, Path)):
            pil_image = Image.open(str(image)).convert("RGB")
        else:
            pil_image = image.convert("RGB")

        # 1. Try Hugging Face API if token configured
        api_result = self._query_hf_api(pil_image, question)
        if api_result is not None:
            return api_result

        # 2. Check if local model can be loaded
        self.load_model()

        if not self._is_loaded or self.model is None or self.processor is None:
            logger.info("Local BLIP model unavailable on low-memory container; returning gracefully.")
            return {
                "question": question,
                "answer": "Visual attribute analysis via BLIP is currently operating in low-memory cloud mode.",
                "latency_ms": 1.0,
                "device": "cloud_safeguard",
                "model": self.model_name,
            }

        start_time = time.perf_counter()

        # Preprocess multimodal inputs
        inputs = self.processor(
            images=pil_image,
            text=question,
            return_tensors="pt",
        ).to(self.device)

        # Generate answer with no grad
        with torch.inference_mode():
            output_tokens = self.model.generate(**inputs, max_new_tokens=50)
            raw_answer = self.processor.decode(output_tokens[0], skip_special_tokens=True).strip()

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"BLIP answered '{question}' -> '{raw_answer}' in {latency_ms:.2f}ms on {self.device.upper()}")

        import gc
        gc.collect()

        return {
            "question": question,
            "answer": raw_answer,
            "latency_ms": round(latency_ms, 2),
            "device": self.device,
            "model": self.model_name,
        }


_blip_instance: Optional[BLIPService] = None


def get_blip_service() -> BLIPService:
    global _blip_instance
    if _blip_instance is None:
        _blip_instance = BLIPService()
    return _blip_instance
