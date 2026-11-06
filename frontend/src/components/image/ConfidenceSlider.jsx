import React from 'react';
import { Sliders, Filter } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

export default function ConfidenceSlider() {
  const { confidenceThreshold, setConfidenceThreshold } = useChat();

  const percentage = Math.round(confidenceThreshold * 100);

  const presets = [
    { label: 'Low (20%)', value: 0.2 },
    { label: 'Balanced (40%)', value: 0.4 },
    { label: 'High (65%)', value: 0.65 },
    { label: 'Strict (80%)', value: 0.8 },
  ];

  return (
    <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2 text-slate-300 font-medium">
          <Sliders className="w-3.5 h-3.5 text-blue-400" />
          <span>Confidence Threshold</span>
        </div>
        <span className="font-mono font-semibold px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800 text-[11px]">
          {percentage}%
        </span>
      </div>

      {/* Range Input Slider */}
      <input
        type="range"
        min="0.1"
        max="0.95"
        step="0.05"
        value={confidenceThreshold}
        onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
        className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
      />

      {/* Preset Buttons */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/80">
        <div className="text-[10px] text-slate-500">Presets:</div>
        <div className="flex items-center space-x-1.5">
          {presets.map((preset) => (
            <button
              key={preset.value}
              onClick={() => setConfidenceThreshold(preset.value)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
                Math.abs(confidenceThreshold - preset.value) < 0.03
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-slate-200'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
