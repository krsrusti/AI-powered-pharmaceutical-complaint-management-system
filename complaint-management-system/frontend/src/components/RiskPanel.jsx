import { useSelector } from "react-redux";
import { AlertTriangle, ShieldCheck, ShieldAlert, Shield, RefreshCw } from "lucide-react";

const RISK_CONFIG = {
  high: { color: "#DC2626", bg: "#FEF2F2", border: "#FECACA", icon: ShieldAlert, label: "High Risk" },
  medium: { color: "#D97706", bg: "#FFFBEB", border: "#FDE68A", icon: AlertTriangle, label: "Medium Risk" },
  low: { color: "#16A34A", bg: "#F0FDF4", border: "#BBF7D0", icon: ShieldCheck, label: "Low Risk" },
  unassessed: { color: "#6B7280", bg: "#F9FAFB", border: "#E5E7EB", icon: Shield, label: "Not Yet Assessed" },
};

function ReasoningRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="reasoning-row">
      <span className="reasoning-label">{label}</span>
      <p className="reasoning-value">{value}</p>
    </div>
  );
}

export default function RiskPanel() {
  const { complaint, riskChanged } = useSelector((s) => s.complaint);
  const risk = complaint?.risk_assessment;
  const level = risk?.risk_level || "unassessed";
  const config = RISK_CONFIG[level] || RISK_CONFIG.unassessed;
  const Icon = config.icon;

  if (!complaint) {
    return (
      <div className="risk-panel risk-panel-empty">
        <Shield size={20} color="#9CA3AF" />
        <p>Risk assessment will appear here once a complaint is logged.</p>
      </div>
    );
  }

  return (
    <div className="risk-panel" style={{ background: config.bg, borderColor: config.border }}>
      <div className="risk-panel-header">
        <div className="risk-level-badge" style={{ color: config.color }}>
          <Icon size={20} />
          <span>{config.label}</span>
        </div>
        {level !== "unassessed" && (
          <span className={`risk-change-indicator ${riskChanged ? "changed" : "unchanged"}`}>
            {riskChanged ? (
              <>
                <RefreshCw size={12} /> Updated this turn
              </>
            ) : (
              "Unchanged"
            )}
          </span>
        )}
      </div>

      {risk?.reasoning_summary && <p className="risk-summary">{risk.reasoning_summary}</p>}

      <ReasoningRow label="Possible Product Impact" value={risk?.product_impact} />
      <ReasoningRow label="Possible Patient Impact" value={risk?.patient_impact} />
      <ReasoningRow label="Investigation Priority" value={risk?.investigation_priority} />

      {risk?.rubric_criteria_matched && risk.rubric_criteria_matched.length > 0 && (
        <div className="rubric-tags">
          {risk.rubric_criteria_matched.map((criterion, i) => (
            <span key={i} className="rubric-tag">
              {criterion}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}