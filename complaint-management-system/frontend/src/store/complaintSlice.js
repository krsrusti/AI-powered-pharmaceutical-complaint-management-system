import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  current: null, // the complaint currently being drafted/viewed
  list: [],
  riskLevel: null,
  riskRationale: null,
  flaggedTerms: [],
  completenessScore: null,
  missingFields: [],
  isComplete: false,
  duplicates: [],
  isDuplicate: false,
  status: "idle", // idle | loading | succeeded | failed
  error: null,
};

const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    setCurrentComplaint(state, action) {
      state.current = action.payload;
    },
    setComplaintList(state, action) {
      state.list = action.payload;
    },
    updateComplaintFields(state, action) {
      state.current = { ...state.current, ...action.payload };
    },
    setRiskAssessment(state, action) {
      const { risk_level, rationale, flagged_terms } = action.payload;
      state.riskLevel = risk_level;
      state.riskRationale = rationale;
      state.flaggedTerms = flagged_terms || [];
    },
    setCompleteness(state, action) {
      const { is_complete, completeness_score, missing_fields } = action.payload;
      state.isComplete = is_complete;
      state.completenessScore = completeness_score;
      state.missingFields = missing_fields || [];
    },
    setDuplicates(state, action) {
      const { is_duplicate, matches } = action.payload;
      state.isDuplicate = is_duplicate;
      state.duplicates = matches || [];
    },
    setStatus(state, action) {
      state.status = action.payload;
    },
    setError(state, action) {
      state.error = action.payload;
      state.status = "failed";
    },
    resetComplaintState() {
      return initialState;
    },
  },
});

export const {
  setCurrentComplaint,
  setComplaintList,
  updateComplaintFields,
  setRiskAssessment,
  setCompleteness,
  setDuplicates,
  setStatus,
  setError,
  resetComplaintState,
} = complaintSlice.actions;

export default complaintSlice.reducer;
