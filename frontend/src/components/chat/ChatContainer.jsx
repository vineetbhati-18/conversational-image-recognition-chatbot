import React from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { useChat } from '../../context/ChatContext';
import { MessageSquare, Shield } from 'lucide-react';

export default function ChatContainer() {
  const { messages, sendMessage, isLoading, isSessionLoading, activeImage } = useChat();

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950/60 select-none">
      {/* Chat Header */}
      <div className="px-3.5 py-2.5 border-b border-slate-800/60 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 min-w-0">
          <MessageSquare className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span className="font-medium text-slate-200">Chat</span>
          {activeImage && (
            <span className="text-[10px] text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800 truncate max-w-[160px]">
              {activeImage.name}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1 text-[10px] text-slate-500">
          <Shield className="w-3 h-3 text-emerald-400" />
          <span>Local Engine</span>
        </div>
      </div>

      {/* Messages Stream */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        isSessionLoading={isSessionLoading}
      />

      {/* Message Input */}
      <MessageInput
        onSendMessage={sendMessage}
        isLoading={isLoading}
        disabled={isSessionLoading}
      />
    </div>
  );
}
