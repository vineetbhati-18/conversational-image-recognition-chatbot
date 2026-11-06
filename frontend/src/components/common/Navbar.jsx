import React from 'react';
import { ShieldCheck, Cpu, Database, Activity } from 'lucide-react';

export default function Navbar({ healthData, isConnected }) {
  return (
    <header className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Organization */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-bold tracking-wider shadow-inner">
            BEL
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-semibold text-white tracking-wide">
                Bharat Electronics Limited
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider rounded bg-blue-950 text-blue-400 border border-blue-800">
                Enterprise AI
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Conversational Image Recognition & Multi-Modal Intelligence System
            </p>
          </div>
        </div>

        {/* Telemetry & System Status */}
        <div className="flex items-center space-x-4 text-xs">
          {/* Hardware Device Pill */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-slate-300">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-mono uppercase text-[11px]">
              Device: {healthData?.acceleration?.active_device || 'Detecting...'}
            </span>
          </div>

          {/* Database Pill */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-slate-300">
            <Database className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-[11px]">
              DB: {healthData?.database?.status === 'connected' ? 'PostgreSQL 18' : 'Offline'}
            </span>
          </div>

          {/* Connection Status Pill */}
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-full border text-[11px] font-medium ${
              isConnected
                ? 'bg-emerald-950/60 border-emerald-700/60 text-emerald-300'
                : 'bg-rose-950/60 border-rose-700/60 text-rose-300'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            <span>{isConnected ? 'Backend Online' : 'Connecting...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
