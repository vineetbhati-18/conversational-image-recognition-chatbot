import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';
import TypingIndicator from './TypingIndicator';
import { Loader2 } from 'lucide-react';

export default function MessageList({ messages, isLoading, isSessionLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (isSessionLoading && (!messages || messages.length === 0)) {
    return (
      <div className="flex-1 flex items-center justify-center space-x-2 text-xs text-slate-500">
        <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
        <span>Restoring conversation...</span>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-3.5 py-3 space-y-2 select-text">
      {(!messages || messages.length === 0) ? (
        <div className="h-full flex items-center justify-center text-slate-500 text-xs text-center p-6">
          Upload an image to start visual analysis and ask questions.
        </div>
      ) : (
        messages.map((msg) => <MessageItem key={msg.id} message={msg} />)
      )}

      {isLoading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
