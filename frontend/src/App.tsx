import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import VideoAnalysis from "./pages/VideoAnalysis";
import EvidenceCenter from "./pages/EvidenceCenter";
import ReviewHistory from "./pages/ReviewHistory";
import Analytics from "./pages/Analytics";
import SmartCityMap from "./pages/SmartCityMap";
import Reports from "./pages/Reports";
import Roadmap from "./pages/Roadmap";
import About from "./pages/About";
import Login from "./pages/Login";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/analyze" element={<ProtectedRoute><Analyze /></ProtectedRoute>} />
          <Route path="/video-analysis" element={<ProtectedRoute><VideoAnalysis /></ProtectedRoute>} />
          <Route path="/evidence" element={<ProtectedRoute><EvidenceCenter /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><ReviewHistory /></ProtectedRoute>} />
          <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
          <Route path="/map" element={<ProtectedRoute><SmartCityMap /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
          <Route path="/roadmap" element={<ProtectedRoute><Roadmap /></ProtectedRoute>} />
          <Route path="/about" element={<ProtectedRoute><About /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
