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
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 bg-black/50 z-30 lg:hidden backdrop-blur-sm"
          aria-hidden="true"
        />
      )}

      {/* Left Sidebar (Conversations) */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-30 w-64 sm:w-72 bg-slate-950 flex flex-col transform transition-transform duration-200 ease-in-out ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {sidebar}
      </aside>

      {/* Workspace */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Center: Vision Canvas */}
        <section
          className={`flex-1 flex flex-col overflow-y-auto border-r border-slate-800/60 p-3 lg:p-4 bg-slate-950/40 ${
            activeTab === 'vision' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {visionPanel}
        </section>

        {/* Right: Chat */}
        <section
          className={`w-full lg:w-[380px] xl:w-[420px] 2xl:w-[460px] flex flex-col bg-slate-950/20 ${
            activeTab === 'chat' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {chatPanel}
        </section>
      </div>
    </div>
  );
}
