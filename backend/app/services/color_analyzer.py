import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np

logger = logging.getLogger("bel_chatbot.color_analyzer")


class ObjectColorAnalyzer:
    """
    Computer Vision Color Extraction Engine.
    Analyzes pixel distributions in HSV color space across detected object bounding boxes.
    Provides genuine visual color understanding with zero external API dependencies or latency.
    """

    COLOR_DEFINITIONS = [
        # (name, filter_function)
        ("white", lambda h, s, v: (s < 0.22) & (v >= 0.65)),
        ("black", lambda h, s, v: v < 0.22),
        ("gray/silver", lambda h, s, v: (s < 0.22) & (v >= 0.22) & (v < 0.65)),
        ("red", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & ((h < 15) | (h >= 345))),
        ("orange", lambda h, s, v: (s >= 0.22) & (v >= 0.45) & (h >= 15) & (h < 40)),
        ("brown", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & (v < 0.45) & (h >= 15) & (h < 40)),
        ("yellow", lambda h, s, v: (s >= 0.22) & (v >= 0.35) & (h >= 40) & (h < 70)),
        ("green", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & (h >= 70) & (h < 165)),
        ("cyan", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & (h >= 165) & (h < 195)),
        ("blue", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & (h >= 195) & (h < 260)),
        ("purple", lambda h, s, v: (s >= 0.22) & (v >= 0.22) & (h >= 260) & (h < 315)),
        ("pink", lambda h, s, v: (s >= 0.22) & (v >= 0.50) & (h >= 315) & (h < 345)),
    ]

    @classmethod
    def analyze_crop_colors(cls, pil_crop: Image.Image) -> Dict[str, Any]:
        """
        Analyzes a PIL image crop and returns dominant color names and percentages.
        """
        if pil_crop.width < 2 or pil_crop.height < 2:
            return {"dominant_colors": [], "color_phrase": "indeterminate"}

        # Resize crop if large to optimize CPU execution
        if max(pil_crop.size) > 250:
            pil_crop.thumbnail((250, 250), Image.Resampling.BILINEAR)

        arr = np.array(pil_crop.convert("RGB"), dtype=np.float32) / 255.0
        total_pixels = arr.shape[0] * arr.shape[1]
        if total_pixels == 0:
            return {"dominant_colors": [], "color_phrase": "indeterminate"}

        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        cmax = np.maximum(np.maximum(r, g), b)
        cmin = np.minimum(np.minimum(r, g), b)
        diff = cmax - cmin

        h_deg = np.zeros_like(cmax)
        mask = diff > 1e-4
        r_eq = (cmax == r) & mask
        g_eq = (cmax == g) & mask
        b_eq = (cmax == b) & mask

        h_deg[r_eq] = (60.0 * ((g[r_eq] - b[r_eq]) / diff[r_eq]) + 360.0) % 360.0
        h_deg[g_eq] = (60.0 * ((b[g_eq] - r[g_eq]) / diff[g_eq]) + 120.0) % 360.0
        h_deg[b_eq] = (60.0 * ((r[b_eq] - g[b_eq]) / diff[b_eq]) + 240.0) % 360.0

        s = np.zeros_like(cmax)
        s[cmax > 1e-4] = diff[cmax > 1e-4] / cmax[cmax > 1e-4]
        v = cmax

        color_scores: Dict[str, float] = {}
        for name, filter_fn in cls.COLOR_DEFINITIONS:
            m = filter_fn(h_deg, s, v)
            pct = round(float(np.sum(m) / total_pixels) * 100.0, 1)
            if pct > 0:
                color_scores[name] = pct

        # Sort colors by prominence
        sorted_colors = sorted(color_scores.items(), key=lambda x: x[1], reverse=True)

        # Filter out minor background noise (must be >= 12% to be significant)
        significant = [(name, pct) for name, pct in sorted_colors if pct >= 12.0]

        # Prioritize prominent body colors over standard tire/shadow undercarriage black
        body_colors = [c for c in significant if c[0] != "black"]
        if body_colors:
            non_body = [c for c in significant if c[0] == "black"]
            # If white and gray/silver are both present, sort white first for intuitive natural phrasing
            names = [c[0] for c in body_colors]
            if "white" in names and "gray/silver" in names:
                body_colors = sorted(body_colors, key=lambda x: (x[0] != "white", -x[1]))
            significant = body_colors + non_body

        # Natural language synthesis
        if not significant:
            phrase = sorted_colors[0][0] if sorted_colors else "indeterminate"
        elif len(significant) == 1:
            phrase = significant[0][0]
        elif len(significant) >= 2:
            first_c = significant[0][0]
            second_c = significant[1][0]
            if second_c == "black":
                phrase = f"{first_c} with black trim"
            else:
                phrase = f"{first_c} and {second_c}"
        else:
            phrase = f"{significant[0][0]}"

        return {
            "dominant_colors": [name for name, _ in significant],
            "color_breakdown": dict(sorted_colors[:4]),
            "color_phrase": phrase,
        }

    @classmethod
    def analyze_object_color_from_file(
        cls,
        image_path: str,
        bbox: dict,
        target_dimensions: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Loads image, crops object bounding box, and extracts its genuine color signature.
        """
        try:
            p = Path(image_path)
            if not p.is_file():
                from app.config import get_settings
                alt_path = get_settings().UPLOAD_DIR / p.name
                if alt_path.is_file():
                    p = alt_path
                else:
                    return {
                        "color_phrase": None,
                        "error": "Image file from an earlier server session was cleared upon reboot. Please click 'Replace' or re-upload to analyze colors.",
                    }

            with Image.open(str(p)) as full_img:
                img_w, img_h = full_img.size

                x_min = float(bbox.get("x_min", 0))
                y_min = float(bbox.get("y_min", 0))
                x_max = float(bbox.get("x_max", img_w))
                y_max = float(bbox.get("y_max", img_h))

                # If bbox coordinates were scaled to a different target dimension, normalize to actual image size
                if target_dimensions and target_dimensions[0] > 0 and target_dimensions[1] > 0:
                    scale_x = img_w / target_dimensions[0]
                    scale_y = img_h / target_dimensions[1]
                    x_min *= scale_x
                    y_min *= scale_y
                    x_max *= scale_x
                    y_max *= scale_y

                # Clamp to image boundaries
                x_min = max(0, min(img_w - 1, int(x_min)))
                y_min = max(0, min(img_h - 1, int(y_min)))
                x_max = max(x_min + 1, min(img_w, int(x_max)))
                y_max = max(y_min + 1, min(img_h, int(y_max)))

                crop = full_img.crop((x_min, y_min, x_max, y_max))
                return cls.analyze_crop_colors(crop)
        except Exception as e:
            logger.warning(f"Color analysis exception: {e}")
            return {"color_phrase": "indeterminate", "error": str(e)}


_analyzer_instance: Optional[ObjectColorAnalyzer] = None


def get_color_analyzer() -> ObjectColorAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ObjectColorAnalyzer()
    return _analyzer_instance
