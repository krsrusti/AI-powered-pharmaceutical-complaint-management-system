import { useDispatch, useSelector } from "react-redux";
import { updateComplaint as updateComplaintApi } from "../api";
import { updateComplaintFields } from "../store/complaintSlice";

const FIELDS = [
  { key: "title", label: "Title" },
  { key: "description", label: "Description", multiline: true },
  { key: "category", label: "Category" },
  { key: "complainant_name", label: "Your Name" },
  { key: "complainant_contact", label: "Contact Info" },
];

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const complaint = useSelector((state) => state.complaint.current) || {};

  const handleChange = (key, value) => {
    dispatch(updateComplaintFields({ [key]: value }));
  };

  const handleSave = async () => {
    if (!complaint.id) return;
    const { data } = await updateComplaintApi(complaint.id, complaint);
    dispatch(updateComplaintFields(data));
  };

  return (
    <div className="panel">
      <h2>Complaint Details</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSave();
        }}
      >
        {FIELDS.map(({ key, label, multiline }) => (
          <div key={key} className="form-field">
            <label htmlFor={key}>{label}</label>
            {multiline ? (
              <textarea
                id={key}
                rows={4}
                value={complaint[key] || ""}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            ) : (
              <input
                id={key}
                type="text"
                value={complaint[key] || ""}
                onChange={(e) => handleChange(key, e.target.value)}
              />
            )}
          </div>
        ))}
        <button type="submit" disabled={!complaint.id}>
          Save Changes
        </button>
      </form>
    </div>
  );
}
