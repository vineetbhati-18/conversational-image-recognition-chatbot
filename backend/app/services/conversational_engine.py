from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from enum import Enum
import re
import logging

logger = logging.getLogger("bel_chatbot.conversational_engine")


class QuestionIntent(str, Enum):
    OBJECT_INVENTORY = "object_inventory"
    OBJECT_COUNT = "object_count"
    SPATIAL_LOCATION = "spatial_location"
    VISUAL_ATTRIBUTE = "visual_attribute"
    GENERAL = "general"


CLASS_SYNONYMS: Dict[str, List[str]] = {
    "car": ["car", "cars", "automobile", "automobiles", "sedan", "sedans", "auto", "vehicle", "vehicles"],
    "traffic light": ["traffic light", "traffic lights", "stoplight", "stoplights", "traffic signal", "traffic signals", "signal", "signals"],
    "truck": ["truck", "trucks", "pickup", "lorry", "lorries"],
    "bus": ["bus", "buses"],
    "person": ["person", "persons", "people", "pedestrian", "pedestrians", "human", "humans", "man", "men", "woman", "women"],
    "bicycle": ["bicycle", "bicycles", "bike", "bikes", "cyclist", "cyclists"],
    "motorcycle": ["motorcycle", "motorcycles", "motorbike", "motorbikes"],
    "airplane": ["airplane", "airplanes", "plane", "planes", "aircraft"],
    "tie": ["tie", "ties", "necktie", "neckties"],
    "train": ["train", "trains"],
    "boat": ["boat", "boats", "ship", "ships", "vessel", "vessels"],
    "dog": ["dog", "dogs", "puppy", "puppies", "canine"],
    "cat": ["cat", "cats", "kitten", "kittens", "feline"],
    "chair": ["chair", "chairs", "seat", "seats"],
    "bench": ["bench", "benches"],
    "fire hydrant": ["fire hydrant", "fire hydrants", "hydrant", "hydrants"],
    "stop sign": ["stop sign", "stop signs"],
}

CATEGORY_GROUPS: Dict[str, List[str]] = {
    "vehicle": ["car", "truck", "bus", "motorcycle", "bicycle"],
    "vehicles": ["car", "truck", "bus", "motorcycle", "bicycle"],
}

INVENTORY_TRIGGERS = [
    r"\bwhat objects?\b",
    r"\bwhich objects?\b",
    r"\bwhat.*detected\b",
    r"\bdetected objects?\b",
    r"\bwhat.*visible\b",
    r"\bwhat.*in (?:this|the) image\b",
    r"\bwhat do you see\b",
    r"\blist.*objects?\b",
    r"\bwhat categories\b",
    r"\bidentify.*objects?\b",
    r"\bwhat are the objects\b",
    r"\bwhat did you find\b",
    r"\bwhat.*found\b",
]

COUNT_TRIGGERS = [
    r"\bhow many\b",
    r"\bnumber of\b",
    r"\bcount\b",
    r"\btotal (?:number of )?objects?\b",
]

SPATIAL_TRIGGERS = [
    r"\bwhere (?:is|are|was|were)\b",
    r"\bwhere.*located\b",
    r"\bwhat is (?:on|in|at) the (?:left|right|center|middle|top|bottom)\b",
    r"\bwhich (?:side|part|sector|area|quadrant)\b",
    r"\blocation of\b",
    r"\bposition of\b",
]

ATTRIBUTE_TRIGGERS = [
    r"\bwhat color\b",
    r"\bwhich color\b",
    r"\bcolor of\b",
    r"\bwhat.*wearing\b",
    r"\bwhat.*doing\b",
    r"\bwhat.*look like\b",
    r"\bweather\b",
    r"\btime of day\b",
    r"\bday or night\b",
    r"\bsetting\b",
    r"\bbackground\b",
    r"\benvironment\b",
    r"\bmake\b",
    r"\bbrand\b",
    r"\bmodel\b",
    r"\bdescription\b",
    r"\bdescribe\b",
]


class DialogueTurn:
    """Represents a single conversational exchange."""
    def __init__(self, sender_type: str, content: str, metadata: Optional[dict] = None):
        self.sender_type = sender_type
        self.content = content
        self.metadata = metadata or {}


class ConversationalContextManager:
    """
    Genuine multi-turn conversational memory manager.
    Tracks dialogue turns, resolves entity references, and grounds queries
    in visual and conversational history.
    """

    def __init__(self, max_history_window: int = 10):
        self.max_history_window = max_history_window

    def build_history_window(self, messages: List[Any]) -> List[DialogueTurn]:
        turns = []
        for msg in messages[-self.max_history_window:]:
            sender = getattr(msg, "sender_type", None) or msg.get("sender_type")
            content = getattr(msg, "content", None) or msg.get("content")
            meta = getattr(msg, "metadata_payload", None) or getattr(msg, "metadata", {})
            if sender in ("user", "assistant"):
                turns.append(DialogueTurn(sender, content, meta))
        return turns

    @staticmethod
    def normalize_class_name(word: str) -> Optional[str]:
        w = word.lower().strip()
        for canonical, syns in CLASS_SYNONYMS.items():
            if w in syns:
                return canonical
        for canonical in CLASS_SYNONYMS.keys():
            if w == canonical or w == f"{canonical}s" or w == f"{canonical}es":
                return canonical
        return None

    @classmethod
    def match_target_class_or_group(cls, text: str) -> Tuple[Optional[str], Optional[List[str]]]:
        t = text.lower()
        # Check category groups first (e.g. vehicle)
        for group_name, members in CATEGORY_GROUPS.items():
            pattern = r"\b" + group_name + r"\b"
            if re.search(pattern, t):
                return group_name, members

        # Check multi-word classes first (e.g. traffic light, fire hydrant)
        for canonical, syns in CLASS_SYNONYMS.items():
            for syn in sorted(syns, key=len, reverse=True):
                if " " in syn and re.search(r"\b" + re.escape(syn) + r"\b", t):
                    return canonical, [canonical]

        # Check single-word classes
        words = re.findall(r"\b[a-zA-Z_-]+\b", t)
        for w in words:
            canon = cls.normalize_class_name(w)
            if canon:
                return canon, [canon]

        return None, None

    def resolve_pronouns_and_coreference(
        self,
        current_query: str,
        dialogue_history: List[DialogueTurn],
        active_detected_objects: List[dict],
    ) -> str:
        intent, resolved, _, _, _, _, _ = self.classify_and_resolve(
            current_query, dialogue_history, active_detected_objects
        )
        return resolved

    def classify_and_resolve(
        self,
        current_query: str,
        dialogue_history: List[DialogueTurn],
        active_detected_objects: List[dict],
    ) -> Tuple[QuestionIntent, str, Optional[str], Optional[List[str]], Optional[str], Optional[float], bool]:
        """
        Classifies intent, parses confidence threshold from query if present,
        and resolves pronouns/coreferences.
        Returns:
            (intent, resolved_query, target_class, matched_classes, spatial_target, explicit_threshold, is_follow_up)
        """
        q = current_query.strip()
        q_lower = q.lower()

        # 1. Parse explicit threshold in text if present (e.g. "at 40% confidence", "confidence 0.5")
        explicit_threshold = None
        pct_match = re.search(r"(\d{1,2})\s*%\s*(?:confidence|conf)?", q_lower)
        if pct_match:
            explicit_threshold = float(pct_match.group(1)) / 100.0
        else:
            dec_match = re.search(r"(?:confidence|threshold)\s*(?:of|at|above|>=|>)?\s*(0\.\d+)", q_lower)
            if dec_match:
                explicit_threshold = float(dec_match.group(1))

        # Check for coreference pronouns: "it", "they", "them", "that vehicle", "this", "that"
        pronouns = ["it", "they", "them", "that", "this", "these", "those"]
        words = re.findall(r"\b\w+\b", q_lower)
        has_pronoun = any(p in words for p in pronouns) or "that vehicle" in q_lower or "the vehicle" in q_lower
        is_follow_up = bool(dialogue_history) and (has_pronoun or any(w in words for w in ["also", "and", "too"]))

        # Identify recent entity from dialogue history if follow-up
        referenced_class = None
        referenced_group = None
        if dialogue_history and has_pronoun:
            for turn in reversed(dialogue_history):
                # Check metadata first
                if turn.metadata and turn.metadata.get("primary_subject"):
                    sub = turn.metadata["primary_subject"]
                    if sub == "detected objects":
                        referenced_class = "detected objects"
                        referenced_group = None
                        break
                    if sub in CLASS_SYNONYMS or sub in CATEGORY_GROUPS:
                        referenced_class = sub
                        referenced_group = CATEGORY_GROUPS.get(sub, [sub])
                        break
                # Check turn text
                cand_class, cand_group = self.match_target_class_or_group(turn.content)
                if cand_class:
                    referenced_class = cand_class
                    referenced_group = cand_group
                    break

        # 2. Classify Intent
        # A. Spatial Query
        spatial_match = None
        for direction in ["top-left", "top-right", "top-center", "bottom-left", "bottom-right", "bottom-center", "middle-left", "middle-right", "center", "middle", "left", "right", "top", "bottom"]:
            if re.search(r"\b" + direction + r"\b", q_lower):
                spatial_match = direction
                break

        is_spatial_question = any(re.search(pat, q_lower) for pat in SPATIAL_TRIGGERS) or (
            spatial_match and any(w in words for w in ["what", "which", "where", "show"])
        )

        if is_spatial_question:
            target_class, matched_group = self.match_target_class_or_group(q_lower)
            if not target_class and referenced_class:
                if referenced_class == "detected objects":
                    target_class = None
                    matched_group = None
                else:
                    target_class = referenced_class
                    matched_group = referenced_group
            resolved = q
            if target_class and has_pronoun:
                resolved = re.sub(r"\b(it|they|them|that|this)\b", f"the {target_class}", q, flags=re.IGNORECASE)
            return QuestionIntent.SPATIAL_LOCATION, resolved, target_class, matched_group, spatial_match, explicit_threshold, is_follow_up

        # B. Count Query
        is_count_question = any(re.search(pat, q_lower) for pat in COUNT_TRIGGERS)
        if is_count_question:
            target_class, matched_group = self.match_target_class_or_group(q_lower)
            if not target_class and referenced_class:
                target_class = referenced_class
                matched_group = referenced_group
            resolved = q
            if target_class and has_pronoun:
                resolved = re.sub(r"\b(it|they|them|that|this)\b", f"{target_class}", q, flags=re.IGNORECASE)
            return QuestionIntent.OBJECT_COUNT, resolved, target_class, matched_group, None, explicit_threshold, is_follow_up

        # C. Object Inventory / Identification Query
        is_inventory_question = any(re.search(pat, q_lower) for pat in INVENTORY_TRIGGERS)
        if is_inventory_question:
            return QuestionIntent.OBJECT_INVENTORY, q, None, None, None, explicit_threshold, is_follow_up

        # D. Visual Attribute Query (Color, Appearance, Weather, Action)
        is_attribute_question = any(re.search(pat, q_lower) for pat in ATTRIBUTE_TRIGGERS)
        if is_attribute_question:
            target_class, matched_group = self.match_target_class_or_group(q_lower)
            if not target_class and referenced_class:
                target_class = referenced_class
                matched_group = referenced_group
            resolved = q
            if target_class and has_pronoun:
                resolved = re.sub(r"\b(it|that|this)\b", f"the {target_class}", q, flags=re.IGNORECASE)
                resolved = re.sub(r"\b(they|them)\b", f"the {target_class}s", resolved, flags=re.IGNORECASE)
            return QuestionIntent.VISUAL_ATTRIBUTE, resolved, target_class, matched_group, None, explicit_threshold, is_follow_up

        # E. General Fallback
        target_class, matched_group = self.match_target_class_or_group(q_lower)
        return QuestionIntent.GENERAL, q, target_class, matched_group, None, explicit_threshold, is_follow_up


_context_manager_instance: Optional[ConversationalContextManager] = None


def get_context_manager() -> ConversationalContextManager:
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ConversationalContextManager()
    return _context_manager_instance


class MultiModalFusionEngine:
    """
    Synthesizes YOLO spatial detections, BLIP visual question answering,
    and multi-turn dialogue history into coherent, natural responses.
    """

    def __init__(self, context_manager: Optional[ConversationalContextManager] = None):
        self.context_manager = context_manager or get_context_manager()

    def generate_fused_response(
        self,
        query: str,
        vqa_answer: str,
        yolo_detections: List[dict],
        dialogue_history: List[DialogueTurn],
        conf_threshold: float = 0.40,
        vqa_error: Optional[str] = None,
    ) -> dict:
        """
        Fuses multimodal sources into a grammatically structured, context-aware answer.
        """
        # 1. Classify intent and resolve coreferences
        (
            intent,
            resolved_query,
            target_class,
            matched_classes,
            spatial_direction,
            explicit_threshold,
            is_follow_up,
        ) = self.context_manager.classify_and_resolve(
            query, dialogue_history, yolo_detections
        )

        effective_conf = explicit_threshold if explicit_threshold is not None else conf_threshold
        threshold_pct = int(round(effective_conf * 100))

        # Build class counts and visible detections
        total_detections = len(yolo_detections)
        all_by_class: Dict[str, List[float]] = {}
        for obj in yolo_detections:
            cname = obj.get("class_name", "object")
            all_by_class.setdefault(cname, []).append(obj.get("confidence", 1.0))

        visible_by_class: Dict[str, int] = {}
        filtered_by_class: Dict[str, int] = {}
        for cname, confs in all_by_class.items():
            v_cnt = sum(1 for c in confs if c >= effective_conf)
            f_cnt = len(confs) - v_cnt
            if v_cnt > 0:
                visible_by_class[cname] = v_cnt
            if f_cnt > 0:
                filtered_by_class[cname] = f_cnt

        total_visible = sum(visible_by_class.values())
        detected_classes = list(visible_by_class.keys()) or list(all_by_class.keys())

        response = ""
        primary_subject = target_class

        # ========================================================
        # ROUTE 1: OBJECT INVENTORY ("What objects are detected?")
        # ========================================================
        if intent == QuestionIntent.OBJECT_INVENTORY:
            primary_subject = "detected objects"
            if total_detections == 0:
                response = "No objects were detected in this image."
            elif total_visible == 0:
                filtered_items = [f"{cnt} {cls}" if cnt == 1 else f"{cnt} {cls}s" for cls, cnt in filtered_by_class.items()]
                filtered_phrase = ", ".join(filtered_items)
                response = f"No objects met the {threshold_pct}% confidence threshold ({total_detections} total detected below threshold: {filtered_phrase})."
            else:
                sorted_visible = sorted(visible_by_class.items(), key=lambda x: x[1], reverse=True)
                parts = [f"{cnt} {cls}" if cnt == 1 else f"{cnt} {cls}s" if not cls.endswith("s") else f"{cnt} {cls}" for cls, cnt in sorted_visible]
                items_phrase = ", ".join(parts[:-1]) + f" and {parts[-1]}" if len(parts) > 1 else parts[0]
                category_count = len(visible_by_class)
                cat_word = "category" if category_count == 1 else "categories"

                if filtered_by_class:
                    filtered_parts = [f"{cnt} {cls}" if cnt == 1 else f"{cnt} {cls}s" for cls, cnt in filtered_by_class.items()]
                    filtered_phrase = ", ".join(filtered_parts)
                    response = (
                        f"I detected {total_visible} visible objects across {category_count} {cat_word} at {threshold_pct}% confidence: "
                        f"{items_phrase} ({total_detections} total detections found prior to filtering, including {filtered_phrase} below threshold)."
                    )
                else:
                    response = (
                        f"I detected {total_visible} visible objects across {category_count} {cat_word} at {threshold_pct}% confidence: "
                        f"{items_phrase} ({total_detections} total detections found)."
                    )

        # ========================================================
        # ROUTE 2: OBJECT COUNT ("How many cars?")
        # ========================================================
        elif intent == QuestionIntent.OBJECT_COUNT:
            if not target_class or target_class in ["object", "objects"]:
                # Generic total count
                return self.generate_fused_response(
                    "What objects are detected?", vqa_answer, yolo_detections, dialogue_history, conf_threshold
                )

            classes_to_match = set(matched_classes or [target_class])
            matching_objs = [d for d in yolo_detections if d.get("class_name") in classes_to_match]
            visible_matches = [d for d in matching_objs if d.get("confidence", 1.0) >= effective_conf]
            below_matches = [d for d in matching_objs if d.get("confidence", 1.0) < effective_conf]

            v_count = len(visible_matches)
            b_count = len(below_matches)
            t_count = len(matching_objs)

            label = target_class
            plural_label = f"{label}s" if not label.endswith("s") and label != "person" else "persons" if label == "person" else label

            if v_count > 0:
                name_str = label if v_count == 1 else plural_label
                if b_count > 0:
                    response = f"I detected {v_count} {name_str} in the image at {threshold_pct}% confidence ({t_count} total detected prior to filtering)."
                else:
                    response = f"I detected {v_count} {name_str} in the image at {threshold_pct}% confidence."
            elif b_count > 0:
                name_str = label if b_count == 1 else plural_label
                response = f"I detected 0 {plural_label} at {threshold_pct}% confidence ({b_count} {name_str} detected at lower confidence below the threshold)."
            else:
                response = f"I did not detect any {plural_label} in the image at the current confidence threshold."

        # ========================================================
        # ROUTE 3: SPATIAL LOCATION ("Where are the cars?")
        # ========================================================
        elif intent == QuestionIntent.SPATIAL_LOCATION:
            visible_detections = [d for d in yolo_detections if d.get("confidence", 1.0) >= effective_conf]

            # Case A: User asked about a specific sector (e.g. "What is on the left?")
            if spatial_direction:
                sector_dir = spatial_direction.lower()
                matched_in_sector = [
                    d for d in visible_detections
                    if sector_dir in d.get("spatial_sector", "").lower()
                ]
                if matched_in_sector:
                    counts: Dict[str, int] = {}
                    for d in matched_in_sector:
                        c = d.get("class_name", "object")
                        counts[c] = counts.get(c, 0) + 1
                    parts = [f"{cnt} {cls}" if cnt == 1 else f"{cnt} {cls}s" if not cls.endswith("s") else f"{cnt} {cls}" for cls, cnt in counts.items()]
                    items_str = ", ".join(parts[:-1]) + f" and {parts[-1]}" if len(parts) > 1 else parts[0]
                    response = f"In the {sector_dir} area of the image at {threshold_pct}% confidence, I identified: {items_str}."
                else:
                    response = f"No objects were detected in the {sector_dir} sector of the image at {threshold_pct}% confidence."

            # Case B: Specific target class location (e.g. "Where is the bus?")
            elif target_class and target_class not in ["object", "objects", "they", "it", "them"]:
                classes_to_match = set(matched_classes or [target_class])
                matching_objs = [d for d in visible_detections if d.get("class_name") in classes_to_match]

                if not matching_objs:
                    below_objs = [d for d in yolo_detections if d.get("class_name") in classes_to_match and d.get("confidence", 1.0) < effective_conf]
                    if below_objs:
                        response = f"No {target_class}s meet the {threshold_pct}% confidence threshold ({len(below_objs)} detected below threshold)."
                    else:
                        response = f"I did not detect any {target_class}s in the image."
                else:
                    sector_counts: Dict[str, int] = {}
                    for d in matching_objs:
                        s = d.get("spatial_sector", "center")
                        sector_counts[s] = sector_counts.get(s, 0) + 1

                    plural = f"{target_class}s" if not target_class.endswith("s") and target_class != "person" else "persons" if target_class == "person" else target_class
                    count_str = f"The {len(matching_objs)} {plural}" if len(matching_objs) > 1 else f"The {target_class}"

                    if len(matching_objs) == 1:
                        bbox = matching_objs[0].get("bbox", {})
                        sec = matching_objs[0].get("spatial_sector", "center")
                        coord_str = f" (coordinates: x=[{bbox.get('x_min', 0):.0f}, {bbox.get('x_max', 0):.0f}], y=[{bbox.get('y_min', 0):.0f}, {bbox.get('y_max', 0):.0f}])" if bbox else ""
                        response = f"{count_str} is located in the {sec} sector of the image{coord_str} with {matching_objs[0].get('confidence', 0)*100:.1f}% confidence."
                    else:
                        sector_parts = [f"{sec} ({cnt})" if cnt > 1 else f"{sec}" for sec, cnt in sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)]
                        sec_phrase = ", ".join(sector_parts[:-1]) + f" and {sector_parts[-1]}" if len(sector_parts) > 1 else sector_parts[0]
                        response = f"{count_str} are located primarily in the {sec_phrase} sectors of the image."

            # Case C: Generic "Where are they located?" across all visible objects
            else:
                by_class: Dict[str, List[str]] = {}
                for d in visible_detections:
                    c = d.get("class_name", "object")
                    s = d.get("spatial_sector", "center")
                    by_class.setdefault(c, []).append(s)

                if not by_class:
                    response = "No objects were detected above the confidence threshold to report spatial locations."
                else:
                    class_locs = []
                    for c, sectors in by_class.items():
                        uniq_secs = list(dict.fromkeys(sectors))
                        sec_str = ", ".join(uniq_secs[:3])
                        plural = f"{c}s" if not c.endswith("s") and c != "person" else "persons" if c == "person" else c
                        class_locs.append(f"{len(sectors)} {plural} positioned in the {sec_str} areas")
                    loc_summary = "; ".join(class_locs)
                    response = f"The detected objects are located across the image: {loc_summary}."

        # ========================================================
        # ROUTE 4: VISUAL ATTRIBUTES & SCENE DESCRIPTIONS (VQA)
        # ========================================================
        elif intent == QuestionIntent.VISUAL_ATTRIBUTE:
            clean_vqa = (vqa_answer or "").strip()
            if clean_vqa:
                # Format naturally
                if target_class:
                    response = f"Visual analysis indicates that the {target_class} is {clean_vqa}."
                else:
                    response = f"Visual analysis indicates: {clean_vqa.capitalize()}."
            elif vqa_error:
                response = f"Visual question answering is currently unavailable: {vqa_error}"
            else:
                response = (
                    "Visual question answering is currently unavailable because the external inference service "
                    "(HF_TOKEN) is unconfigured or unreachable. You can continue asking questions about detected "
                    "objects, categories, counts, and spatial positions."
                )

        # ========================================================
        # ROUTE 5: GENERAL CONVERSATION
        # ========================================================
        else:
            clean_vqa = (vqa_answer or "").strip()
            if clean_vqa:
                response = f"Visual analysis indicates: {clean_vqa.capitalize()}."
            elif total_detections > 0:
                response = f"The image contains {total_visible} visible detected objects at {threshold_pct}% confidence."
            elif vqa_error:
                response = f"Visual analysis is currently unavailable: {vqa_error}"
            else:
                response = (
                    "Visual analysis is currently operating in low-memory cloud mode. "
                    "You can ask questions about detected objects, counts, and spatial positions."
                )

        # Add contextual follow-up continuation if prior dialogue exists and question was a follow-up
        if is_follow_up and not response.startswith("Regarding your follow-up:"):
            response = f"Regarding your follow-up: {response}"

        return {
            "content": response,
            "vqa_answer": vqa_answer,
            "detected_classes": detected_classes,
            "total_objects": total_detections,
            "primary_subject": primary_subject,
            "intent": intent.value,
        }


_fusion_engine_instance: Optional[MultiModalFusionEngine] = None


def get_fusion_engine() -> MultiModalFusionEngine:
    global _fusion_engine_instance
    if _fusion_engine_instance is None:
        _fusion_engine_instance = MultiModalFusionEngine()
    return _fusion_engine_instance
