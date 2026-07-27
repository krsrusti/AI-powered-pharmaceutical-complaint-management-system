import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  sessionId: null,
  messages: [], // { role: 'user' | 'assistant', content: string, timestamp?: string }
  isSending: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    setSessionId(state, action) {
      state.sessionId = action.payload;
    },
    setMessages(state, action) {
      state.messages = action.payload;
    },
    addMessage(state, action) {
      state.messages.push(action.payload);
    },
    setSending(state, action) {
      state.isSending = action.payload;
    },
    setChatError(state, action) {
      state.error = action.payload;
    },
    resetChat() {
      return initialState;
    },
  },
});

export const { setSessionId, setMessages, addMessage, setSending, setChatError, resetChat } =
  chatSlice.actions;

export default chatSlice.reducer;
