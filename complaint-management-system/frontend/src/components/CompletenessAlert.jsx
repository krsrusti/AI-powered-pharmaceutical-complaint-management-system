import { useSelector } from "react-redux";

export default function CompletenessAlert() {
  const { isComplete, completenessScore, missingFields } = useSelector(
    (state) => state.complaint
  );

  if (completenessScore === null) return null;

  if (isComplete) {
    return (
      <div className="panel alert alert--success">
        <strong>Complete.</strong> All required information has been provided.
      </div>
    );
  }

  return (
    <div className="panel alert alert--warning">
      <strong>Missing information</strong> ({Math.round((completenessScore || 0) * 100)}% complete)
      {missingFields?.length > 0 && (
        <ul>
          {missingFields.map((field, i) => (
            <li key={i}>{field}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
