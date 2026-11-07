/**
 * Canvas & Bounding Box Utilities for YOLO Detection
 */

// Class category color mappings
export const CLASS_COLORS = {
  // Military & Vehicles
  truck: { stroke: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)', text: '#cffafe' },
  car: { stroke: '#3b82f6', bg: 'rgba(59, 130, 246, 0.15)', text: '#dbeafe' },
  bus: { stroke: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)', text: '#e0e7ff' },
  airplane: { stroke: '#a855f7', bg: 'rgba(168, 85, 247, 0.15)', text: '#f3e8ff' },
  boat: { stroke: '#0ea5e9', bg: 'rgba(14, 165, 233, 0.15)', text: '#e0f2fe' },
  // Personnel
  person: { stroke: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', text: '#d1fae5' },
  // Equipment & Objects
  backpack: { stroke: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', text: '#fef3c7' },
  traffic: { stroke: '#eab308', bg: 'rgba(234, 179, 8, 0.15)', text: '#fef9c3' },
  default: { stroke: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', text: '#f0f9ff' },
};

export function getColorForClass(className) {
  const lower = (className || '').toLowerCase();
  for (const [key, val] of Object.entries(CLASS_COLORS)) {
    if (lower.includes(key)) return val;
  }
  return CLASS_COLORS.default;
}

/**
 * Normalizes any bounding box format into [0.0, 1.0] relative image coordinates.
 * Handles:
 * - obj.normalized_bbox ({ x_min, y_min, x_max, y_max } in 0..1)
 * - obj.bbox ({ x_min, y_min, x_max, y_max } in pixels)
 * - Flat fields (obj.bbox_x_min, obj.bbox_y_min, obj.bbox_x_max, obj.bbox_y_max)
 */
export function getNormalizedBBox(obj, naturalWidth, naturalHeight) {
  if (!obj) return null;

  // 1. Direct normalized_bbox from backend
  if (obj.normalized_bbox) {
    const { x_min, y_min, x_max, y_max } = obj.normalized_bbox;
    if (x_max <= 1.05 && y_max <= 1.05 && (x_max > 0 || y_max > 0)) {
      return {
        x_min: Math.max(0, Math.min(1, x_min)),
        y_min: Math.max(0, Math.min(1, y_min)),
        x_max: Math.max(0, Math.min(1, x_max)),
        y_max: Math.max(0, Math.min(1, y_max)),
      };
    }
  }

  // 2. From bbox object or flat fields
  const bbox = obj.bbox || {
    x_min: obj.bbox_x_min,
    y_min: obj.bbox_y_min,
    x_max: obj.bbox_x_max,
    y_max: obj.bbox_y_max,
  };

  if (bbox && bbox.x_max !== undefined && bbox.y_max !== undefined) {
    // If bbox is already normalized (e.g. <= 1.05)
    if (bbox.x_max <= 1.05 && bbox.y_max <= 1.05 && (bbox.x_max > 0 || bbox.y_max > 0)) {
      return {
        x_min: Math.max(0, Math.min(1, bbox.x_min)),
        y_min: Math.max(0, Math.min(1, bbox.y_min)),
        x_max: Math.max(0, Math.min(1, bbox.x_max)),
        y_max: Math.max(0, Math.min(1, bbox.y_max)),
      };
    }

    // Convert pixel coordinates to [0, 1] using known image dimensions
    const w = naturalWidth && naturalWidth > 0 ? naturalWidth : 1;
    const h = naturalHeight && naturalHeight > 0 ? naturalHeight : 1;
    return {
      x_min: Math.max(0, Math.min(1, bbox.x_min / w)),
      y_min: Math.max(0, Math.min(1, bbox.y_min / h)),
      x_max: Math.max(0, Math.min(1, bbox.x_max / w)),
      y_max: Math.max(0, Math.min(1, bbox.y_max / h)),
    };
  }

  return null;
}

/**
 * Calculates the exact content rectangle of the image rendered inside an <img> element,
 * accounting for aspect ratio, container dimensions, and object-contain letterboxing.
 */
export function getImageRenderedBounds(img) {
  if (!img) return null;

  const clientWidth = img.clientWidth;
  const clientHeight = img.clientHeight;
  const naturalWidth = img.naturalWidth || 1;
  const naturalHeight = img.naturalHeight || 1;

  if (clientWidth === 0 || clientHeight === 0) return null;

  const imageAspect = naturalWidth / naturalHeight;
  const elementAspect = clientWidth / clientHeight;

  let renderWidth = clientWidth;
  let renderHeight = clientHeight;
  let offsetX = 0;
  let offsetY = 0;

  // Account for CSS object-contain letterbox / pillarbox padding
  if (elementAspect > imageAspect + 0.001) {
    // Pillarbox: container is wider than image aspect -> blank horizontal bars on sides
    renderWidth = clientHeight * imageAspect;
    offsetX = (clientWidth - renderWidth) / 2;
  } else if (elementAspect < imageAspect - 0.001) {
    // Letterbox: container is taller than image aspect -> blank vertical bars top & bottom
    renderHeight = clientWidth / imageAspect;
    offsetY = (clientHeight - renderHeight) / 2;
  }

  return {
    renderWidth,
    renderHeight,
    offsetX,
    offsetY,
    naturalWidth,
    naturalHeight,
    clientWidth,
    clientHeight,
  };
}

/**
 * Pixel-accurate hit test for click/hover on bounding boxes
 */
export function isPointInBBox(clientX, clientY, obj, bounds, naturalWidth, naturalHeight) {
  if (!bounds) return false;
  const norm = getNormalizedBBox(obj, naturalWidth || bounds.naturalWidth, naturalHeight || bounds.naturalHeight);
  if (!norm) return false;

  const bx1 = bounds.offsetX + norm.x_min * bounds.renderWidth;
  const by1 = bounds.offsetY + norm.y_min * bounds.renderHeight;
  const bx2 = bounds.offsetX + norm.x_max * bounds.renderWidth;
  const by2 = bounds.offsetY + norm.y_max * bounds.renderHeight;

  return clientX >= bx1 && clientX <= bx2 && clientY >= by1 && clientY <= by2;
}
