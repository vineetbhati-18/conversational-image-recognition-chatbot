import React, { useState } from 'react';
import { User, Bot, Info, Copy, Check, Eye, Cpu } from 'lucide-react';

export default function MessageItem({ message }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.sender_type === 'user';
  const isSystem = message.sender_type === 'system';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedTime = new Date(message.created_at || Date.now()).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (isSystem) {
    return (
      <div className="flex items-center justify-center my-3">
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-[11px] text-slate-300 shadow-sm max-w-[90%] text-center">
          <Info className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`group flex items-start space-x-2.5 my-3 text-xs transition-all ${
        isUser ? 'flex-row-reverse space-x-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
          isUser
            ? 'bg-blue-600 border-blue-400 text-white shadow-sm'
            : 'bg-slate-800 border-slate-700 text-blue-400'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div className="flex flex-col max-w-[85%]">
        <div
          className={`relative px-4 py-3 rounded-2xl shadow-sm text-left leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-slate-850 bg-slate-900/90 text-slate-100 rounded-tl-sm border border-slate-800 dark:border-slate-800/80'
          }`}
        >
          {/* Message Content with simple bold/newline support */}
          <div className="whitespace-pre-wrap break-words">
            {message.content.split('\n').map((line, i) => (
              <p key={i} className={i > 0 ? 'mt-1.5' : ''}>
                {line}
              </p>
            ))}
          </div>

          {/* Model Telemetry Pill for Assistant Messages */}
          {!isUser && message.metadata && (
            <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
              {message.metadata.vqa_mode && (
                <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-blue-950/70 border border-blue-800/60 text-blue-300">
                  <Eye className="w-2.5 h-2.5" />
                  <span>BLIP VQA</span>
                </span>
              )}
              {message.metadata.latency_ms && (
                <span className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
                  <Cpu className="w-2.5 h-2.5" />
                  <span>{message.metadata.latency_ms}ms</span>
                </span>
              )}
            </div>
          )}

          {/* Floating Copy Action */}
          <button
            onClick={copyToClipboard}
            className={`absolute top-2 right-2 p-1 rounded transition-opacity opacity-0 group-hover:opacity-100 ${
              isUser
                ? 'hover:bg-blue-700 text-blue-200'
                : 'hover:bg-slate-800 text-slate-400 hover:text-white'
            }`}
            title="Copy message"
            aria-label="Copy message text"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          </button>
        </div>

        {/* Timestamp */}
        <span
          className={`text-[10px] text-slate-500 mt-1 px-1 ${
            isUser ? 'text-right' : 'text-left'
          }`}
        >
          {formattedTime}
        </span>
      </div>
    </div>
  );
}
