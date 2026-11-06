import React, { useState, useEffect } from 'react';
import Navbar from './components/common/Navbar';
import { fetchHealth } from './services/api';
import { MessageSquare, Image as ImageIcon, Box, Eye, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [healthData, setHealthData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function checkBackend() {
      try {
        const data = await fetchHealth();
        setHealthData(data);
        setIsConnected(true);
      } catch (err) {
        console.warn('Backend connection check warning:', err.message);
        setIsConnected(false);
      } finally {
        setLoading(false);
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Navigation */}
      <Navbar healthData={healthData} isConnected={isConnected} />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col justify-between">
        <div className="space-y-6">
          {/* Welcome Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-950/40 via-slate-900 to-indigo-950/30 border border-slate-800 shadow-xl">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <span>Conversational Image Recognition Intelligence</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1 max-w-2xl">
                  Upload tactical and surveillance imagery to perform deep-learning object detection,
                  bounding-box spatial extraction, and interactive visual question answering with continuous multi-turn dialogue memory.
                </p>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono bg-slate-900/80 px-3.5 py-2 rounded-lg border border-slate-700">
                <span className="text-slate-400">Models:</span>
                <span className="text-indigo-400 font-semibold">YOLOv8s</span>
                <span className="text-slate-600">+</span>
                <span className="text-sky-400 font-semibold">Salesforce BLIP VQA</span>
              </div>
            </div>
          </div>

          {/* Phase 1 Verification Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3">
              <div className="p-2.5 rounded-lg bg-blue-600/10 border border-blue-500/20 text-blue-400">
                <ImageIcon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Image Ingestion</h3>
                <p className="text-xs text-slate-400 mt-0.5">Secure local storage & MIME validation</p>
                <div className="mt-2 flex items-center space-x-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Pipeline Ready</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3">
              <div className="p-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
                <Box className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">YOLOv8s Detector</h3>
                <p className="text-xs text-slate-400 mt-0.5">Bounding box coordinates & confidence</p>
                <div className="mt-2 flex items-center space-x-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Apple MPS Benchmarked</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3">
              <div className="p-2.5 rounded-lg bg-sky-600/10 border border-sky-500/20 text-sky-400">
                <Eye className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">BLIP VQA Engine</h3>
                <p className="text-xs text-slate-400 mt-0.5">Visual reasoning & question comprehension</p>
                <div className="mt-2 flex items-center space-x-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>HuggingFace PyTorch</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3">
              <div className="p-2.5 rounded-lg bg-amber-600/10 border border-amber-500/20 text-amber-400">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Context Memory</h3>
                <p className="text-xs text-slate-400 mt-0.5">PostgreSQL 18 dialogue persistence</p>
                <div className="mt-2 flex items-center space-x-1 text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Async Session Pool</span>
                </div>
              </div>
            </div>
          </div>

          {/* Development Status Card */}
          <div className="p-6 rounded-xl bg-slate-900/40 border border-dashed border-slate-800 text-center py-12">
            <h4 className="text-base font-semibold text-slate-200">
              Phase 1 Architecture & Foundation Active
            </h4>
            <p className="text-xs text-slate-400 mt-2 max-w-lg mx-auto">
              FastAPI backend running on port 8000 with Apple MPS acceleration.
              React 18 frontend initialized with Vite & Tailwind CSS on port 5173.
              Ready for Phase 2 component tree development.
            </p>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
          <span>Bharat Electronics Limited (BEL) • Defense Electronics & Software</span>
          <span>100% On-Premise Air-Gapped AI System</span>
        </footer>
      </main>
    </div>
  );
}
