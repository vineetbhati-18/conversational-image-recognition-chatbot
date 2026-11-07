import React, { useState } from 'react';
import { useChat } from '../../context/ChatContext';
import SessionItem from './SessionItem';
import { Plus, Search, Layers, Database, Shield, X } from 'lucide-react';

export default function SessionSidebar({ onClose }) {
  const { sessions, activeSessionId, switchSession, createNewSession, deleteSession, isSessionLoading } = useChat();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredSessions = sessions.filter((s) =>
    (s.title || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/90 dark:bg-slate-950/90 text-slate-100 select-none">
      {/* Top Header & Actions */}
      <div className="p-4 border-b border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Conversations
            </h3>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-400 hover:text-white lg:hidden"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* New Conversation Button */}
        <button
          onClick={() => createNewSession()}
          className="w-full py-2.5 px-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-md shadow-blue-900/20 active:scale-[0.99]"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full bg-slate-800/80 border border-slate-700/60 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {isSessionLoading && sessions.length === 0 ? (
          <div className="flex items-center justify-center py-10 space-x-2 text-xs text-slate-400">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span>Loading conversations...</span>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            {searchQuery ? 'No matching conversations' : 'No conversations yet'}
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

      {/* Sidebar Footer with PostgreSQL & Security Telemetry */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/60 text-[11px] text-slate-500 space-y-1.5">
        <div className="flex items-center justify-between text-[10px]">
          <span className="flex items-center space-x-1">
            <Database className="w-3 h-3 text-amber-400" />
            <span>PostgreSQL 18</span>
          </span>
          <span className="font-mono text-slate-400">{sessions.length} Threads</span>
        </div>
        <div className="flex items-center space-x-1 text-[10px] text-slate-500">
          <Shield className="w-3 h-3 text-emerald-400" />
          <span>Multi-turn contextual persistence</span>
        </div>
      </div>
    </div>
  );
}
