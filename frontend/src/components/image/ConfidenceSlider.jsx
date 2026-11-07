import React from 'react';
import { Sliders } from 'lucide-react';
import { useChat } from '../../context/ChatContext';

export default function ConfidenceSlider() {
  const { confidenceThreshold, setConfidenceThreshold } = useChat();
  const percentage = Math.round(confidenceThreshold * 100);

  const presets = [
    { label: '20%', value: 0.2 },
    { label: '40%', value: 0.4 },
    { label: '60%', value: 0.6 },
    { label: '80%', value: 0.8 },
  ];

  return (
    <div className="px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-800/70 text-xs flex flex-wrap items-center justify-between gap-2.5">
      <div className="flex items-center space-x-2 text-slate-300 min-w-0">
        <Sliders className="w-3.5 h-3.5 text-blue-400 shrink-0" />
        <span className="font-medium text-slate-300">Confidence</span>
        <span className="font-mono text-blue-400 font-semibold">{percentage}%</span>
      </div>

      <div className="flex-1 min-w-[120px] max-w-xs mx-2">
        <input
          type="range"
          min="0.1"
          max="0.95"
          step="0.05"
          value={confidenceThreshold}
          onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
          className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
      </div>

      <div className="flex items-center space-x-1 shrink-0">
        {presets.map((preset) => (
          <button
            key={preset.value}
            onClick={() => setConfidenceThreshold(preset.value)}
            className={`px-1.5 py-0.5 rounded text-[10px] transition-colors ${
              Math.abs(confidenceThreshold - preset.value) < 0.03
                ? 'bg-blue-600 text-white font-medium'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
