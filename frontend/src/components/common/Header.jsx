import React from 'react';
import { Cpu, Database, Sun, Moon, Menu, X } from 'lucide-react';
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
    <header className="bg-slate-900/90 border-b border-slate-800/60 sticky top-0 z-40 px-4 py-2.5 transition-colors backdrop-blur-md">
      <div className="max-w-[1920px] mx-auto flex items-center justify-between">
        {/* Left: Mobile Toggle & Brand */}
        <div className="flex items-center space-x-3">
          <button
            onClick={toggleSidebar}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
            aria-label="Toggle menu"
          >
            {isSidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
              BEL
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-white tracking-tight">
                  BEL Vision AI
                </span>
                <span className="text-[10px] text-slate-500 hidden sm:inline">
                  Image Recognition & Chat
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Mobile View Switcher */}
        <div className="flex lg:hidden bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/50">
          <button
            onClick={() => setActiveTab('vision')}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all ${
              activeTab === 'vision'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Vision
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all ${
              activeTab === 'chat'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Chat
          </button>
        </div>

        {/* Right: Minimal Status & Theme */}
        <div className="flex items-center space-x-3 text-xs">
          {/* Hardware Device */}
          <div className="hidden sm:flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <Cpu className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-mono">
              {healthData?.acceleration?.active_device?.toUpperCase() || 'MPS'}
            </span>
          </div>

          {/* Database */}
          <div className="hidden md:flex items-center space-x-1.5 text-slate-400 text-[11px]">
            <Database className="w-3.5 h-3.5 text-amber-400" />
            <span>PostgreSQL</span>
          </div>

          {/* Connection Status */}
          <div className="flex items-center space-x-1.5 text-[11px]">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400' : 'bg-rose-500 animate-pulse'
              }`}
            />
            <span className="text-slate-400 hidden sm:inline">
              {isConnected ? 'Connected' : 'Offline'}
            </span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </header>
  );
}
