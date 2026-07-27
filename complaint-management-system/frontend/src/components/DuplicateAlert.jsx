import { useSelector } from "react-redux";

export default function DuplicateAlert() {
  const { isDuplicate, duplicates } = useSelector((state) => state.complaint);

  if (!isDuplicate || !duplicates?.length) return null;

  return (
    <div className="panel alert alert--info">
      <strong>Possible duplicate complaints found:</strong>
      <ul>
        {duplicates.map((match) => (
          <li key={match.complaint_id}>
            Complaint #{match.complaint_id} — {Math.round(match.similarity_score * 100)}% similar
            {match.matched_on?.length > 0 && ` (matched on: ${match.matched_on.join(", ")})`}
          </li>
        ))}
      </ul>
    </div>
  );
}
