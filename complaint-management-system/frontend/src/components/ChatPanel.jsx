import { useState, useRef } from "react";
import { useSelector, useDispatch } from "react-redux";
import { Sparkles, UploadCloud, FileText, Send, Loader2 } from "lucide-react";
import { sendMessage, uploadFile } from "../store/complaintSlice";
import { addUserMessage } from "../store/chatSlice";

const SUPPORTED_FORMATS = "PDF, DOCX, TXT, EML";
const MAX_FILE_SIZE_MB = 10;

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { complaintId } = useSelector((s) => s.complaint);
  const { messages, isThinking, isUploading, uploadStatusMessage } = useSelector((s) => s.chat);

  const [inputText, setInputText] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const handleSend = () => {
    const trimmed = inputText.trim();
    if (!trimmed || isThinking) return;

    dispatch(addUserMessage(trimmed));
    dispatch(sendMessage({ complaintId, message: trimmed }));
    setInputText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelected = (file) => {
    if (!file) return;
    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      dispatch(addUserMessage(`Attempted to upload ${file.name} (exceeds ${MAX_FILE_SIZE_MB}MB limit)`));
      return;
    }
    dispatch(addUserMessage(`Uploaded document: ${file.name}`));
    dispatch(uploadFile({ complaintId, file }));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFileSelected(file);
  };

  const busy = isThinking || isUploading;

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-title">
          <Sparkles size={18} />
          <h2>AI Complaint Intake Assistant</h2>
        </div>
        <span className="beta-badge">BETA</span>
      </div>

      <div
        className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <UploadCloud size={22} />
        <p>
          Drag &amp; drop complaint document here <br />
          or <span className="link-text">click to browse</span>
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.eml,.txt,.png,.jpg,.jpeg,.webp,.bmp"
          hidden
          onChange={(e) => handleFileSelected(e.target.files?.[0])}
        />
      </div>

      <div className="divider-with-text">
        <span>OR</span>
      </div>

      <button
        className="paste-text-btn"
        onClick={() => document.getElementById("chat-textarea")?.focus()}
      >
        <FileText size={16} />
        Paste Complaint Text / Email
      </button>

      <div className="format-info">
        Supported formats: {SUPPORTED_FORMATS}
        <br />
        Max file size: {MAX_FILE_SIZE_MB}MB
      </div>

      {isUploading && uploadStatusMessage && (
        <div className="extraction-progress">
          <div className="progress-label">
            <span>EXTRACTION PROGRESS</span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" />
          </div>
          <p className="progress-status">{uploadStatusMessage}</p>
        </div>
      )}

      <div className="chat-messages">
        <div className="ai-assistant-label">AI ASSISTANT</div>

        {messages.length === 0 && (
          <div className="chat-bubble chat-bubble-ai">
            <Sparkles size={16} />
            <p>
              Upload a complaint document or paste text above. I will automatically
              extract the details and populate the form for you.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`chat-bubble ${m.role === "ai" ? "chat-bubble-ai" : "chat-bubble-user"} ${
              m.isError ? "chat-bubble-error" : ""
            }`}
          >
            {m.role === "ai" && <Sparkles size={16} />}
            <p>{m.text}</p>
          </div>
        ))}

        {isThinking && !isUploading && (
          <div className="chat-bubble chat-bubble-ai chat-bubble-thinking">
            <Loader2 size={16} className="spin" />
            <p>Thinking...</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          id="chat-textarea"
          placeholder="Ask me anything about this complaint..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={busy}
        />
        <button className="send-btn" onClick={handleSend} disabled={busy || !inputText.trim()}>
          <Send size={16} />
        </button>
      </div>
      <p className="disclaimer">AI responses may contain errors. Please verify information.</p>
    </div>
  );
}