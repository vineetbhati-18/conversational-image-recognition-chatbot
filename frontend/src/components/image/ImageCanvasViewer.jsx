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

    canvas.width = renderedWidth;
    canvas.height = renderedHeight;
    ctx.clearRect(0, 0, renderedWidth, renderedHeight);

    if (!showBoxes || visibleObjects.length === 0) return;

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
      ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2 : 1.5;
      ctx.strokeStyle = isSelected ? '#38bdf8' : colors.stroke;
      ctx.fillStyle = isSelected
        ? 'rgba(56, 189, 248, 0.20)'
        : isHovered
        ? 'rgba(255, 255, 255, 0.10)'
        : colors.bg;

      ctx.fillRect(x, y, width, height);
      ctx.strokeRect(x, y, width, height);

      // Draw Label Badge
      const conf = (obj.confidence ?? obj.confidence_score ?? 0) * 100;
      const labelText = showScores
        ? `${obj.class_name} ${conf.toFixed(0)}%`
        : obj.class_name;

      ctx.font = '500 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      const textMetrics = ctx.measureText(labelText);
      const textWidth = textMetrics.width;
      const badgeHeight = 16;
      const badgeWidth = textWidth + 8;

      const badgeY = y - badgeHeight >= 0 ? y - badgeHeight : y;
      ctx.fillStyle = isSelected ? '#0284c7' : colors.stroke;
      if (typeof ctx.roundRect === 'function') {
        ctx.beginPath();
        ctx.roundRect(x, badgeY, badgeWidth, badgeHeight, [3, 3, 0, 0]);
        ctx.fill();
      } else {
        ctx.fillRect(x, badgeY, badgeWidth, badgeHeight);
      }

      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, x + 4, badgeY + 12);
    });
  }, [
    activeImage,
    visibleObjects,
    showBoxes,
    showScores,
    selectedObjectId,
    hoveredObjectId,
  ]);

  useEffect(() => {
    renderCanvas();
    const handleResize = () => renderCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderCanvas]);

  const handleCanvasMouseMove = (e) => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !activeImage) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const naturalWidth = activeImage.width || img.naturalWidth || canvas.width;
    const naturalHeight = activeImage.height || img.naturalHeight || canvas.height;
    const scaleX = canvas.width / naturalWidth;
    const scaleY = canvas.height / naturalHeight;

    const hovered = visibleObjects.find((obj) => {
      const bbox = obj.bbox || {
        x_min: obj.bbox_x_min,
        y_min: obj.bbox_y_min,
        x_max: obj.bbox_x_max,
        y_max: obj.bbox_y_max,
      };
      return isPointInBBox(clientX, clientY, bbox, scaleX, scaleY);
    });

    setHoveredObjectId(hovered ? hovered.id : null);
  };

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    const img = imageRef.current;
    if (!canvas || !img || !activeImage) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const naturalWidth = activeImage.width || img.naturalWidth || canvas.width;
    const naturalHeight = activeImage.height || img.naturalHeight || canvas.height;
    const scaleX = canvas.width / naturalWidth;
    const scaleY = canvas.height / naturalHeight;

    const clicked = visibleObjects.find((obj) => {
      const bbox = obj.bbox || {
        x_min: obj.bbox_x_min,
        y_min: obj.bbox_y_min,
        x_max: obj.bbox_x_max,
        y_max: obj.bbox_y_max,
      };
      return isPointInBBox(clientX, clientY, bbox, scaleX, scaleY);
    });

    setSelectedObjectId(clicked ? clicked.id : null);
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  if (!activeImage) return null;

  return (
    <div
      ref={containerRef}
      className={`rounded-xl bg-slate-900/50 border border-slate-800/70 overflow-hidden flex flex-col ${
        isFullscreen ? 'fixed inset-0 z-50 p-4 bg-slate-950' : 'w-full'
      }`}
    >
      {/* Top Toolbar */}
      <div className="px-3 py-2 border-b border-slate-800/60 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-slate-200">Vision Canvas</span>
          <span className="text-[11px] text-slate-500">
            {visibleObjects.length} detected
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-1 text-slate-300">
          <button
            onClick={() => setShowBoxes((prev) => !prev)}
            className={`px-2 py-1 rounded text-[11px] flex items-center space-x-1 transition-colors ${
              showBoxes
                ? 'bg-blue-600/20 text-blue-400'
                : 'bg-slate-800 text-slate-500'
            }`}
            title="Toggle Boxes"
          >
            {showBoxes ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
            <span className="hidden sm:inline">Boxes</span>
          </button>

          <button
            onClick={() => setShowScores((prev) => !prev)}
            className={`px-2 py-1 rounded text-[11px] flex items-center space-x-1 transition-colors ${
              showScores
                ? 'bg-blue-600/20 text-blue-400'
                : 'bg-slate-800 text-slate-500'
            }`}
            title="Toggle Confidence Scores"
          >
            <Percent className="w-3 h-3" />
            <span className="hidden sm:inline">Scores</span>
          </button>

          <div className="h-3 w-px bg-slate-800 mx-1" />

          <button
            onClick={() => setZoomLevel((prev) => Math.max(prev - 0.25, 0.75))}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setZoomLevel((prev) => Math.min(prev + 0.25, 3))}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>

          {zoomLevel !== 1 && (
            <button
              onClick={() => setZoomLevel(1)}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={toggleFullscreen}
            className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            title="Toggle Fullscreen"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="relative flex-1 overflow-auto p-3 flex items-center justify-center bg-slate-950/70 min-h-[320px] max-h-[500px]">
        <div
          className="relative inline-block transition-transform duration-100 origin-center"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          <img
            ref={imageRef}
            src={activeImage.url}
            alt={activeImage.name}
            onLoad={renderCanvas}
            className="block max-w-full max-h-[460px] object-contain rounded select-none"
          />

          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            onMouseLeave={() => setHoveredObjectId(null)}
            className="absolute inset-0 w-full h-full cursor-crosshair rounded"
          />
        </div>
      </div>
    </div>
  );
}
