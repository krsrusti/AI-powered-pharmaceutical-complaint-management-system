import { useSelector } from "react-redux";

const RISK_COLORS = {
  low: "#2e7d32",
  medium: "#f9a825",
  high: "#ef6c00",
  critical: "#c62828",
};

export default function RiskPanel() {
  const { riskLevel, riskRationale, flaggedTerms } = useSelector((state) => state.complaint);

  if (!riskLevel) {
    return (
      <div className="panel">
        <h3>Risk Assessment</h3>
        <p>Risk will be assessed once the complaint is complete.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h3>Risk Assessment</h3>
      <span
        className="risk-badge"
        style={{ backgroundColor: RISK_COLORS[riskLevel] || "#999", color: "#fff" }}
      >
        {riskLevel.toUpperCase()}
      </span>
      {riskRationale && <p>{riskRationale}</p>}
      {flaggedTerms?.length > 0 && (
        <div>
          <strong>Flagged terms:</strong>
          <ul>
            {flaggedTerms.map((term, i) => (
              <li key={i}>{term}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
