import React from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { useChat } from '../../context/ChatContext';
import { MessageSquare, Shield, Trash2 } from 'lucide-react';

export default function ChatContainer() {
  const { messages, sendMessage, isLoading, activeSession, activeImage } = useChat();

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm">
      {/* Chat Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white tracking-wide">
              Conversational Dialogue
            </h3>
            <p className="text-[10px] text-slate-400 truncate max-w-[220px]">
              {activeImage ? `Context: ${activeImage.name}` : 'Awaiting image upload'}
            </p>
          </div>
        </div>

        {/* Security / Confidentiality Pill */}
        <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700/60 text-[10px] text-slate-400 font-medium">
          <Shield className="w-3 h-3 text-emerald-400" />
          <span>Local Engine</span>
        </div>
      </div>

      {/* Messages Stream */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Message Input */}
      <MessageInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={false}
      />
    </div>
  );
}
