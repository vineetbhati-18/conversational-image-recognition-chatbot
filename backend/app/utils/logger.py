import logging
import sys
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter for BEL enterprise auditing.
    """
    def format(self, record: logging.LogRecord) -> str:
        record_time = self.formatTime(record, self.datefmt)
        request_id = getattr(record, "request_id", "-")
        prefix = f"[{record_time}] [{record.levelname:<7}] [req:{request_id}] [{record.name}]:"
        return f"{prefix} {record.getMessage()}"


def setup_logger(name: str = "bel_chatbot", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if reloaded
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    full_name = f"bel_chatbot.{module_name}" if module_name else "bel_chatbot"
    return logging.getLogger(full_name)
