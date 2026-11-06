from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime
import time

from app.core.database import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.image import ImageModel
from app.schemas.chat import ChatMessageRequest, MessageResponse
from app.services.blip_service import get_blip_service
from app.services.conversational_engine import get_context_manager, get_fusion_engine
from app.core.exceptions import EntityNotFoundError

router = APIRouter()


@router.post("/message", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def send_chat_message(
    payload: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Context-Aware Multimodal Chatbot Completion:
    1. Loads dialogue history from PostgreSQL.
    2. Resolves pronouns & coreferences across dialogue turns.
    3. Runs BLIP VQA on active image if present.
    4. Fuses YOLO telemetry and BLIP answer into coherent natural response.
    5. Saves dialogue exchange to PostgreSQL.
    """
    start_time = time.perf_counter()

    # 1. Fetch Session
    session_query = (
        select(SessionModel)
        .where(SessionModel.id == payload.session_id)
        .options(selectinload(SessionModel.messages))
    )
    result = await db.execute(session_query)
    session = result.scalar_one_or_none()

    if not session:
        # Create new session if does not exist
        session = SessionModel(id=payload.session_id, title=payload.content[:40])
        db.add(session)
        await db.commit()
        session_messages = []
    else:
        session_messages = session.messages

    # 2. Persist User Message
    user_msg = MessageModel(
        session_id=payload.session_id,
        image_id=payload.image_id,
        sender_type="user",
        content=payload.content,
    )
    db.add(user_msg)
    await db.commit()

    # 3. Context & Multimodal Processing
    context_mgr = get_context_manager()
    fusion_engine = get_fusion_engine()

    history_turns = context_mgr.build_history_window(session_messages)

    yolo_detections = []
    vqa_answer = ""
    vqa_latency = 0.0

    if payload.image_id:
        img_query = (
            select(ImageModel)
            .where(ImageModel.id == payload.image_id)
            .options(selectinload(ImageModel.detected_objects))
        )
        img_res = await db.execute(img_query)
        image = img_res.scalar_one_or_none()

        if image:
            # Map DB detected objects to dicts for fusion engine
            yolo_detections = [
                {
                    "class_name": o.class_name,
                    "confidence": o.confidence_score,
                    "spatial_sector": "center",
                    "bbox": {
                        "x_min": o.bbox_x_min,
                        "y_min": o.bbox_y_min,
                        "x_max": o.bbox_x_max,
                        "y_max": o.bbox_y_max,
                    },
                }
                for o in image.detected_objects
            ]

            # Resolve coreference
            resolved_query = context_mgr.resolve_pronouns_and_coreference(
                payload.content, history_turns, yolo_detections
            )

            # Run BLIP VQA
            blip = get_blip_service()
            vqa_res = blip.answer_question(image.storage_path, resolved_query)
            vqa_answer = vqa_res["answer"]
            vqa_latency = vqa_res["latency_ms"]

    # 4. Generate Synthesized Response via Fusion Engine
    fused = fusion_engine.generate_fused_response(
        query=payload.content,
        vqa_answer=vqa_answer,
        yolo_detections=yolo_detections,
        dialogue_history=history_turns,
    )

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 5. Persist Assistant Response
    meta_payload = {
        "vqa_mode": bool(payload.image_id),
        "vqa_answer": vqa_answer,
        "detected_classes": fused["detected_classes"],
        "latency_ms": total_latency_ms,
        "vqa_latency_ms": vqa_latency,
    }

    assistant_msg = MessageModel(
        session_id=payload.session_id,
        image_id=payload.image_id,
        sender_type="assistant",
        content=fused["content"],
        metadata_payload=meta_payload,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return MessageResponse(
        id=assistant_msg.id,
        session_id=assistant_msg.session_id,
        image_id=assistant_msg.image_id,
        sender_type="assistant",
        content=assistant_msg.content,
        metadata=meta_payload,
        created_at=assistant_msg.created_at,
    )
