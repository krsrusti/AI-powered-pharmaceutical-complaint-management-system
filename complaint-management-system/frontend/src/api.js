/**
 * Thin fetch wrappers around the FastAPI backend.
 *
 * Kept deliberately simple (no axios, no interceptors) since this is a
 * small surface area — three endpoints. Each function throws on non-2xx
 * so callers (Redux thunks) can catch and dispatch error state.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function handleResponse(response) {
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new Error(detail);
  }
  return response.json();
}

/**
 * Send a natural-language chat message. Pass complaintId=null to start a
 * new complaint; the backend generates and returns a new complaint_id.
 */
export async function sendChatMessage(complaintId, message) {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ complaint_id: complaintId, message }),
  });
  return handleResponse(response);
}

/**
 * Upload a document (PDF, email, image, txt). Pass complaintId=null to
 * start a new complaint from this document.
 */
export async function uploadDocument(complaintId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const url = new URL(`${BASE_URL}/upload`);
  if (complaintId) {
    url.searchParams.set("complaint_id", complaintId);
  }

  const response = await fetch(url.toString(), {
    method: "POST",
    body: formData,
  });
  return handleResponse(response);
}

export async function fetchComplaint(complaintId) {
  const response = await fetch(`${BASE_URL}/complaints/${complaintId}`);
  return handleResponse(response);
}

export async function fetchAllComplaints() {
  const response = await fetch(`${BASE_URL}/complaints`);
  return handleResponse(response);
}

export async function fetchAuditLog(complaintId) {
  const response = await fetch(`${BASE_URL}/complaints/${complaintId}/audit-log`);
  return handleResponse(response);
}

export async function submitComplaint(complaintId) {
  const response = await fetch(`${BASE_URL}/complaints/${complaintId}/submit`, {
    method: "PATCH",
  });
  return handleResponse(response);
}