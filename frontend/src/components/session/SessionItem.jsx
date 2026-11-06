import React, { useState } from 'react';
import { MessageSquare, Trash2, Check, X, Clock } from 'lucide-react';

export default function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
}) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);

  const formattedDate = new Date(session.created_at || Date.now()).toLocaleDateString([], {
    month: 'short',
    day: 'numeric',
  });

  const handleDelete = (e) => {
    e.stopPropagation();
    if (isConfirmingDelete) {
      onDelete(session.id);
    } else {
      setIsConfirmingDelete(true);
    }
  };

  const cancelDelete = (e) => {
    e.stopPropagation();
    setIsConfirmingDelete(false);
  };

  return (
    <div
      onClick={onSelect}
      className={`group relative p-2.5 rounded-xl transition-all cursor-pointer border text-xs flex items-center justify-between ${
        isActive
          ? 'bg-blue-600/15 border-blue-500/50 text-white shadow-sm'
          : 'bg-slate-900/60 hover:bg-slate-800/80 border-slate-800/80 text-slate-300'
      }`}
    >
      <div className="flex items-center space-x-2.5 min-w-0 pr-2">
        <div
          className={`p-1.5 rounded-lg shrink-0 transition-colors ${
            isActive
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
        </div>
        <div className="min-w-0">
          <p className="font-medium truncate text-xs">{session.title}</p>
          <div className="flex items-center space-x-1 text-[10px] text-slate-500 mt-0.5">
            <Clock className="w-2.5 h-2.5" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </div>

      {/* Delete Controls */}
      <div className="shrink-0 flex items-center space-x-1">
        {isConfirmingDelete ? (
          <div className="flex items-center space-x-1 animate-fade-in" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={handleDelete}
              className="p-1 rounded bg-rose-600 hover:bg-rose-500 text-white transition-colors"
              title="Confirm Delete"
            >
              <Check className="w-3 h-3" />
            </button>
            <button
              onClick={cancelDelete}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 transition-colors"
              title="Cancel"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleDelete}
            className="p-1 rounded text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
            title="Delete conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
}
