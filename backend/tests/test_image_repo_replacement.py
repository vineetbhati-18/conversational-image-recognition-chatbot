from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.repositories.image_repo import ImageRepository


@pytest.mark.asyncio
async def test_replace_detected_objects():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()

    image_id = uuid4()
    car_id = uuid4()
    person_id = uuid4()

    detections = [
        {
            "class_name": "car",
            "confidence": 0.95,
            "id": str(car_id),
            "bbox": {
                "x_min": 10,
                "y_min": 20,
                "x_max": 100,
                "y_max": 120,
            },
        },
        {
            "class_name": "person",
            "confidence": 0.88,
            "id": str(person_id),
            "bbox": {
                "x_min": 30,
                "y_min": 40,
                "x_max": 80,
                "y_max": 150,
            },
        },
    ]

    result = await ImageRepository.replace_detected_objects(
        db,
        image_id=image_id,
        detections=detections,
    )

    assert len(result) == 2
    assert result[0].class_name == "car"
    assert result[1].class_name == "person"

    assert db.execute.await_count == 1

    delete_query = db.execute.await_args.args[0]
    assert delete_query.table.name == "detected_objects"
    assert delete_query.whereclause.left.name == "image_id"
    assert delete_query.whereclause.right.value == image_id

    assert db.add.call_count == 2

    assert result[0].id == car_id
    assert result[1].id == person_id

    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()

@pytest.mark.asyncio
async def test_replace_with_empty_detections():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()

    result = await ImageRepository.replace_detected_objects(
        db,
        image_id=uuid4(),
        detections=[],
    )

    assert result == []
    db.execute.assert_awaited_once()
    db.add.assert_not_called()
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_replace_rolls_back_on_failure():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock(side_effect=RuntimeError("Insert failed"))

    detections = [
        {
            "class_name": "car",
            "confidence": 0.95,
            "bbox": {
                "x_min": 10,
                "y_min": 20,
                "x_max": 100,
                "y_max": 120,
            },
        }
    ]

    with pytest.raises(RuntimeError, match="Insert failed"):
        await ImageRepository.replace_detected_objects(
            db,
            image_id=uuid4(),
            detections=detections,
        )

    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()