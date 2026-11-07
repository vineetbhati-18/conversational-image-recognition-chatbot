import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

const SUGGESTIONS = [
  'What objects are detected?',
  'How many cars?',
  'Where are they located?',
];

export default function MessageInput({ onSendMessage, isLoading, disabled }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
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
    <div className="p-2.5 border-t border-slate-800/60 bg-slate-950/40">
      {/* Suggestions */}
      <div className="flex items-center space-x-1 overflow-x-auto pb-1.5 scrollbar-none mb-1 text-[11px]">
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => applySuggestion(s)}
            disabled={isLoading || disabled}
            className="shrink-0 px-2 py-0.5 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-[10px]"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="relative flex items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isLoading}
          placeholder={
            disabled
              ? 'Loading conversation...'
              : 'Ask a question about the image...'
          }
          rows={1}
          className="w-full bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-2 pr-9 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/80 resize-none transition-colors disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!input.trim() || isLoading || disabled}
          className="absolute right-1.5 bottom-1.5 p-1 rounded-md bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white transition-colors"
          title="Send"
        >
          {isLoading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5" />
          )}
        </button>
      </form>
    </div>
  );
}
