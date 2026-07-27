import { useSelector, useDispatch } from "react-redux";
import { RotateCcw, Save } from "lucide-react";
import { resetComplaint, submitComplaintThunk } from "../store/complaintSlice";
import { clearChat } from "../store/chatSlice";

// Mirrors backend STATUS_DISPLAY_LABELS (schemas.py) — kept as a small,
// intentional duplication rather than a shared package, since this is the
// only place the frontend needs it.
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

function Field({ label, value, unit, isTextarea }) {
  const displayValue = value || "";
  const placeholder = "Awaiting AI extraction...";

  return (
    <div className="field">
      <label>{label}</label>
      <div className="field-input-wrap">
        {isTextarea ? (
          <textarea readOnly value={displayValue} placeholder={placeholder} rows={3} />
        ) : (
          <input readOnly type="text" value={displayValue} placeholder={placeholder} />
        )}
        {unit && <span className="field-unit">{unit}</span>}
      </div>
    </div>
  );
}

export default function ComplaintForm() {
  const dispatch = useDispatch();
  const { complaint, complaintId, status } = useSelector((s) => s.complaint);

  const statusKey = complaint?.status || "draft";
  const statusLabel = STATUS_LABELS[statusKey] || statusKey;
  const statusColor = STATUS_COLORS[statusKey] || STATUS_COLORS.draft;

  const handleReset = () => {
    dispatch(resetComplaint());
    dispatch(clearChat());
  };

  const handleSave = () => {
    if (complaintId) {
      dispatch(submitComplaintThunk(complaintId));
    }
  };

  const c = complaint || {};
  const customer = c.customer_details || {};
  const mfg = c.manufacturing_info || {};
  const risk = c.risk_assessment || {};

  return (
    <div className="complaint-form">
      <div className="form-header">
        <div>
          <h1>Log Customer Complaint</h1>
          <p className="subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span
          className="status-badge"
          style={{ background: statusColor.bg, color: statusColor.text }}
        >
          {statusLabel}
        </span>
      </div>

      <section>
        <h2>1. Origin &amp; Customer Details</h2>
        <div className="field-grid">
          <Field label="Complaint Source" value={c.complaint_source} />
          <Field label="Customer Name" value={customer.name} />
          <Field label="Customer Organization" value={customer.organization} />
          <Field label="Customer Contact" value={customer.contact_info} />
        </div>
      </section>

      <section>
        <h2>2. Product &amp; Batch Identification</h2>
        <div className="field-grid">
          <Field label="Product Name" value={c.product_name} />
          <Field label="Product Strength/Grade" value={c.product_strength_grade} />
          <Field label="Batch/Lot Number" value={c.batch_number} />
          <Field label="Manufacturing Date" value={mfg.manufacturing_date} />
          <Field label="Expiry Date" value={mfg.expiry_date} />
          <Field label="Quantity Affected" value={c.affected_quantity} unit={c.affected_quantity_unit} />
        </div>
      </section>

      <section>
        <h2>3. Complaint Details</h2>
        <div className="field-grid">
          <Field label="Complaint Type" value={c.complaint_type} />
          <Field label="Complaint Date" value={c.complaint_date} />
        </div>
        <Field label="Detailed Complaint Description" value={c.complaint_description} isTextarea />
      </section>

      <section>
        <h2>4. Initial Assessment &amp; Priority</h2>
        <p className="ai-note">AI-determined — updates automatically as the complaint changes</p>
        <div className="field-grid">
          <Field label="Initial Severity" value={risk.risk_level} />
          <Field label="Priority" value={risk.investigation_priority} />
        </div>
      </section>

      <div className="form-actions">
        <button className="btn-secondary" onClick={handleReset}>
          <RotateCcw size={16} />
          Reset Form
        </button>
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={!complaintId || status === "loading"}
        >
          <Save size={16} />
          Save Complaint
        </button>
      </div>
    </div>
  );
}