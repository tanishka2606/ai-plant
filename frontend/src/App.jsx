import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import PlantScanner from "./pages/PlantScanner";
import SeedIdentification from "./pages/SeedIdentification";
import PlantHealth from "./pages/PlantHealth";
import PlantDetails from "./pages/PlantDetails";
import Assistant from "./pages/Assistant";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        <Routes>
          {/* Main Landing Page */}
          <Route path="/" element={<Home />} />

          {/* Plant Scanner Workspace */}
          <Route path="/scanner" element={<PlantScanner />} />

          {/* Dedicated Seed Recognition */}
          <Route path="/seed-identification" element={<SeedIdentification />} />
          <Route path="/seed-identify" element={<SeedIdentification />} />

          {/* Plant Health & Foliar Pathology */}
          <Route path="/health" element={<PlantHealth />} />

          {/* Plant Care Guide (Both direct param & general catalog) */}
          <Route path="/plant-care/:plantName" element={<PlantDetails />} />
          <Route path="/details" element={<PlantDetails />} />

          {/* Conversational AI Assistant */}
          <Route path="/assistant" element={<Assistant />} />

          {/* Plant Intelligence Dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Authentication UI */}
          <Route path="/login" element={<Login />} />

          {/* Professional Botanical 404 Fallback */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
