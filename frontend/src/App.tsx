import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analyze from "./pages/Analyze";
import EvidenceCenter from "./pages/EvidenceCenter";
import Analytics from "./pages/Analytics";
import SmartCityMap from "./pages/SmartCityMap";
import Reports from "./pages/Reports";
import Roadmap from "./pages/Roadmap";
import About from "./pages/About";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/evidence" element={<EvidenceCenter />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/map" element={<SmartCityMap />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </BrowserRouter>
  );
}
