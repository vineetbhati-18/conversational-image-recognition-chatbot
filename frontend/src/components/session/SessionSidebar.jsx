import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import SessionItem from './SessionItem';
import { Plus, Search, MessageSquare, Database, X, Loader2 } from 'lucide-react';

export default function SessionSidebar({ onClose }) {
  const { sessions, activeSessionId, switchSession, createNewSession, deleteSession, isSessionLoading } = useChat();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter((s) =>
    (s.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950/80 text-slate-200 select-none border-r border-slate-800/60">
      {/* Top Header & Actions */}
      <div className="p-3 border-b border-slate-800/60 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300">Conversations</span>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded text-slate-400 hover:text-white lg:hidden"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* New Chat Button */}
        <button
          onClick={() => createNewSession()}
          className="w-full py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center justify-center space-x-1.5 transition-colors shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>

        {/* Search Input */}
        <div className="relative">
          <Search className="w-3 h-3 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            className="w-full bg-slate-900/80 border border-slate-800 rounded-lg pl-7 pr-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/80"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isSessionLoading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-8 space-x-2 text-xs text-slate-400">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
            <span>Loading...</span>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            {searchQuery ? 'No matching chats' : 'No conversations'}
          </div>
        ) : (
          filteredSessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              isActive={s.id === activeSessionId}
              onSelect={() => {
                switchSession(s.id);
                onClose?.();
              }}
              onDelete={deleteSession}
            />
          ))
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="p-2.5 border-t border-slate-800/60 bg-slate-950/40 text-[10px] text-slate-500 flex items-center justify-between">
        <span className="flex items-center space-x-1">
          <Database className="w-2.5 h-2.5 text-amber-400" />
          <span>PostgreSQL</span>
        </span>
        <span>{sessions.length} sessions</span>
      </div>
    </div>
  );
}
