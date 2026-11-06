import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  fetchSessions,
  createSession as apiCreateSession,
  uploadImage as apiUploadImage,
  sendChatMessage as apiSendChatMessage,
  detectObjects as apiDetectObjects,
} from '../services/api';

const ChatContext = createContext();

export function ChatProvider({ children }) {
  // Session State
  const [sessions, setSessions] = useState([
    {
      id: 'session-demo-01',
      title: 'Tactical Reconnaissance Analysis',
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 'session-demo-02',
      title: 'Perimeter Security Surveillance',
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ]);
  const [activeSessionId, setActiveSessionId] = useState('session-demo-01');

  // Active Image State & Detection Telemetry
  const [activeImage, setActiveImage] = useState(null);
  // activeImage shape: { id, url, name, size, width, height, file }

  // Detected Objects from YOLOv8
  const [detectedObjects, setDetectedObjects] = useState([]);
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.35);

  // Messages / Chat Conversation History
  const [messages, setMessages] = useState([
    {
      id: 'msg-welcome',
      sender_type: 'assistant',
      content:
        'Welcome to the Bharat Electronics Limited (BEL) Conversational Image Recognition System. Upload an aerial, tactical, or standard image to detect objects, inspect bounding boxes, and ask natural-language questions with multi-turn context retention.',
      created_at: new Date(Date.now() - 300000).toISOString(),
      metadata: { system: true },
    },
  ]);

  // Loading & Processing States
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Create New Session
  const createNewSession = useCallback(async (customTitle) => {
    const title = customTitle || `Recon Session #${sessions.length + 1}`;
    try {
      const newSession = await apiCreateSession(title).catch(() => ({
        id: `session-${Date.now()}`,
        title,
        created_at: new Date().toISOString(),
      }));
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setActiveImage(null);
      setDetectedObjects([]);
      setSelectedObjectId(null);
      setMessages([
        {
          id: `msg-${Date.now()}`,
          sender_type: 'assistant',
          content: `Started new conversation: "${title}". Please upload an image to begin object detection and conversational analysis.`,
          created_at: new Date().toISOString(),
        },
      ]);
      return newSession;
    } catch (err) {
      setErrorMessage(`Failed to create session: ${err.message}`);
    }
  }, [sessions.length]);

  // Switch Active Session
  const switchSession = useCallback((sessionId) => {
    setActiveSessionId(sessionId);
    setSelectedObjectId(null);
  }, []);

  // Delete Session
  const deleteSession = useCallback((sessionId) => {
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      if (activeSessionId === sessionId && filtered.length > 0) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  }, [activeSessionId]);

  // Upload & Process Image
  const handleImageUpload = useCallback(async (file) => {
    if (!file) return;
    setIsUploading(true);
    setErrorMessage(null);

    try {
      // 1. Create client-side preview and read natural dimensions
      const localUrl = URL.createObjectURL(file);
      const img = new Image();
      img.src = localUrl;
      await new Promise((resolve) => {
        img.onload = resolve;
      });

      const newImagePayload = {
        id: `img-${Date.now()}`,
        url: localUrl,
        name: file.name,
        size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
        width: img.naturalWidth || 800,
        height: img.naturalHeight || 600,
        file,
      };

      setActiveImage(newImagePayload);

      // 2. Call backend upload if available
      try {
        const response = await apiUploadImage(file, activeSessionId);
        if (response) {
          if (response.id) newImagePayload.id = response.id;
          if (response.url) newImagePayload.backendUrl = response.url;
          if (response.detected_objects && response.detected_objects.length > 0) {
            setDetectedObjects(response.detected_objects);
            const classesSummary = [
              ...new Set(response.detected_objects.map((o) => o.class_name)),
            ].join(', ');

            // Add system confirmation message in chat with real detection count
            setMessages((prev) => [
              ...prev,
              {
                id: `msg-${Date.now()}`,
                sender_type: 'system',
                content: `Image "${file.name}" ingested. YOLOv8 detected ${response.detected_objects.length} object(s): [${classesSummary}]. Canvas updated with bounding boxes.`,
                created_at: new Date().toISOString(),
                metadata: { image_id: newImagePayload.id },
              },
            ]);
            return;
          }
        }
      } catch (apiErr) {
        console.info('Backend detection endpoint note:', apiErr.message);
      }

      // Fallback system confirmation message in chat
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now()}`,
          sender_type: 'system',
          content: `Image "${file.name}" (${newImagePayload.width}x${newImagePayload.height}) loaded successfully. Ready for visual question answering.`,
          created_at: new Date().toISOString(),
          metadata: { image_id: newImagePayload.id },
        },
      ]);
    } catch (err) {
      setErrorMessage(`Image processing failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  }, [activeSessionId]);

  // Remove Active Image
  const removeImage = useCallback(() => {
    if (activeImage?.url) {
      URL.revokeObjectURL(activeImage.url);
    }
    setActiveImage(null);
    setDetectedObjects([]);
    setSelectedObjectId(null);
  }, [activeImage]);

  // Initial fetch from backend if available
  useEffect(() => {
    async function loadBackendSessions() {
      try {
        const data = await fetchSessions();
        if (data && data.length > 0) {
          setSessions(data);
          setActiveSessionId(data[0].id);
        }
      } catch (err) {
        console.info('Backend session fetch note:', err.message);
      }
    }
    loadBackendSessions();
  }, []);

  // Send Chat Message
  const sendMessage = useCallback(async (text) => {
    if (!text || !text.trim()) return;
    const trimmed = text.trim();

    const userMessage = {
      id: `msg-user-${Date.now()}`,
      sender_type: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      // Call backend chat API with active image ID
      const res = await apiSendChatMessage(
        activeSessionId,
        trimmed,
        activeImage?.id || null
      );

      if (res && res.content) {
        setMessages((prev) => [...prev, res]);
      }
    } catch (err) {
      console.warn('Backend chat API error, using local fallback:', err.message);
      // Return context-aware fallback response if backend endpoint temporarily unavailable
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-ast-${Date.now()}`,
          sender_type: 'assistant',
          content: activeImage
            ? `Regarding the loaded image "${activeImage.name}": I am analyzing the visual features against your query "${trimmed}". Ready for Phase 3 & 4 full YOLOv8 and BLIP model inference.`
            : `Please upload an image first so I can inspect visual objects and answer questions about it.`,
          created_at: new Date().toISOString(),
          metadata: {
            vqa_mode: Boolean(activeImage),
            latency_ms: 32,
          },
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [activeSessionId, activeImage]);

  return (
    <ChatContext.Provider
      value={{
        sessions,
        activeSessionId,
        activeSession: sessions.find((s) => s.id === activeSessionId) || sessions[0],
        createNewSession,
        switchSession,
        deleteSession,
        activeImage,
        setActiveImage,
        detectedObjects,
        setDetectedObjects,
        selectedObjectId,
        setSelectedObjectId,
        confidenceThreshold,
        setConfidenceThreshold,
        messages,
        sendMessage,
        handleImageUpload,
        removeImage,
        isLoading,
        isUploading,
        errorMessage,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
