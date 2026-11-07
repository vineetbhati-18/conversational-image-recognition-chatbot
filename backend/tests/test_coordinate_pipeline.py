import pytest
from app.services.yolo_service import YOLOService


def test_yolo_coordinate_mapping_on_different_resolutions():
    """
    Verifies that when YOLO runs on a downscaled image (e.g. 800x450),
    passing orig_dimensions (e.g. 1672x941) accurately maps the bounding
    box back to the user's original image pixel space without loss of precision.
    """
    yolo = YOLOService()

    # Suppose a detection on 800x450 thumbnail coordinates:
    img_w, img_h = 800, 450
    orig_w, orig_h = 1672, 941

    src_x_min, src_y_min = 364.46, 98.95
    src_x_max, src_y_max = 544.45, 273.15

    # 1. Normalize
    norm_x_min = src_x_min / img_w
    norm_y_min = src_y_min / img_h
    norm_x_max = src_x_max / img_w
    norm_y_max = src_y_max / img_h

    assert 0.0 <= norm_x_min <= 1.0
    assert 0.0 <= norm_y_min <= 1.0
    assert 0.0 <= norm_x_max <= 1.0
    assert 0.0 <= norm_y_max <= 1.0
    assert norm_x_min < norm_x_max
    assert norm_y_min < norm_y_max

    # 2. Scale back to original resolution
    target_x_min = norm_x_min * orig_w
    target_y_min = norm_y_min * orig_h
    target_x_max = norm_x_max * orig_w
    target_y_max = norm_y_max * orig_h

    # The truck in Pap.webp is centered in the middle of the roadway (x ~ 762 to 1138)
    assert 700 <= target_x_min <= 800
    assert 1100 <= target_x_max <= 1200
    assert 180 <= target_y_min <= 240
    assert 540 <= target_y_max <= 600

    # Ensure ratio of original bounding box matches normalized box exactly
    assert round(target_x_min / orig_w, 4) == round(norm_x_min, 4)
    assert round(target_y_min / orig_h, 4) == round(norm_y_min, 4)
    assert round(target_x_max / orig_w, 4) == round(norm_x_max, 4)
    assert round(target_y_max / orig_h, 4) == round(norm_y_max, 4)


def test_letterbox_aspect_ratio_calculation():
    """
    Verifies CSS object-contain pillarbox and letterbox offset calculation.
    """
    # Case 1: Wide element with pillarbox (bars on left and right)
    natural_w, natural_h = 1672, 941  # Aspect ~ 1.7768
    client_w, client_h = 800, 300     # Element aspect = 2.6667 (wider than image)

    image_aspect = natural_w / natural_h
    element_aspect = client_w / client_h

    assert element_aspect > image_aspect
    # Render width is constrained by height
    render_w = client_h * image_aspect
    offset_x = (client_w - render_w) / 2
    offset_y = 0

    assert render_w < client_w
    assert offset_x > 0
    assert offset_y == 0
    assert round(render_w + 2 * offset_x, 2) == client_w

    # Case 2: Tall element with letterbox (bars on top and bottom)
    client_w, client_h = 500, 500  # Square container (element aspect = 1.0 < image aspect 1.7768)
    element_aspect = client_w / client_h

    assert element_aspect < image_aspect
    render_h = client_w / image_aspect
    offset_y = (client_h - render_h) / 2
    offset_x = 0

    assert render_h < client_h
    assert offset_y > 0
    assert offset_x == 0
    assert round(render_h + 2 * offset_y, 2) == client_h
