import React, { useState } from 'react';
import { MessageSquare, Trash2, Check, X } from 'lucide-react';

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
      className={`group relative px-2.5 py-2 rounded-lg transition-all cursor-pointer text-xs flex items-center justify-between ${
        isActive
          ? 'bg-blue-600/15 border-l-2 border-blue-500 text-white'
          : 'hover:bg-slate-900/60 text-slate-400 hover:text-slate-200'
      }`}
    >
      <div className="flex items-center space-x-2 min-w-0 pr-1">
        <MessageSquare
          className={`w-3.5 h-3.5 shrink-0 ${
            isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-400'
          }`}
        />
        <div className="min-w-0">
          <p className="font-medium truncate text-xs">{session.title}</p>
          <span className="text-[10px] text-slate-500">{formattedDate}</span>
        </div>
      </div>

      {/* Delete Controls */}
      <div className="shrink-0 flex items-center">
        {isConfirmingDelete ? (
          <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={handleDelete}
              className="p-1 rounded bg-rose-600 hover:bg-rose-500 text-white"
              title="Confirm Delete"
            >
              <Check className="w-2.5 h-2.5" />
            </button>
            <button
              onClick={cancelDelete}
              className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white"
              title="Cancel"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={handleDelete}
            className="p-1 rounded text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
            title="Delete chat"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
}
