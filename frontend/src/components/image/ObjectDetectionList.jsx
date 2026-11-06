import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import { getColorForClass } from '../../utils/canvasHelpers';
import { Box, HelpCircle, Layers, CheckCircle2, Sparkles, AlertCircle } from 'lucide-react';

// Sample demonstration telemetry (strictly separate from real API responses per Rule 6)
const SAMPLE_DEMO_DETECTIONS = [
  {
    id: 'demo-obj-1',
    class_name: 'truck',
    confidence: 0.94,
    bbox: { x_min: 60, y_min: 120, x_max: 320, y_max: 290 },
    isDemo: true,
  },
  {
    id: 'demo-obj-2',
    class_name: 'car',
    confidence: 0.88,
    bbox: { x_min: 360, y_min: 180, x_max: 490, y_max: 270 },
    isDemo: true,
  },
  {
    id: 'demo-obj-3',
    class_name: 'person',
    confidence: 0.82,
    bbox: { x_min: 520, y_min: 150, x_max: 570, y_max: 260 },
    isDemo: true,
  },
  {
    id: 'demo-obj-4',
    class_name: 'backpack',
    confidence: 0.65,
    bbox: { x_min: 535, y_min: 175, x_max: 565, y_max: 215 },
    isDemo: true,
  },
];

export default function ObjectDetectionList() {
  const {
    detectedObjects,
    setDetectedObjects,
    selectedObjectId,
    setSelectedObjectId,
    confidenceThreshold,
    sendMessage,
    activeImage,
  } = useChat();

  const [activeClassFilter, setActiveClassFilter] = useState('ALL');

  // Filter objects by confidence threshold
  const filteredByConf = detectedObjects.filter(
    (obj) => (obj.confidence ?? obj.confidence_score ?? 1) >= confidenceThreshold
  );

  // Group classes for category filter
  const classCounts = filteredByConf.reduce((acc, obj) => {
    acc[obj.class_name] = (acc[obj.class_name] || 0) + 1;
    return acc;
  }, {});

  const displayedObjects =
    activeClassFilter === 'ALL'
      ? filteredByConf
      : filteredByConf.filter((obj) => obj.class_name === activeClassFilter);

  const handleAskAboutObject = (obj) => {
    const conf = Math.round((obj.confidence ?? obj.confidence_score ?? 0) * 100);
    sendMessage(
      `Please provide details on the detected ${obj.class_name} with ${conf}% confidence score.`
    );
  };

  const loadDemoTelemetry = () => {
    setDetectedObjects(SAMPLE_DEMO_DETECTIONS);
  };

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-4 text-xs shadow-md flex flex-col space-y-3">
      {/* Header & Stats */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <Box className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-semibold text-white tracking-wide">Detected Object Telemetry</h4>
            <p className="text-[11px] text-slate-400">
              {filteredByConf.length} objects meet {Math.round(confidenceThreshold * 100)}% threshold
            </p>
          </div>
        </div>

        {/* Demo Telemetry Loader if no objects loaded */}
        {activeImage && detectedObjects.length === 0 && (
          <button
            onClick={loadDemoTelemetry}
            className="px-2.5 py-1 rounded-lg bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-800 text-[11px] font-medium flex items-center space-x-1 transition-colors"
            title="Load sample detection annotations for frontend verification"
          >
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>Load Demo Annotations</span>
          </button>
        )}
      </div>

      {/* Demo Data Notice if currently showing demo objects */}
      {detectedObjects.some((o) => o.isDemo) && (
        <div className="p-2 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-[11px] text-indigo-300 flex items-center justify-between">
          <span>Notice: Displaying sample annotations [Demo Data] for interface testing.</span>
          <button
            onClick={() => setDetectedObjects([])}
            className="text-indigo-400 hover:text-white underline text-[10px]"
          >
            Clear Demo
          </button>
        </div>
      )}

      {/* Class Category Filter Chips */}
      {Object.keys(classCounts).length > 0 && (
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none text-[11px]">
          <button
            onClick={() => setActiveClassFilter('ALL')}
            className={`px-2.5 py-0.5 rounded-full border transition-colors ${
              activeClassFilter === 'ALL'
                ? 'bg-blue-600 border-blue-500 text-white font-medium'
                : 'bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-slate-200'
            }`}
          >
            All ({filteredByConf.length})
          </button>
          {Object.entries(classCounts).map(([cls, count]) => (
            <button
              key={cls}
              onClick={() => setActiveClassFilter(cls)}
              className={`px-2.5 py-0.5 rounded-full border capitalize transition-colors ${
                activeClassFilter === cls
                  ? 'bg-blue-600 border-blue-500 text-white font-medium'
                  : 'bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-slate-200'
              }`}
            >
              {cls} ({count})
            </button>
          ))}
        </div>
      )}

      {/* Object Cards List */}
      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
        {displayedObjects.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            {detectedObjects.length === 0
              ? 'No objects detected yet. Real detections will display here upon YOLO analysis.'
              : 'No objects match current confidence threshold filter.'}
          </div>
        ) : (
          displayedObjects.map((obj, idx) => {
            const isSelected = selectedObjectId === obj.id;
            const colors = getColorForClass(obj.class_name);
            const conf = Math.round((obj.confidence ?? obj.confidence_score ?? 0) * 100);

            return (
              <div
                key={obj.id || idx}
                onClick={() => setSelectedObjectId(isSelected ? null : obj.id)}
                className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  isSelected
                    ? 'bg-blue-950/60 border-blue-500 shadow-sm'
                    : 'bg-slate-850 bg-slate-900/60 hover:bg-slate-800/80 border-slate-800'
                }`}
              >
                {/* Left: Class Chip & Coordinates */}
                <div className="flex items-center space-x-3">
                  <div
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: colors.stroke }}
                  />
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-white capitalize text-xs">
                        {obj.class_name} #{idx + 1}
                      </span>
                      {isSelected && (
                        <span className="text-[10px] px-1.5 rounded bg-blue-600 text-white font-medium">
                          Selected
                        </span>
                      )}
                    </div>
                    {obj.bbox && (
                      <span className="text-[10px] font-mono text-slate-500">
                        [{Math.round(obj.bbox.x_min)}, {Math.round(obj.bbox.y_min)}] → [
                        {Math.round(obj.bbox.x_max)}, {Math.round(obj.bbox.y_max)}]
                      </span>
                    )}
                  </div>
                </div>

                {/* Right: Confidence Score & Quick Query */}
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <span className="font-mono font-bold text-xs text-slate-200">{conf}%</span>
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${conf}%`,
                          backgroundColor: colors.stroke,
                        }}
                      />
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAskAboutObject(obj);
                    }}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-blue-600 text-slate-400 hover:text-white transition-colors"
                    title="Ask AI about this object"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
