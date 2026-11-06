from typing import List, Dict, Any, Optional
from uuid import UUID
import re
import logging

logger = logging.getLogger("bel_chatbot.context_manager")


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
        """
        Extracts recent dialogue turns up to max_history_window.
        """
        turns = []
        for msg in messages[-self.max_history_window:]:
            sender = getattr(msg, "sender_type", None) or msg.get("sender_type")
            content = getattr(msg, "content", None) or msg.get("content")
            meta = getattr(msg, "metadata_payload", None) or getattr(msg, "metadata", {})
            if sender in ("user", "assistant"):
                turns.append(DialogueTurn(sender, content, meta))
        return turns

    def resolve_pronouns_and_coreference(
        self,
        current_query: str,
        dialogue_history: List[DialogueTurn],
        active_detected_objects: List[dict],
    ) -> str:
        """
        Resolves ambiguous pronouns ('it', 'they', 'the vehicle', 'the person')
        by inspecting the immediate dialogue history and detected objects.
        """
        query_lower = current_query.lower()
        pronouns = ["it", "this", "that", "these", "them", "they"]

        # Check if the query contains a coreference pronoun
        words = re.findall(r"\b\w+\b", query_lower)
        has_pronoun = any(p in words for p in pronouns)

        if not has_pronoun or not dialogue_history:
            return current_query

        # Find the most recently discussed object class in recent assistant or user messages
        last_turn = dialogue_history[-1]
        referenced_class = None

        for obj in active_detected_objects:
            cname = obj.get("class_name", "").lower()
            if cname in last_turn.content.lower():
                referenced_class = cname
                break

        if referenced_class:
            logger.info(f"Resolved coreference pronoun in '{current_query}' to entity: '{referenced_class}'")
            # If query is short like "What color is it?", expand to "What color is the {referenced_class}?"
            expanded = re.sub(r"\b(it|this|that)\b", f"the {referenced_class}", current_query, flags=re.IGNORECASE)
            return expanded

        return current_query

    def extract_recent_entities(self, dialogue_history: List[DialogueTurn]) -> List[str]:
        """
        Extracts entities and subjects tracked in previous dialogue turns.
        """
        entities = []
        for turn in dialogue_history:
            if turn.metadata and "detected_classes" in turn.metadata:
                entities.extend(turn.metadata["detected_classes"])
        return list(set(entities))


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
    ) -> dict:
        """
        Fuses multimodal sources into a grammatically structured, context-aware answer.
        """
        query_lower = query.lower()
        clean_vqa = (vqa_answer or "").strip()

        # Class counts from YOLO
        class_counts: Dict[str, int] = {}
        sector_map: Dict[str, List[str]] = {}
        for obj in yolo_detections:
            cname = obj.get("class_name", "object")
            class_counts[cname] = class_counts.get(cname, 0) + 1
            sector = obj.get("spatial_sector", "middle")
            sector_map.setdefault(sector, []).append(cname)

        total_objects = len(yolo_detections)
        classes_summary = ", ".join([f"{count} {cls}" if count == 1 else f"{count} {cls}s" for cls, count in class_counts.items()])

        # Pattern 1: Count queries ("how many", "count")
        if any(w in query_lower for w in ["how many", "number of", "count"]):
            target_class = None
            for cls in class_counts.keys():
                if cls in query_lower:
                    target_class = cls
                    break

            if target_class:
                cnt = class_counts[target_class]
                plural = f"{target_class}s" if cnt != 1 else target_class
                response = f"I detected {cnt} {plural} in the image."
            elif total_objects > 0:
                response = f"Based on deep-learning object detection, there are {total_objects} total objects visible: {classes_summary}."
            else:
                response = f"I did not detect distinct countable objects for this category at the current confidence threshold."

        # Pattern 2: Spatial queries ("where is", "what is on the left", "what is in the center")
        elif any(loc in query_lower for loc in ["left", "right", "center", "middle", "top", "bottom"]):
            matched_sector = None
            for sector, items in sector_map.items():
                if any(part in query_lower for part in sector.split("-")):
                    matched_sector = (sector, items)
                    break

            if matched_sector:
                sec_name, items = matched_sector
                unique_items = ", ".join(set(items))
                response = f"In the {sec_name} of the image, I identified: {unique_items}."
            else:
                response = f"In that sector, visual inference identifies: {clean_vqa}."

        # Pattern 3: General / Color / State questions
        else:
            if clean_vqa:
                # Capitalize and make a full sentence if concise
                if len(clean_vqa.split()) <= 3:
                    if total_objects > 0:
                        first_class = list(class_counts.keys())[0]
                        response = f"The visual analysis indicates {clean_vqa} for the {first_class} in the scene."
                    else:
                        response = f"Visual analysis indicates: {clean_vqa.capitalize()}."
                else:
                    response = clean_vqa[0].upper() + clean_vqa[1:]
                    if not response.endswith("."):
                        response += "."
            elif total_objects > 0:
                response = f"The image contains {total_objects} detected objects: {classes_summary}."
            else:
                response = "I have inspected the image, but could not detect a definitive visual feature answering that specific query."

        # Add contextual follow-up continuity if prior dialogue exists
        if dialogue_history and len(dialogue_history) >= 2:
            last_user_query = dialogue_history[-2].content if dialogue_history[-2].sender_type == "user" else ""
            if last_user_query and any(p in query_lower for p in ["it", "that", "this", "also"]):
                response = f"Regarding your follow-up: {response}"

        return {
            "content": response,
            "vqa_answer": clean_vqa,
            "detected_classes": list(class_counts.keys()),
            "total_objects": total_objects,
        }


_fusion_engine_instance: Optional[MultiModalFusionEngine] = None


def get_fusion_engine() -> MultiModalFusionEngine:
    global _fusion_engine_instance
    if _fusion_engine_instance is None:
        _fusion_engine_instance = MultiModalFusionEngine()
    return _fusion_engine_instance
