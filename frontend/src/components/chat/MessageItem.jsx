import React, { useState } from 'react';
import { User, Bot, Copy, Check } from 'lucide-react';

export default function MessageItem({ message }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender_type === 'user';
  const isSystem = message.sender_type === 'system';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const formattedTime = new Date(message.created_at || Date.now()).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <div className="px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 text-center max-w-[90%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`group flex items-start space-x-2 my-2 text-xs ${
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      }`}
    >
      {/* Small Avatar */}
      <div
        className={`w-6 h-6 rounded-md flex items-center justify-center shrink-0 text-white ${
          isUser ? 'bg-blue-600' : 'bg-slate-800 text-blue-400 border border-slate-700/60'
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Bubble */}
      <div className="flex flex-col max-w-[85%]">
        <div
          className={`relative px-3.5 py-2.5 rounded-2xl leading-relaxed text-left ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-slate-900/90 text-slate-200 rounded-tl-sm border border-slate-800/80'
          }`}
        >
          <div className="whitespace-pre-wrap break-words">
            {message.content.split('\n').map((line, i) => (
              <p key={i} className={i > 0 ? 'mt-1' : ''}>
                {line}
              </p>
            ))}
          </div>

          {/* Minimal Telemetry Tag */}
          {!isUser && message.metadata && (message.metadata.vqa_mode || message.metadata.latency_ms) && (
            <div className="mt-1.5 pt-1.5 border-t border-slate-800/60 flex items-center space-x-2 text-[10px] text-slate-500">
              {message.metadata.vqa_mode && <span>BLIP VQA</span>}
              {message.metadata.latency_ms && <span>{message.metadata.latency_ms}ms</span>}
            </div>
          )}

          {/* Copy Button */}
          <button
            onClick={copyToClipboard}
            className={`absolute top-1.5 right-1.5 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
              isUser ? 'hover:bg-blue-700 text-blue-200' : 'hover:bg-slate-800 text-slate-400'
            }`}
            title="Copy"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>

        <span className={`text-[10px] text-slate-500 mt-0.5 px-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {formattedTime}
        </span>
      </div>
    </div>
  );
}
