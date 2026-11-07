/**
 * API Service Client for BEL Conversational Image Recognition Backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

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
      : '');
  if (!backendBase) {
    return path;
  }
  const cleanBase = backendBase.endsWith('/') ? backendBase.slice(0, -1) : backendBase;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${cleanBase}${cleanPath}`;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function fetchSessions() {
  const response = await fetch(`${API_BASE_URL}/sessions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.status}`);
  }
  return response.json();
}

export async function fetchSessionDetail(sessionId) {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch session detail: ${response.status}`);
  }
  return response.json();
}

export async function createSession(title = 'New Conversation') {
  const response = await fetch(`${API_BASE_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.status}`);
  }
  return response.json();
}

export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!response.ok && response.status !== 204) {
    throw new Error(`Failed to delete session: ${response.status}`);
  }
  return true;
}

export async function uploadImage(file, sessionId) {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await fetch(`${API_BASE_URL}/images/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Upload failed with status: ${response.status}`);
  }
  return response.json();
}

export async function detectObjects(imageId, confidenceThreshold = 0.35) {
  const response = await fetch(
    `${API_BASE_URL}/images/${imageId}/detect?confidence_threshold=${confidenceThreshold}`,
    {
      method: 'POST',
    }
  );
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Detection failed with status: ${response.status}`);
  }
  return response.json();
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

  const response = await fetch(`${API_BASE_URL}/chat/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Message failed with status: ${response.status}`);
  }
  return response.json();
}
