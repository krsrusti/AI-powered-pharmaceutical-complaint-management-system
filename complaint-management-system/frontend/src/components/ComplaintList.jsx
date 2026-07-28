import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { RefreshCw, FileSearch, AlertCircle } from "lucide-react";
import { fetchAllComplaints } from "../api";
import { loadComplaint } from "../store/complaintSlice";
import { clearChat } from "../store/chatSlice";

const STATUS_LABELS = {
  draft: "Pending Triage",
  submitted: "Submitted",
  under_investigation: "Under Investigation",
  closed: "Closed",
};

const STATUS_COLORS = {
  draft: { bg: "#FEF3C7", text: "#92400E" },
  submitted: { bg: "#DBEAFE", text: "#1E40AF" },
  under_investigation: { bg: "#FEE2E2", text: "#991B1B" },
  closed: { bg: "#DCFCE7", text: "#166534" },
};

const RISK_COLORS = {
  high: "#DC2626",
  medium: "#D97706",
  low: "#16A34A",
  unassessed: "#9CA3AF",
};

export default function ComplaintList({ onOpenComplaint }) {
  const dispatch = useDispatch();
  const [complaints, setComplaints] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadList = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAllComplaints();
      setComplaints(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  const handleOpen = (complaintId) => {
    dispatch(clearChat());
    dispatch(loadComplaint(complaintId));
    if (onOpenComplaint) onOpenComplaint();
  };

  return (
    <div className="complaint-list">
      <div className="complaint-list-header">
        <h2>Saved Complaints</h2>
        <button className="btn-secondary" onClick={loadList} disabled={isLoading}>
          <RefreshCw size={14} className={isLoading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="alert alert-warning">
          <AlertCircle size={16} />
          <span>Failed to load complaints: {error}</span>
        </div>
      )}

      {!error && !isLoading && complaints.length === 0 && (
        <div className="complaint-list-empty">
          <FileSearch size={24} color="#9CA3AF" />
          <p>No complaints saved yet — start a conversation in the AI Copilot to log one.</p>
        </div>
      )}

      <div className="complaint-list-table">
        {complaints.map((c) => {
          const statusKey = c.status || "draft";
          const statusColor = STATUS_COLORS[statusKey] || STATUS_COLORS.draft;
          const riskLevel = c.risk_assessment?.risk_level || "unassessed";

          return (
            <button
              key={c.complaint_id}
              className="complaint-list-row"
              onClick={() => handleOpen(c.complaint_id)}
            >
              <div className="complaint-row-main">
                <span className="complaint-row-id">{c.complaint_id}</span>
                <span className="complaint-row-product">
                  {c.product_name || "Product not yet extracted"}
                  {c.batch_number ? ` · Batch ${c.batch_number}` : ""}
                </span>
              </div>
              <div className="complaint-row-meta">
                <span
                  className="risk-dot"
                  style={{ background: RISK_COLORS[riskLevel] }}
                  title={`Risk: ${riskLevel}`}
                />
                <span
                  className="status-badge status-badge-sm"
                  style={{ background: statusColor.bg, color: statusColor.text }}
                >
                  {STATUS_LABELS[statusKey] || statusKey}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}