import { useSelector } from "react-redux";
import { ClipboardCheck, ClipboardList } from "lucide-react";

export default function CompletenessAlert() {
  const { completeness } = useSelector((s) => s.complaint);

  if (!completeness) return null;

  if (completeness.is_complete) {
    return (
      <div className="alert alert-success">
        <ClipboardCheck size={16} />
        <span>All required fields are present — ready to save.</span>
      </div>
    );
  }

  return (
    <div className="alert alert-warning">
      <ClipboardList size={16} />
      <div>
        <span>{completeness.message || "Some required fields are still missing."}</span>
        {completeness.missing_fields?.length > 0 && (
          <div className="missing-fields-list">
            {completeness.missing_fields.map((f) => (
              <span key={f} className="missing-field-tag">
                {f.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}