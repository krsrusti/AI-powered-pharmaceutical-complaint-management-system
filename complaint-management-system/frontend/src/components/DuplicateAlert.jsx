import { useSelector } from "react-redux";
import { Copy } from "lucide-react";

export default function DuplicateAlert() {
  const { duplicates } = useSelector((s) => s.complaint);

  if (!duplicates || !duplicates.has_duplicates) return null;

  return (
    <div className="alert alert-info">
      <Copy size={16} />
      <div>
        <span>
          Possible duplicate{duplicates.matches.length > 1 ? "s" : ""} detected —
          review before saving:
        </span>
        <div className="duplicate-matches-list">
          {duplicates.matches.map((m) => (
            <div key={m.complaint_id} className="duplicate-match-row">
              <span className="duplicate-id">{m.complaint_id}</span>
              <span className="duplicate-score">{Math.round(m.similarity_score * 100)}% match</span>
              <span className="duplicate-matched-on">{m.matched_on.join(", ").replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}