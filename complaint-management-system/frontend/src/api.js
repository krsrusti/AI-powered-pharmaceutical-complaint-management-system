import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export const sendChatMessage = (sessionId, message, complaintId = null) =>
  api.post("/chat", { session_id: sessionId, message, complaint_id: complaintId });

export const getChatHistory = (sessionId) => api.get(`/chat/${sessionId}/history`);

export const listComplaints = () => api.get("/complaints");

export const getComplaint = (id) => api.get(`/complaints/${id}`);

export const createComplaint = (payload) => api.post("/complaints", payload);

export const updateComplaint = (id, payload) => api.patch(`/complaints/${id}`, payload);

export const deleteComplaint = (id) => api.delete(`/complaints/${id}`);

export const checkDuplicates = (id) => api.get(`/complaints/${id}/duplicates`);

export default api;
