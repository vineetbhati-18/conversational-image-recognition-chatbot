/**
 * API Service Client for BEL Conversational Image Recognition Backend
 */

const DEFAULT_PROD_API = 'https://bel-chatbot-api.onrender.com/api/v1';
const DEFAULT_PROD_BACKEND = 'https://bel-chatbot-api.onrender.com';

const isProductionHost =
  typeof window !== 'undefined' &&
  (window.location.hostname.includes('vercel.app') || window.location.hostname !== 'localhost');

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD || isProductionHost
    ? DEFAULT_PROD_API
    : '/api/v1');

/**
 * Resolves static media paths to absolute URLs in production cloud environments.
 */
export function resolveMediaUrl(path) {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:')) {
    return path;
  }
  const backendBase =
    import.meta.env.VITE_BACKEND_URL ||
    (import.meta.env.VITE_API_BASE_URL
      ? import.meta.env.VITE_API_BASE_URL.replace(/\/api\/v1\/?$/, '')
      : (import.meta.env.PROD || isProductionHost ? DEFAULT_PROD_BACKEND : ''));
  if (!backendBase) {
    return path;
  }
  const cleanBase = backendBase.endsWith('/') ? backendBase.slice(0, -1) : backendBase;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

/**
 * Robust fetch wrapper that inspects network failures, timeouts, and detailed error payloads.
 */
async function safeApiFetch(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
      throw new Error(
        'Backend connection failed. The server may be waking up from free-tier sleep or rebooting. Please try again in a few moments.'
      );
    }
    throw err;
  }

  if (!response.ok) {
    let errorMessage = '';
    try {
      const errorData = await response.json();
      errorMessage = errorData.error || errorData.detail || errorData.message || JSON.stringify(errorData);
    } catch {
      const text = await response.text().catch(() => '');
      errorMessage = text || `HTTP ${response.status} ${response.statusText}`;
    }
    throw new Error(errorMessage || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchHealth() {
  return safeApiFetch(`${API_BASE_URL}/health`);
}

export async function fetchSessions() {
  return safeApiFetch(`${API_BASE_URL}/sessions`);
}

export async function fetchSessionDetail(sessionId) {
  return safeApiFetch(`${API_BASE_URL}/sessions/${sessionId}`);
}

export async function createSession(title = 'New Conversation') {
  return safeApiFetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    if (!response.ok && response.status !== 204) {
      throw new Error(`Failed to delete session: ${response.status}`);
    }
    return true;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
      throw new Error('Connection lost while deleting session.');
    }
    throw err;
  }
}

export async function uploadImage(file, sessionId, retryCount = 1) {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  try {
    return await safeApiFetch(`${API_BASE_URL}/images/upload`, {
      method: 'POST',
      body: formData,
    });
  } catch (err) {
    if (retryCount > 0 && (err.message.includes('waking up') || err.message.includes('Backend connection'))) {
      await new Promise((resolve) => setTimeout(resolve, 2500));
      return uploadImage(file, sessionId, retryCount - 1);
    }
    throw err;
  }
}

export async function detectObjects(imageId, confidenceThreshold = 0.35) {
  return safeApiFetch(
    `${API_BASE_URL}/images/${imageId}/detect?confidence_threshold=${confidenceThreshold}`,
    {
      method: 'POST',
    }
  );
}

export async function sendChatMessage(sessionId, content, imageId = null, confidenceThreshold = null) {
  const payload = {
    session_id: sessionId,
    content,
    image_id: imageId,
  };
  if (confidenceThreshold !== null && confidenceThreshold !== undefined) {
    payload.confidence_threshold = confidenceThreshold;
  }

  return safeApiFetch(`${API_BASE_URL}/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
