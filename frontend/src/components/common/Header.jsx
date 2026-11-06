import React from 'react';
import { Cpu, Database, Sun, Moon, Menu, X, Shield, Activity } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export default function Header({
  healthData,
  isConnected,
  isSidebarOpen,
  toggleSidebar,
  activeTab,
  setActiveTab,
}) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-slate-900/95 dark:bg-slate-950/95 light:bg-white/95 border-b border-slate-800 dark:border-slate-800/80 light:border-slate-200 sticky top-0 z-40 px-4 lg:px-6 py-2.5 transition-colors duration-200 backdrop-blur-md">
      <div className="max-w-[1920px] mx-auto flex items-center justify-between">
        {/* Left: Mobile Sidebar Toggle & Branding */}
        <div className="flex items-center space-x-3">
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 dark:hover:bg-slate-800 light:hover:bg-slate-100 transition-colors lg:hidden"
            aria-label="Toggle navigation drawer"
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-700 to-indigo-900 border border-blue-400/30 flex items-center justify-center text-white font-extrabold text-sm tracking-wider shadow-md">
              BEL
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-bold text-white dark:text-white light:text-slate-900 tracking-tight">
                  Bharat Electronics Limited
                </span>
                <span className="hidden sm:inline-flex px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-blue-900/60 dark:bg-blue-950 text-blue-300 border border-blue-700/50">
                  Tactical AI
                </span>
              </div>
              <p className="text-[11px] text-slate-400 dark:text-slate-400 light:text-slate-500 hidden md:block">
                Conversational Image Recognition & Object Detection Intelligence
              </p>
            </div>
          </div>
        </div>

        {/* Center: Mobile Navigation Switcher (Vision vs Chat) */}
        <div className="flex lg:hidden bg-slate-800/80 dark:bg-slate-900 p-1 rounded-lg border border-slate-700/50">
          <button
            onClick={() => setActiveTab('vision')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              activeTab === 'vision'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Vision Canvas
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Chatbot
          </button>
        </div>

        {/* Right: Telemetry, Hardware & Theme Controls */}
        <div className="flex items-center space-x-2.5 sm:space-x-3.5">
          {/* Hardware Device Pill (Apple MPS) */}
          <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/70 dark:bg-slate-900 border border-slate-700/60 text-slate-300 text-xs shadow-sm">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-mono text-[11px] font-medium uppercase">
              {healthData?.acceleration?.active_device
                ? `${healthData.acceleration.active_device.toUpperCase()} (M4)`
                : 'MPS ACCEL'}
            </span>
          </div>

          {/* Database Status Pill */}
          <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/70 dark:bg-slate-900 border border-slate-700/60 text-slate-300 text-xs shadow-sm">
            <Database className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-[11px]">
              {healthData?.database?.status === 'connected' ? 'PostgreSQL' : 'DB Ready'}
            </span>
          </div>

          {/* Backend Online Indicator */}
          <div
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
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
            <span className="text-[11px] hidden sm:inline">
              {isConnected ? 'Online' : 'Reconnecting'}
            </span>
          </div>

          {/* Theme Switcher Toggle */}
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg bg-slate-800/80 dark:bg-slate-900 border border-slate-700/70 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-300" />
            ) : (
              <Moon className="w-4 h-4 text-slate-300" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
