import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  fetchSessions,
  fetchSessionDetail,
  createSession as apiCreateSession,
  deleteSession as apiDeleteSession,
  uploadImage as apiUploadImage,
  sendChatMessage as apiSendChatMessage,
  detectObjects as apiDetectObjects,
} from '../services/api';

const ChatContext = createContext();

const LOCAL_STORAGE_SESSION_KEY = 'bel_active_session_id';

const DEFAULT_WELCOME_MESSAGE = {
  id: 'msg-welcome',
  sender_type: 'assistant',
  content:
    'Welcome to the Bharat Electronics Limited (BEL) Conversational Image Recognition System. Upload an aerial, tactical, or standard image to detect objects, inspect bounding boxes, and ask natural-language questions with multi-turn context retention.',
  created_at: new Date().toISOString(),
  metadata: { system: true },
};

export function ChatProvider({ children }) {
  // Session State
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(() => {
    try {
      return localStorage.getItem(LOCAL_STORAGE_SESSION_KEY) || null;
    } catch {
      return null;
    }
  });

  // Active Image State & Detection Telemetry
  const [activeImage, setActiveImage] = useState(null);
  // shape: { id, url, backendUrl, name, size, width, height, file }

  // Detected Objects from YOLOv8
  const [detectedObjects, setDetectedObjects] = useState([]);
  const [selectedObjectId, setSelectedObjectId] = useState(null);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.40);

  // Messages / Chat Conversation History
  const [messages, setMessages] = useState([DEFAULT_WELCOME_MESSAGE]);

  // Loading & Processing States
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSessionLoading, setIsSessionLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Fetch full session details (messages, image, detections) from backend
  const loadSessionDetail = useCallback(async (sessionId) => {
    if (!sessionId) return null;
    setIsSessionLoading(true);
    setErrorMessage(null);

    try {
      const detail = await fetchSessionDetail(sessionId);
      if (detail) {
        // 1. Restore Conversation Messages
        if (detail.messages && detail.messages.length > 0) {
          setMessages(detail.messages);
        } else {
          setMessages([
            {
              id: `msg-welcome-${detail.id}`,
              sender_type: 'assistant',
              content: `Started conversation: "${detail.title || 'New Conversation'}". Upload an image to begin object detection and conversational analysis.`,
              created_at: detail.created_at || new Date().toISOString(),
              metadata: { system: true },
            },
          ]);
        }

        // 2. Restore Image and YOLO Detected Objects
        if (detail.images && detail.images.length > 0) {
          // Latest image is first (order_by created_at.desc())
          const latestImg = detail.images[0];
          setActiveImage({
            id: latestImg.id,
            url: latestImg.url,
            backendUrl: latestImg.url,
            name: latestImg.filename,
            size: `${(latestImg.file_size_bytes / (1024 * 1024)).toFixed(2)} MB`,
            width: latestImg.width,
            height: latestImg.height,
          });
          setDetectedObjects(latestImg.detected_objects || []);
        } else {
          setActiveImage(null);
          setDetectedObjects([]);
        }

        setSelectedObjectId(null);
        setActiveSessionId(detail.id);
        try {
          localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, detail.id);
        } catch {
          // ignore storage errors
        }
        return detail;
      }
    } catch (err) {
      console.warn('Failed to load session detail:', err.message);
      try {
        localStorage.removeItem(LOCAL_STORAGE_SESSION_KEY);
      } catch {
        // ignore storage errors
      }
    } finally {
      setIsSessionLoading(false);
    }
    return null;
  }, []);

  // Application Startup: Fetch all saved sessions from FastAPI backend and restore active session
  useEffect(() => {
    async function initSessions() {
      setIsSessionLoading(true);
      try {
        const backendSessions = await fetchSessions();
        if (backendSessions && backendSessions.length > 0) {
          setSessions(backendSessions);

          // Restore last active session from localStorage or default to most recent session
          let targetSessionId = null;
          try {
            const savedSessionId = localStorage.getItem(LOCAL_STORAGE_SESSION_KEY);
            const found = backendSessions.find((s) => s.id === savedSessionId);
            targetSessionId = found ? found.id : backendSessions[0].id;
          } catch {
            targetSessionId = backendSessions[0].id;
          }

          if (targetSessionId) {
            await loadSessionDetail(targetSessionId);
          }
        } else {
          // No sessions exist yet in PostgreSQL -> create the initial session
          const newSession = await apiCreateSession('Tactical Reconnaissance Analysis').catch(() => null);
          if (newSession) {
            setSessions([newSession]);
            setActiveSessionId(newSession.id);
            try {
              localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, newSession.id);
            } catch {
              // ignore
            }
            setMessages([DEFAULT_WELCOME_MESSAGE]);
          }
        }
      } catch (err) {
        console.warn('Backend session fetch note:', err.message);
      } finally {
        setIsSessionLoading(false);
      }
    }

    initSessions();
  }, [loadSessionDetail]);

  // Switch Active Session
  const switchSession = useCallback(async (sessionId) => {
    if (!sessionId || sessionId === activeSessionId) return;
    await loadSessionDetail(sessionId);
  }, [activeSessionId, loadSessionDetail]);

  // Create New Session
  const createNewSession = useCallback(async (customTitle) => {
    const title = customTitle || `Recon Session #${sessions.length + 1}`;
    try {
      const newSession = await apiCreateSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      try {
        localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, newSession.id);
      } catch {
        // ignore
      }
      setActiveImage(null);
      setDetectedObjects([]);
      setSelectedObjectId(null);
      setMessages([
        {
          id: `msg-${Date.now()}`,
          sender_type: 'assistant',
          content: `Started new conversation: "${newSession.title}". Please upload an image to begin object detection and conversational analysis.`,
          created_at: new Date().toISOString(),
          metadata: { system: true },
        },
      ]);
      return newSession;
    } catch (err) {
      setErrorMessage(`Failed to create session: ${err.message}`);
    }
  }, [sessions.length]);

  // Delete Session from Backend & State
  const deleteSession = useCallback(async (sessionId) => {
    try {
      await apiDeleteSession(sessionId);
    } catch (err) {
      console.warn('API delete session error:', err.message);
    }

    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== sessionId);
      if (activeSessionId === sessionId) {
        if (filtered.length > 0) {
          const nextId = filtered[0].id;
          loadSessionDetail(nextId);
        } else {
          setActiveSessionId(null);
          try {
            localStorage.removeItem(LOCAL_STORAGE_SESSION_KEY);
          } catch {
            // ignore
          }
          setActiveImage(null);
          setDetectedObjects([]);
          setMessages([DEFAULT_WELCOME_MESSAGE]);
        }
      }
      return filtered;
    });
  }, [activeSessionId, loadSessionDetail]);

  // Upload & Process Image
  const handleImageUpload = useCallback(async (file) => {
    if (!file) return;
    setIsUploading(true);
    setErrorMessage(null);

    try {
      // 1. Revoke previous local object URL if existing to free memory
      if (activeImage?.url && activeImage.url.startsWith('blob:')) {
        URL.revokeObjectURL(activeImage.url);
      }

      // Ensure active session exists in backend
      let targetSessionId = activeSessionId;
      if (!targetSessionId) {
        const created = await apiCreateSession(`Recon (${file.name})`);
        if (created) {
          targetSessionId = created.id;
          setActiveSessionId(created.id);
          setSessions((prev) => [created, ...prev]);
          try {
            localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, created.id);
          } catch {
            // ignore
          }
        }
      }

      // Create client-side preview
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

      // 2. Call backend upload endpoint
      const response = await apiUploadImage(file, targetSessionId);
      if (response) {
        if (response.id) newImagePayload.id = response.id;
        if (response.url) {
          newImagePayload.url = response.url;
          newImagePayload.backendUrl = response.url;
        }

        if (response.detected_objects && response.detected_objects.length > 0) {
          setDetectedObjects(response.detected_objects);
          const classesSummary = [
            ...new Set(response.detected_objects.map((o) => o.class_name)),
          ].join(', ');

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
        } else {
          setDetectedObjects([]);
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${Date.now()}`,
              sender_type: 'system',
              content: `Image "${file.name}" ingested. No distinct objects identified above the current confidence threshold. You may lower the confidence slider or ask questions directly.`,
              created_at: new Date().toISOString(),
              metadata: { image_id: newImagePayload.id },
            },
          ]);
        }

        // Refresh session list to update titles and timestamps
        const updatedSessions = await fetchSessions().catch(() => null);
        if (updatedSessions) setSessions(updatedSessions);
        return;
      }
    } catch (err) {
      setErrorMessage(`Image processing failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  }, [activeImage, activeSessionId]);

  // Remove Active Image
  const removeImage = useCallback(() => {
    if (activeImage?.url && activeImage.url.startsWith('blob:')) {
      URL.revokeObjectURL(activeImage.url);
    }
    setActiveImage(null);
    setDetectedObjects([]);
    setSelectedObjectId(null);
  }, [activeImage]);

  // Send Chat Message
  const sendMessage = useCallback(async (text) => {
    if (!text || !text.trim()) return;
    const trimmed = text.trim();

    // Ensure session exists
    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      const created = await apiCreateSession(trimmed.slice(0, 30));
      if (created) {
        targetSessionId = created.id;
        setActiveSessionId(created.id);
        setSessions((prev) => [created, ...prev]);
        try {
          localStorage.setItem(LOCAL_STORAGE_SESSION_KEY, created.id);
        } catch {
          // ignore
        }
      }
    }

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
      const res = await apiSendChatMessage(
        targetSessionId,
        trimmed,
        activeImage?.id || null,
        confidenceThreshold
      );

      if (res && res.content) {
        setMessages((prev) => [...prev, res]);
      }

      // Update sessions list to reflect latest activity
      const updatedSessions = await fetchSessions().catch(() => null);
      if (updatedSessions) setSessions(updatedSessions);
    } catch (err) {
      console.warn('Backend chat API error, using fallback:', err.message);
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-ast-${Date.now()}`,
          sender_type: 'assistant',
          content: activeImage
            ? `Regarding "${activeImage.name}": ${err.message}`
            : `Please upload an image first so I can inspect visual objects and answer questions about it.`,
          created_at: new Date().toISOString(),
          metadata: { error: true },
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [activeSessionId, activeImage, confidenceThreshold]);

  return (
    <ChatContext.Provider
      value={{
        sessions,
        activeSessionId,
        activeSession: sessions.find((s) => s.id === activeSessionId) || sessions[0] || null,
        createNewSession,
        switchSession,
        deleteSession,
        loadSessionDetail,
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
        isSessionLoading,
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
