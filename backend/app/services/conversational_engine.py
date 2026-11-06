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
