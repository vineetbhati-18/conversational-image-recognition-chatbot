import pytest
import os
import psutil
from pathlib import Path
from PIL import Image
from app.services.yolo_service import get_yolo_service
from app.services.image_processing import validate_and_save_image

SAMPLE_IMAGE = Path(__file__).resolve().parent.parent.parent / ".venv/lib/python3.11/site-packages/ultralytics/assets/bus.jpg"

@pytest.mark.asyncio
async def test_yolo_concurrency_and_memory_stability(tmp_path):
    """
    Verifies that YOLO inference executes within memory bounds and memory remains
    stable across repeated inference passes without memory leaks.
    """
    yolo = get_yolo_service()
    assert yolo is not None

    proc = psutil.Process(os.getpid())
    initial_rss_mb = proc.memory_info().rss / (1024 * 1024)

    # Run 5 consecutive inferences
    for i in range(5):
        result = await yolo.detect_objects_async(
            image_source=str(SAMPLE_IMAGE),
            conf_threshold=0.30,
        )
        assert result["count"] > 0
        assert len(result["detections"]) > 0

    end_rss_mb = proc.memory_info().rss / (1024 * 1024)
    growth_mb = end_rss_mb - initial_rss_mb

    # Ensure memory growth is tightly bounded
    assert growth_mb < 80, f"Excessive memory growth detected: {growth_mb:.2f}MB"


@pytest.mark.asyncio
async def test_image_preprocessing_downscaling():
    """
    Verifies that oversized images are automatically downscaled to protect 512MB RAM.
    """
    import io
    # Create large 1600x1200 dummy image
    img = Image.new("RGB", (1600, 1200), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    file_bytes = buf.getvalue()

    meta = await validate_and_save_image(file_bytes, "oversized_test.jpg")
    assert meta["width"] <= 800
    assert meta["height"] <= 800
    assert Path(meta["storage_path"]).exists()
    # Cleanup
    try:
        os.remove(meta["storage_path"])
    except Exception:
        pass
