import { createSlice } from "@reduxjs/toolkit";
import { sendMessage, uploadFile } from "./complaintSlice";

/**
 * Chat history is kept separate from complaint state deliberately — the
 * complaint is "what the AI currently believes," the chat log is "how we
 * got here." Listens to complaintSlice's thunks via extraReducers rather
 * than components dispatching two separate actions per turn, so the two
 * slices can't drift out of sync (e.g. a message added without a
 * corresponding AI reply).
 */

let messageIdCounter = 0;
function nextId() {
  messageIdCounter += 1;
  return `msg-${messageIdCounter}`;
}

const initialState = {
  messages: [],       // { id, role: 'user' | 'ai', text, timestamp }
  isThinking: false,
  isUploading: false,
  uploadStatusMessage: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage: (state, action) => {
      state.messages.push({
        id: nextId(),
        role: "user",
        text: action.payload,
        timestamp: new Date().toISOString(),
      });
    },
    clearChat: (state) => {
      state.messages = [];
      state.isThinking = false;
      state.isUploading = false;
      state.uploadStatusMessage = null;
    },
    setUploadStatusMessage: (state, action) => {
      state.uploadStatusMessage = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // --- text chat turn ---
      .addCase(sendMessage.pending, (state) => {
        state.isThinking = true;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isThinking = false;
        state.messages.push({
          id: nextId(),
          role: "ai",
          text: action.payload.ai_message,
          timestamp: new Date().toISOString(),
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isThinking = false;
        state.messages.push({
          id: nextId(),
          role: "ai",
          text: action.payload || "Something went wrong processing that message.",
          isError: true,
          timestamp: new Date().toISOString(),
        });
      })

      // --- document upload turn ---
      .addCase(uploadFile.pending, (state) => {
        state.isUploading = true;
        state.isThinking = true;
        state.uploadStatusMessage = "Analyzing document content and extracting key details...";
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.isUploading = false;
        state.isThinking = false;
        state.uploadStatusMessage = null;
        state.messages.push({
          id: nextId(),
          role: "ai",
          text: action.payload.ai_message,
          timestamp: new Date().toISOString(),
        });
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.isUploading = false;
        state.isThinking = false;
        state.uploadStatusMessage = null;
        state.messages.push({
          id: nextId(),
          role: "ai",
          text: action.payload || "Something went wrong processing that document.",
          isError: true,
          timestamp: new Date().toISOString(),
        });
      });
  },
});

export const { addUserMessage, clearChat, setUploadStatusMessage } = chatSlice.actions;
export default chatSlice.reducer;