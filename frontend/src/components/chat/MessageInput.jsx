import React, { useState, useRef, useEffect } from 'react';
import { Send, CornerDownLeft, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  'What objects are detected in this image?',
  'How many vehicles are present?',
  'Describe the overall scene and terrain',
  'What is located on the left side?',
];

export default function MessageInput({ onSendMessage, isLoading, disabled }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea height based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading || disabled) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const applySuggestion = (suggestion) => {
    if (isLoading || disabled) return;
    onSendMessage(suggestion);
  };

  return (
    <div className="p-3 border-t border-slate-800 bg-slate-900/90 dark:bg-slate-950/90 backdrop-blur-sm">
      {/* Quick Prompt Suggestion Chips */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-2 scrollbar-none mb-1 text-[11px]">
        <div className="flex items-center text-slate-500 shrink-0 mr-1">
          <Sparkles className="w-3 h-3 text-blue-400 mr-1" />
          <span>Suggestions:</span>
        </div>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => applySuggestion(s)}
            disabled={isLoading || disabled}
            className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-750 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 hover:border-blue-500/50 transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-[11px]"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative flex items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={
            disabled
              ? 'Upload an image to ask questions...'
              : 'Ask a question about the image (e.g. "What objects are detected?")...'
          }
          rows={1}
          className="w-full bg-slate-800/90 dark:bg-slate-900 border border-slate-700/80 rounded-xl px-3.5 py-2.5 pr-11 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        />

        <button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          className="absolute right-1.5 bottom-1.5 p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
          title="Send message (Enter)"
          aria-label="Send message"
        >
          {isLoading ? (
            <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </button>
      </form>

      <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1.5 px-1">
        <span>Press Enter to send, Shift+Enter for new line</span>
        <span>Salesforce BLIP VQA + Context Memory</span>
      </div>
    </div>
  );
}
