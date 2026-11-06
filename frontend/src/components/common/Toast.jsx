import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, toast.duration || 4000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  const iconMap = {
    success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
    error: <AlertCircle className="w-4 h-4 text-rose-400" />,
    info: <Info className="w-4 h-4 text-indigo-400" />,
  };

  const borderMap = {
    success: 'border-emerald-500/30 bg-emerald-950/40 text-emerald-200',
    error: 'border-rose-500/30 bg-rose-950/40 text-rose-200',
    info: 'border-indigo-500/30 bg-indigo-950/40 text-indigo-200',
  };

  const type = toast.type || 'info';

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in fade-in slide-in-from-bottom-4 duration-200 max-w-sm">
      <div
        className={`flex items-start space-x-3 p-3.5 rounded-xl border backdrop-blur-md shadow-2xl ${
          borderMap[type] || borderMap.info
        }`}
      >
        <div className="shrink-0 mt-0.5">{iconMap[type] || iconMap.info}</div>
        <div className="flex-1 pr-2">
          {toast.title && <h4 className="text-xs font-semibold leading-tight">{toast.title}</h4>}
          <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{toast.message}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-slate-400 hover:text-slate-100 transition-colors shrink-0 p-0.5 rounded"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
