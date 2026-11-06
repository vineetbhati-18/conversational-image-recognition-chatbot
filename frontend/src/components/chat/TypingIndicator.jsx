import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

export default function TypingIndicator() {
  return (
    <div className="flex items-start space-x-3 text-xs animate-fade-in py-2">
      <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
        <Bot className="w-4 h-4" />
      </div>
      <div className="bg-slate-800/90 dark:bg-slate-900 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3 shadow-md max-w-[85%]">
        <div className="flex items-center space-x-2 text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span className="text-[11px] font-medium text-slate-300">
            Analyzing visual features & generating response...
          </span>
        </div>
        <div className="flex items-center space-x-1.5 mt-2 pl-0.5">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.3s]" />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce [animation-delay:-0.15s]" />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" />
        </div>
      </div>
    </div>
  );
}
