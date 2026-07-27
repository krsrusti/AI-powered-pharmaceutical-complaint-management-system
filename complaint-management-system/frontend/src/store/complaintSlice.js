import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage, uploadDocument, fetchComplaint } from "../api";

/**
 * This slice mirrors the backend's ChatResponse shape almost exactly —
 * deliberately, so components can read `complaint`, `diff`, `completeness`,
 * `duplicates`, `riskChanged` directly without a translation layer. The
 * `complaint` object itself is the single source of truth the form renders
 * from; there is no separate "form state" to keep in sync (per Requirement 6:
 * the form is the AI's output, never manually edited).
 */

const initialState = {
  complaintId: null,
  complaint: null,
  diff: [],
  completeness: null,
  duplicates: null,
  riskChanged: false,
  extractedTextPreview: null,
  status: "idle", // idle | loading | succeeded | failed
  error: null,
};

export const sendMessage = createAsyncThunk(
  "complaint/sendMessage",
  async ({ complaintId, message }, { rejectWithValue }) => {
    try {
      return await sendChatMessage(complaintId, message);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const uploadFile = createAsyncThunk(
  "complaint/uploadFile",
  async ({ complaintId, file }, { rejectWithValue }) => {
    try {
      return await uploadDocument(complaintId, file);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

export const loadComplaint = createAsyncThunk(
  "complaint/loadComplaint",
  async (complaintId, { rejectWithValue }) => {
    try {
      return await fetchComplaint(complaintId);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  }
);

const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    resetComplaint: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      // --- sendMessage ---
      .addCase(sendMessage.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "succeeded";
        applyResponse(state, action.payload);
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Failed to process message.";
      })

      // --- uploadFile ---
      .addCase(uploadFile.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.status = "succeeded";
        applyResponse(state, action.payload);
        state.extractedTextPreview = action.payload.extracted_text_preview || null;
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Failed to process document.";
      })

      // --- loadComplaint ---
      .addCase(loadComplaint.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(loadComplaint.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.complaintId = action.payload.complaint_id;
        state.complaint = action.payload;
      })
      .addCase(loadComplaint.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload || "Failed to load complaint.";
      });
  },
});

/** Shared by sendMessage and uploadFile — both return a ChatResponse-shaped payload. */
function applyResponse(state, payload) {
  state.complaintId = payload.complaint_id;
  state.complaint = payload.complaint;
  state.diff = payload.diff || [];
  state.completeness = payload.completeness;
  state.duplicates = payload.duplicates;
  state.riskChanged = payload.risk_changed;
}

export const { resetComplaint } = complaintSlice.actions;
export default complaintSlice.reducer;