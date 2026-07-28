import { useState } from "react";
import { FilePlus, List } from "lucide-react";
import ComplaintForm from "./components/ComplaintForm";
import ChatPanel from "./components/ChatPanel";
import RiskPanel from "./components/RiskPanel";
import CompletenessAlert from "./components/CompletenessAlert";
import DuplicateAlert from "./components/DuplicateAlert";
import ComplaintList from "./components/ComplaintList";

export default function App() {
  const [activeTab, setActiveTab] = useState("intake"); // "intake" | "list"

  return (
    <div className="app-root">
      <nav className="top-nav">
        <button
          className={`nav-tab ${activeTab === "intake" ? "nav-tab-active" : ""}`}
          onClick={() => setActiveTab("intake")}
        >
          <FilePlus size={15} />
          Log Complaint
        </button>
        <button
          className={`nav-tab ${activeTab === "list" ? "nav-tab-active" : ""}`}
          onClick={() => setActiveTab("list")}
        >
          <List size={15} />
          Saved Complaints
        </button>
      </nav>

      {activeTab === "intake" ? (
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
      ) : (
        <div className="app-shell app-shell-single">
          <ComplaintList onOpenComplaint={() => setActiveTab("intake")} />
        </div>
      )}
    </div>
  );
}