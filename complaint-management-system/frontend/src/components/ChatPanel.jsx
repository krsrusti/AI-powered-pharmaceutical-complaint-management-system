import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendChatMessage } from "../api";
import { addMessage, setSending, setSessionId } from "../store/chatSlice";
import {
  setCompleteness,
  setDuplicates,
  setRiskAssessment,
  updateComplaintFields,
} from "../store/complaintSlice";

function ensureSessionId(sessionId, dispatch) {
  if (sessionId) return sessionId;
  const newId = crypto.randomUUID();
  dispatch(setSessionId(newId));
  return newId;
}

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { sessionId, messages, isSending } = useSelector((state) => state.chat);
  const complaintId = useSelector((state) => state.complaint.current?.id ?? null);
  const [draft, setDraft] = useState("");

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || isSending) return;

    const activeSessionId = ensureSessionId(sessionId, dispatch);
    dispatch(addMessage({ role: "user", content: text }));
    setDraft("");
    dispatch(setSending(true));

    try {
      const { data } = await sendChatMessage(activeSessionId, text, complaintId);
      dispatch(addMessage({ role: "assistant", content: data.reply }));

      if (data.completeness_check) dispatch(setCompleteness(data.completeness_check));
      if (data.duplicate_check) dispatch(setDuplicates(data.duplicate_check));
      if (data.risk_assessment) dispatch(setRiskAssessment(data.risk_assessment));
      if (data.updated_complaint) dispatch(updateComplaintFields(data.updated_complaint));
    } catch (err) {
      dispatch(
        addMessage({
          role: "assistant",
          content: "Sorry, something went wrong sending that message.",
        })
      );
    } finally {
      dispatch(setSending(false));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="panel chat-panel">
      <h2>File a Complaint</h2>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-message--${m.role}`}>
            {m.content}
          </div>
        ))}
        {isSending && <div className="chat-message chat-message--assistant">Typing…</div>}
      </div>
      <div className="chat-input-row">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your complaint..."
          rows={3}
        />
        <button onClick={handleSend} disabled={isSending || !draft.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
