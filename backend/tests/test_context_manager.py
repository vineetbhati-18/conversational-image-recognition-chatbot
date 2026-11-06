import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.conversational_engine import ConversationalContextManager, DialogueTurn


def test_dialogue_history_window():
    mgr = ConversationalContextManager(max_history_window=3)
    raw_msgs = [
        {"sender_type": "user", "content": "Hello", "metadata": {}},
        {"sender_type": "assistant", "content": "Welcome", "metadata": {}},
        {"sender_type": "user", "content": "Question 1", "metadata": {}},
        {"sender_type": "assistant", "content": "Answer 1", "metadata": {}},
        {"sender_type": "user", "content": "Question 2", "metadata": {}},
    ]
    window = mgr.build_history_window(raw_msgs)
    assert len(window) == 3
    assert window[-1].content == "Question 2"


def test_coreference_resolution():
    mgr = ConversationalContextManager()
    history = [
        DialogueTurn("user", "Is there a truck in the scene?"),
        DialogueTurn("assistant", "Yes, a military truck was detected on the left side with 94% confidence."),
    ]
    detected_objects = [{"class_name": "truck"}, {"class_name": "car"}]

    query = "What color is it?"
    resolved = mgr.resolve_pronouns_and_coreference(query, history, detected_objects)
    assert "truck" in resolved.lower()
