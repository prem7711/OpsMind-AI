import { BrowserRouter, Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { UploadPage } from "./pages/UploadPage";
import { InvestigationPage } from "./pages/InvestigationPage";
import { HistoryPage } from "./pages/HistoryPage";
import { DashboardPage } from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0c10]">
        <div
          className="pointer-events-none fixed inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(60rem 30rem at 20% -10%, rgba(99,102,241,0.15), transparent), radial-gradient(50rem 25rem at 100% 0%, rgba(139,92,246,0.12), transparent)",
          }}
        />
        <div className="relative">
          <NavBar />
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/incident/:incidentId" element={<InvestigationPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
