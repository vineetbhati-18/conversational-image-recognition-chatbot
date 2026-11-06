import React, { useState, useEffect } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { ChatProvider, useChat } from './context/ChatContext';
import Header from './components/common/Header';
import DashboardLayout from './components/common/DashboardLayout';
import ChatContainer from './components/chat/ChatContainer';
import ImageUploader from './components/image/ImageUploader';
import ImageCanvasViewer from './components/image/ImageCanvasViewer';
import ConfidenceSlider from './components/image/ConfidenceSlider';
import ObjectDetectionList from './components/image/ObjectDetectionList';
import SessionSidebar from './components/session/SessionSidebar';
import { fetchHealth } from './services/api';

function MainAppContent() {
  const [healthData, setHealthData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('vision'); // 'vision' | 'chat' for mobile

  const { activeSession, messages, activeImage } = useChat();

  useEffect(() => {
    async function checkBackend() {
      try {
        const data = await fetchHealth();
        setHealthData(data);
        setIsConnected(true);
      } catch (err) {
        setIsConnected(false);
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      {/* Enterprise Header */}
      <Header
        healthData={healthData}
        isConnected={isConnected}
        isSidebarOpen={isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main 3-Column Responsive Dashboard */}
      <DashboardLayout
        isSidebarOpen={isSidebarOpen}
        closeSidebar={() => setIsSidebarOpen(false)}
        activeTab={activeTab}
        sidebar={<SessionSidebar onClose={() => setIsSidebarOpen(false)} />}
        visionPanel={
          <div className="flex-1 flex flex-col space-y-4">
            <ImageUploader />
            {activeImage ? (
              <>
                <ImageCanvasViewer />
                <ConfidenceSlider />
                <ObjectDetectionList />
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-2xl p-6 text-center text-slate-500">
                <p className="text-xs">No image loaded. Upload an image above to activate the deep-learning vision canvas.</p>
              </div>
            )}
          </div>
        }
        chatPanel={<ChatContainer />}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <ChatProvider>
        <MainAppContent />
      </ChatProvider>
    </ThemeProvider>
  );
}
