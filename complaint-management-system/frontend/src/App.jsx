import ComplaintForm from "./components/ComplaintForm";
import ChatPanel from "./components/ChatPanel";
import RiskPanel from "./components/RiskPanel";
import CompletenessAlert from "./components/CompletenessAlert";
import DuplicateAlert from "./components/DuplicateAlert";

export default function App() {
  return (
    <div className="app-shell">
      <div className="panel panel-left">
        <CompletenessAlert />
        <DuplicateAlert />
        <ComplaintForm />
        <RiskPanel />
      </div>
      <div className="panel panel-right">
        <ChatPanel />
      </div>
    </div>
  );
}