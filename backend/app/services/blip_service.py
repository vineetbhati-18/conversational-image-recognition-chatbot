import torch
from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image
import time
import logging
from typing import Optional, Union
from pathlib import Path
from app.config import get_settings

logger = logging.getLogger("bel_chatbot.blip_service")
settings = get_settings()


class BLIPService:
    """
    Salesforce BLIP Visual Question Answering (VQA) Service.
    Runs on local Apple Silicon Metal Performance Shaders (MPS) or CPU.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.VQA_MODEL_NAME
        self.device = settings.INFERENCE_DEVICE
        self.processor: Optional[BlipProcessor] = None
        self.model: Optional[BlipForQuestionAnswering] = None
        self._is_loaded = False

    def load_model(self) -> None:
        if self._is_loaded and self.model is not None:
            return

        logger.info(f"Loading BLIP VQA model ({self.model_name}) on device {self.device.upper()}...")
        try:
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
        self.load_model()

        if isinstance(image, (str, Path)):
            pil_image = Image.open(str(image)).convert("RGB")
        else:
            pil_image = image.convert("RGB")

        start_time = time.perf_counter()

        # Preprocess multimodal inputs
        inputs = self.processor(
            images=pil_image,
            text=question,
            return_tensors="pt",
        ).to(self.device)

        # Generate answer with no grad
        with torch.no_grad():
            output_tokens = self.model.generate(**inputs, max_new_tokens=50)
            raw_answer = self.processor.decode(output_tokens[0], skip_special_tokens=True).strip()

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"BLIP answered '{question}' -> '{raw_answer}' in {latency_ms:.2f}ms on {self.device.upper()}")

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
