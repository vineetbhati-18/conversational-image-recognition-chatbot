import React from 'react';

export default function DashboardLayout({
  sidebar,
  visionPanel,
  chatPanel,
  isSidebarOpen,
  closeSidebar,
  activeTab,
}) {
  return (
    <div className="flex-1 flex overflow-hidden relative">
      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Left Sidebar (Conversations & History) */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-72 sm:w-80 bg-slate-900 dark:bg-slate-950 border-r border-slate-800 dark:border-slate-800/80 flex flex-col transform transition-transform duration-200 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {sidebar}
      </aside>

      {/* Main Workspace (Vision Center + Chat Right) */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Center Panel: Vision & Canvas (Desktop or active mobile tab) */}
        <section
          className={`flex-1 flex flex-col overflow-y-auto border-r border-slate-800/80 p-4 lg:p-6 bg-slate-950/50 ${
            activeTab === 'vision' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {visionPanel}
        </section>

        {/* Right Panel: Chatbot Interface (Desktop or active mobile tab) */}
        <section
          className={`w-full lg:w-[420px] xl:w-[460px] 2xl:w-[500px] flex flex-col bg-slate-900/40 dark:bg-slate-950/60 border-slate-800/80 ${
            activeTab === 'chat' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {chatPanel}
        </section>
      </div>
    </div>
  );
}
