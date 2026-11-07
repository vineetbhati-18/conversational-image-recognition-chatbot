import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import { getColorForClass } from '../../utils/canvasHelpers';
import { Box } from 'lucide-react';

export default function ObjectDetectionList() {
  const {
    detectedObjects,
    selectedObjectId,
    setSelectedObjectId,
    confidenceThreshold,
    sendMessage,
    activeImage,
  } = useChat();

  const [activeClassFilter, setActiveClassFilter] = useState('ALL');

  if (!activeImage) return null;

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
    sendMessage(`Tell me about the ${obj.class_name} detected at ${conf}% confidence.`);
  };

  return (
    <div className="rounded-xl bg-slate-900/50 border border-slate-800/70 p-3 text-xs flex flex-col space-y-2.5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Box className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-medium text-slate-200">Detected Objects</span>
          <span className="text-[11px] text-slate-500">
            ({filteredByConf.length})
          </span>
        </div>
      </div>

      {/* Category Filter Chips */}
      {Object.keys(classCounts).length > 0 && (
        <div className="flex flex-wrap gap-1">
          <button
            onClick={() => setActiveClassFilter('ALL')}
            className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
              activeClassFilter === 'ALL'
                ? 'bg-blue-600 text-white font-medium'
                : 'bg-slate-800/80 text-slate-400 hover:text-white'
            }`}
          >
            All ({filteredByConf.length})
          </button>
          {Object.entries(classCounts).map(([cls, count]) => (
            <button
              key={cls}
              onClick={() => setActiveClassFilter(cls)}
              className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
                activeClassFilter === cls
                  ? 'bg-blue-600 text-white font-medium'
                  : 'bg-slate-800/80 text-slate-400 hover:text-white'
              }`}
            >
              {cls} ({count})
            </button>
          ))}
        </div>
      )}

      {/* Objects List */}
      <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
        {displayedObjects.length === 0 ? (
          <p className="text-slate-500 text-[11px] py-3 text-center">
            No objects meet the current confidence threshold.
          </p>
        ) : (
          displayedObjects.map((obj, idx) => {
            const isSelected = selectedObjectId === obj.id;
            const colors = getColorForClass(obj.class_name);
            const conf = Math.round((obj.confidence ?? obj.confidence_score ?? 0) * 100);

            return (
              <div
                key={obj.id || idx}
                onClick={() => setSelectedObjectId(isSelected ? null : obj.id)}
                className={`px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-blue-600/20 border border-blue-500/50 text-white'
                    : 'bg-slate-900/80 hover:bg-slate-800/60 text-slate-300'
                }`}
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: colors.stroke }}
                  />
                  <span className="font-medium text-xs truncate capitalize">
                    {obj.class_name}
                  </span>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <span className="font-mono text-[10px] text-slate-400">
                    {conf}%
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAskAboutObject(obj);
                    }}
                    className="text-[10px] text-blue-400 hover:text-blue-300 underline"
                  >
                    Ask
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
