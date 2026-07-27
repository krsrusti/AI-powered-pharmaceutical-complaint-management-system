import { Provider } from "react-redux";
import store from "./store/store";
import ChatPanel from "./components/ChatPanel";
import ComplaintForm from "./components/ComplaintForm";
import RiskPanel from "./components/RiskPanel";
import CompletenessAlert from "./components/CompletenessAlert";
import DuplicateAlert from "./components/DuplicateAlert";

function AppContent() {
  return (
    <div className="app-layout">
      <div className="app-column">
        <ChatPanel />
      </div>
      <div className="app-column">
        <CompletenessAlert />
        <DuplicateAlert />
        <ComplaintForm />
        <RiskPanel />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <AppContent />
    </Provider>
  );
}
