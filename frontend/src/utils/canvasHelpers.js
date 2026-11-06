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
 * Check if a click point (x, y) is inside a bounding box
 */
export function isPointInBBox(x, y, bbox, scaleX, scaleY) {
  const bx1 = bbox.x_min * scaleX;
  const by1 = bbox.y_min * scaleY;
  const bx2 = bbox.x_max * scaleX;
  const by2 = bbox.y_max * scaleY;
  return x >= bx1 && x <= bx2 && y >= by1 && y <= by2;
}
