from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime
import time

from app.core.database import get_db
from app.repositories.session_repo import SessionRepository
from app.repositories.image_repo import ImageRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.chat import ChatMessageRequest, MessageResponse
from app.services.blip_service import get_blip_service
from app.services.yolo_service import YOLOService
from app.services.conversational_engine import get_context_manager, get_fusion_engine, QuestionIntent
from app.core.exceptions import EntityNotFoundError

router = APIRouter()


@router.post("/message", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def send_chat_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Context-Aware Multimodal Chatbot Completion:
    1. Loads dialogue history from PostgreSQL via SessionRepository.
    2. Resolves pronouns & coreferences across dialogue turns.
    3. Runs BLIP VQA on active image if present.
    4. Fuses YOLO telemetry and BLIP answer into coherent natural response.
    5. Saves dialogue exchange to PostgreSQL via MessageRepository.
    """
    start_time = time.perf_counter()

    # 1. Fetch or create Session
    session = await SessionRepository.get_by_id(db, payload.session_id, load_relations=True)
    if not session:
        session = await SessionRepository.create(
            db, title=payload.content[:40], session_id=payload.session_id
        )
        session_messages = []
    else:
        session_messages = session.messages

    # 2. Persist User Message
    await MessageRepository.create(
        db,
        session_id=payload.session_id,
        sender_type="user",
        content=payload.content,
        image_id=payload.image_id,
    )

    # 3. Context & Multimodal Processing
    context_mgr = get_context_manager()
    fusion_engine = get_fusion_engine()

    history_turns = context_mgr.build_history_window(session_messages)

    yolo_detections = []
    vqa_answer = ""
    vqa_latency = 0.0
    conf_threshold = payload.confidence_threshold if payload.confidence_threshold is not None else 0.40

    # Resolve target image: use explicit image_id, or fallback to session's latest image
    target_image_id = payload.image_id
    if not target_image_id and session:
        # Eagerly load images if not already loaded
        images = getattr(session, "images", None)
        if images:
            # Pick the most recently created image in this session
            sorted_imgs = sorted(images, key=lambda img: img.created_at, reverse=True)
            target_image_id = sorted_imgs[0].id

    if target_image_id:
        image = await ImageRepository.get_by_id(db, target_image_id, load_objects=True)
        if image:
            img_w = image.width or 640
            img_h = image.height or 480
            yolo_detections = [
                {
                    "class_name": o.class_name,
                    "confidence": o.confidence_score,
                    "spatial_sector": YOLOService.calculate_spatial_position(
                        o.bbox_x_min, o.bbox_y_min, o.bbox_x_max, o.bbox_y_max, img_w, img_h
                    ),
                    "bbox": {
                        "x_min": o.bbox_x_min,
                        "y_min": o.bbox_y_min,
                        "x_max": o.bbox_x_max,
                        "y_max": o.bbox_y_max,
                    },
                }
                for o in image.detected_objects
            ]

            (
                intent,
                resolved_query,
                target_class,
                matched_classes,
                spatial_direction,
                explicit_threshold,
                is_follow_up,
            ) = context_mgr.classify_and_resolve(
                payload.content, history_turns, yolo_detections
            )

            # Route object identification, counting, and spatial queries directly to structured YOLO data.
            # Only execute external VQA for visual attributes, color, appearance, and scene descriptions.
            if intent in (QuestionIntent.VISUAL_ATTRIBUTE, QuestionIntent.GENERAL):
                import asyncio
                blip = get_blip_service()
                vqa_res = await asyncio.to_thread(blip.answer_question, image.storage_path, resolved_query)
                vqa_answer = vqa_res.get("answer") or ""
                vqa_error = vqa_res.get("error")
                vqa_latency = vqa_res.get("latency_ms", 0.0)

                # Color analysis: If external VQA is unconfigured or failed, extract genuine color signature directly from pixel data
                is_color_q = any(w in payload.content.lower() for w in ["color", "colour", "shade", "paint", "tint"])
                if is_color_q and target_class and not vqa_answer:
                    classes_to_match = set(matched_classes or [target_class])
                    matching_objs = [d for d in yolo_detections if d.get("class_name") in classes_to_match]
                    if matching_objs:
                        from app.services.color_analyzer import get_color_analyzer
                        analyzer = get_color_analyzer()
                        color_res = analyzer.analyze_object_color_from_file(
                            image.storage_path,
                            matching_objs[0]["bbox"],
                            target_dimensions=(img_w, img_h)
                        )
                        if color_res and color_res.get("color_phrase") and color_res["color_phrase"] not in ("unknown", "indeterminate"):
                            vqa_answer = color_res["color_phrase"]
                            vqa_error = None
                        elif color_res.get("error"):
                            vqa_error = color_res["error"]

    # 4. Generate Synthesized Response via Fusion Engine
    fused = fusion_engine.generate_fused_response(
        query=payload.content,
        vqa_answer=vqa_answer,
        yolo_detections=yolo_detections,
        dialogue_history=history_turns,
        conf_threshold=conf_threshold,
        vqa_error=vqa_error if "vqa_error" in locals() else None,
    )

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    meta_payload = {
        "vqa_mode": bool(vqa_answer),
        "vqa_answer": vqa_answer,
        "detected_classes": fused["detected_classes"],
        "primary_subject": fused.get("primary_subject"),
        "intent": fused.get("intent"),
        "latency_ms": total_latency_ms,
        "vqa_latency_ms": vqa_latency,
        "confidence_threshold": conf_threshold,
    }

    # 5. Persist Assistant Response via Repository
    assistant_msg = await MessageRepository.create(
        db,
        session_id=payload.session_id,
        sender_type="assistant",
        content=fused["content"],
        image_id=payload.image_id,
        metadata=meta_payload,
    )

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        image_id=assistant_msg.image_id,
        sender_type="assistant",
        content=assistant_msg.content,
        metadata=meta_payload,
        created_at=assistant_msg.created_at,
    )
