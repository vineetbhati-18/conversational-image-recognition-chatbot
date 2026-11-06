import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import TypingIndicator from './TypingIndicator';

export default function MessageList({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center text-slate-500 text-xs text-center p-6">
          No messages yet. Ask a question about the uploaded image to start the conversation.
        </div>
      ) : (
        messages.map((msg) => <MessageItem key={msg.id} message={msg} />)
      )}

      {isLoading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
