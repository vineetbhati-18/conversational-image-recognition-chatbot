import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useChat } from '../../context/ChatContext';
import { getColorForClass, isPointInBBox } from '../../utils/canvasHelpers';
import { Eye, EyeOff, ZoomIn, ZoomOut, RotateCcw, Maximize2, Minimize2, Percent } from 'lucide-react';

export default function ImageCanvasViewer() {
  const {
    activeImage,
    detectedObjects,
    selectedObjectId,
    setSelectedObjectId,
    confidenceThreshold,
  } = useChat();

  const containerRef = useRef(null);
  const imageRef = useRef(null);
  const canvasRef = useRef(null);

  // Canvas View Controls
  const [showBoxes, setShowBoxes] = useState(true);
  const [showScores, setShowScores] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredObjectId, setHoveredObjectId] = useState(null);

  // Filter detected objects based on user threshold slider
  const visibleObjects = detectedObjects.filter(
    (obj) => (obj.confidence ?? obj.confidence_score ?? 1) >= confidenceThreshold
  );

  // Redraw Canvas Overlay
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !activeImage) return;

    const ctx = canvas.getContext('2d');
    const renderedWidth = img.clientWidth;
    const renderedHeight = img.clientHeight;

    // Match canvas coordinate system to rendered image dimensions
    canvas.width = renderedWidth;
    canvas.height = renderedHeight;
    ctx.clearRect(0, 0, renderedWidth, renderedHeight);

    if (!showBoxes || visibleObjects.length === 0) return;

    // Compute coordinate scale factors
    const naturalWidth = activeImage.width || img.naturalWidth || renderedWidth;
    const naturalHeight = activeImage.height || img.naturalHeight || renderedHeight;
    const scaleX = renderedWidth / naturalWidth;
    const scaleY = renderedHeight / naturalHeight;

    visibleObjects.forEach((obj) => {
      const isSelected = selectedObjectId === obj.id;
      const isHovered = hoveredObjectId === obj.id;
      const colors = getColorForClass(obj.class_name);

      const bbox = obj.bbox || {
        x_min: obj.bbox_x_min,
        y_min: obj.bbox_y_min,
        x_max: obj.bbox_x_max,
        y_max: obj.bbox_y_max,
      };

      const x = bbox.x_min * scaleX;
      const y = bbox.y_min * scaleY;
      const width = (bbox.x_max - bbox.x_min) * scaleX;
      const height = (bbox.y_max - bbox.y_min) * scaleY;

      // Draw bounding box rectangle
      ctx.lineWidth = isSelected ? 3 : isHovered ? 2.5 : 2;
      ctx.strokeStyle = isSelected ? '#38bdf8' : colors.stroke;
      ctx.fillStyle = isSelected
        ? 'rgba(56, 189, 248, 0.25)'
        : isHovered
        ? 'rgba(255, 255, 255, 0.15)'
        : colors.bg;

      ctx.fillRect(x, y, width, height);
      ctx.strokeRect(x, y, width, height);

      // Draw Label Badge
      const conf = (obj.confidence ?? obj.confidence_score ?? 0) * 100;
      const labelText = showScores
        ? `${obj.class_name} ${conf.toFixed(0)}%`
        : obj.class_name;

      ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      const textMetrics = ctx.measureText(labelText);
      const textWidth = textMetrics.width;
      const badgeHeight = 18;
      const badgeWidth = textWidth + 12;

      // Badge background (above box, or inside if too close to top)
      const badgeY = y - badgeHeight >= 0 ? y - badgeHeight : y;
      ctx.fillStyle = isSelected ? '#0284c7' : colors.stroke;
      ctx.beginPath();
      ctx.roundRect(x, badgeY, badgeWidth, badgeHeight, [4, 4, 0, 0]);
      ctx.fill();

      // Badge text
      ctx.fillStyle = '#ffffff';
      ctx.textBaseline = 'middle';
      ctx.fillText(labelText, x + 6, badgeY + badgeHeight / 2);
    });
  }, [
    activeImage,
    visibleObjects,
    showBoxes,
    showScores,
    selectedObjectId,
    hoveredObjectId,
  ]);

  // Re-render when dependencies change or window resizes
  useEffect(() => {
    renderCanvas();
    window.addEventListener('resize', renderCanvas);
    return () => window.removeEventListener('resize', renderCanvas);
  }, [renderCanvas]);

  // Click detection on Canvas
  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !activeImage) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const naturalWidth = activeImage.width || img.naturalWidth;
    const naturalHeight = activeImage.height || img.naturalHeight;
    const scaleX = img.clientWidth / naturalWidth;
    const scaleY = img.clientHeight / naturalHeight;

    const clicked = visibleObjects.find((obj) => {
      const bbox = obj.bbox || {
        x_min: obj.bbox_x_min,
        y_min: obj.bbox_y_min,
        x_max: obj.bbox_x_max,
        y_max: obj.bbox_y_max,
      };
      return isPointInBBox(clickX, clickY, bbox, scaleX, scaleY);
    });

    if (clicked) {
      setSelectedObjectId(clicked.id === selectedObjectId ? null : clicked.id);
    } else {
      setSelectedObjectId(null);
    }
  };

  // Mouse move for hover detection
  const handleCanvasMouseMove = (e) => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !activeImage) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const naturalWidth = activeImage.width || img.naturalWidth;
    const naturalHeight = activeImage.height || img.naturalHeight;
    const scaleX = img.clientWidth / naturalWidth;
    const scaleY = img.clientHeight / naturalHeight;

    const hovered = visibleObjects.find((obj) => {
      const bbox = obj.bbox || {
        x_min: obj.bbox_x_min,
        y_min: obj.bbox_y_min,
        x_max: obj.bbox_x_max,
        y_max: obj.bbox_y_max,
      };
      return isPointInBBox(mouseX, mouseY, bbox, scaleX, scaleY);
    });

    setHoveredObjectId(hovered ? hovered.id : null);
  };

  if (!activeImage) return null;

  return (
    <div
      ref={containerRef}
      className={`relative rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden flex flex-col shadow-lg transition-all ${
        isFullscreen ? 'fixed inset-4 z-50 bg-slate-950' : 'w-full'
      }`}
    >
      {/* Top Canvas Toolbar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-850 bg-slate-900/90 border-b border-slate-800 text-xs">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-white tracking-wide">YOLO Vision Canvas</span>
          <span className="px-2 py-0.5 rounded-full bg-blue-950 text-blue-400 border border-blue-800/60 text-[10px] font-mono">
            {visibleObjects.length} objects visible
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-1 sm:space-x-2 text-slate-300">
          {/* Toggle Bounding Boxes */}
          <button
            onClick={() => setShowBoxes((prev) => !prev)}
            className={`p-1.5 rounded-lg border text-xs flex items-center space-x-1 transition-colors ${
              showBoxes
                ? 'bg-blue-600/20 border-blue-500/40 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
            title="Toggle Bounding Boxes"
          >
            {showBoxes ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline text-[11px]">Boxes</span>
          </button>

          {/* Toggle Scores */}
          <button
            onClick={() => setShowScores((prev) => !prev)}
            className={`p-1.5 rounded-lg border text-xs flex items-center space-x-1 transition-colors ${
              showScores
                ? 'bg-blue-600/20 border-blue-500/40 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
            title="Toggle Confidence Scores"
          >
            <Percent className="w-3.5 h-3.5" />
            <span className="hidden sm:inline text-[11px]">Scores</span>
          </button>

          {/* Zoom In */}
          <button
            onClick={() => setZoomLevel((prev) => Math.min(prev + 0.25, 3))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          {/* Zoom Out */}
          <button
            onClick={() => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>

          {/* Reset Zoom */}
          {zoomLevel !== 1 && (
            <button
              onClick={() => setZoomLevel(1)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Fullscreen Toggle */}
          <button
            onClick={() => setIsFullscreen((prev) => !prev)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="relative flex-1 overflow-auto p-4 flex items-center justify-center bg-slate-950/80 min-h-[360px] max-h-[560px]">
        <div
          className="relative inline-block transition-transform duration-150 origin-center"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          {/* Base Image */}
          <img
            ref={imageRef}
            src={activeImage.url}
            alt={activeImage.name}
            onLoad={renderCanvas}
            className="block max-w-full max-h-[480px] object-contain rounded-lg select-none"
          />

          {/* Overlay Canvas */}
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setHoveredObjectId(null)}
            className="absolute inset-0 w-full h-full cursor-crosshair rounded-lg"
          />
        </div>
      </div>
    </div>
  );
}
