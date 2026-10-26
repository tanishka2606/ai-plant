import React, { useState, useEffect } from "react";
import { useParams, useLocation, useNavigate, Link } from "react-router-dom";
import { 
  Sun, 
  Droplets, 
  Shovel, 
  Box, 
  Compass, 
  Sparkles, 
  HeartPulse, 
  Search, 
  Database, 
  Bot, 
  ArrowRight,
  BookOpen,
  AlertTriangle
} from "lucide-react";
import { getPlantCare } from "../services/api";
import "./PlantDetails.css";

function PlantDetails() {
  const params = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Determine target plant from URL params (/plant-care/:plantName), navigation state, or default
  const urlPlant = params.plantName ? decodeURIComponent(params.plantName) : "";
  const initialPlant = urlPlant || location.state?.plantName || location.state?.commonName || "";

  const [searchTerm, setSearchTerm] = useState(initialPlant);
  const [currentQuery, setCurrentQuery] = useState(initialPlant || "Hibiscus rosa-sinensis");
  const [careData, setCareData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchCare = async (queryName) => {
    if (!queryName || !queryName.trim()) return;

    setLoading(true);
    setErrorMsg("");
    setCareData(null);

    try {
      const response = await getPlantCare(queryName.trim());
      if (response.success && response.data) {
        setCareData(response.data);
      } else {
        setErrorMsg(
          response.message || `Detailed care information for '${queryName}' is currently unavailable.`
        );
      }
    } catch (err) {
      console.error("Plant care fetch error:", err);
      setErrorMsg("Unable to retrieve plant care information. Please make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (urlPlant) {
      setSearchTerm(urlPlant);
      setCurrentQuery(urlPlant);
    }
  }, [urlPlant]);

  useEffect(() => {
    if (currentQuery) {
      fetchCare(currentQuery);
    }
  }, [currentQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      setCurrentQuery(searchTerm.trim());
      navigate(`/plant-care/${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const handleQuickSelect = (name) => {
    setSearchTerm(name);
    setCurrentQuery(name);
    navigate(`/plant-care/${encodeURIComponent(name)}`);
  };

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <div className="page-badge">
          <Database size={14} />
          <span>Botanical Care Catalog & AI Intelligence</span>
        </div>
        <h1 className="page-title">Plant Care Guide</h1>
        <p className="page-subtitle">
          Structured horticultural profiles for optimal sunlight, watering, soil, container size, location, and fertilization.
        </p>
      </header>

      {/* Search Bar */}
      <form className="care-search-form" onSubmit={handleSearch}>
        <div className="search-input-wrap">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            className="care-search-input"
            placeholder="Search plant by common or scientific name (e.g., Tulip, Lavender, Hibiscus, Rose, Neem)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary btn-care-search">
          Lookup Care Guide
        </button>
      </form>

      {/* Quick Plant Suggestions Pills */}
      <div className="quick-suggestions-bar">
        <span className="suggestions-label">Popular profiles:</span>
        {[
          "Tulip",
          "Lavender",
          "Hibiscus",
          "Rose",
          "Tomato",
          "Aloe Vera",
          "Orchid",
          "Apple",
          "Neem",
          "Mango",
          "Jasmine",
          "Tulsi",
          "Mint",
          "Monstera",
          "Banana",
          "Snake Plant"
        ].map((name) => (
          <button
            key={name}
            type="button"
            className={`suggestion-pill ${currentQuery.toLowerCase().includes(name.toLowerCase()) ? "active" : ""}`}
            onClick={() => handleQuickSelect(name)}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Care Details Main Card */}
      <div className="plant-card care-profile-card">
        {loading && (
          <div className="care-loading-state">
            <span className="spinner spinner-primary" style={{ width: "32px", height: "32px" }}></span>
            <p>Retrieving botanical care guide...</p>
          </div>
        )}

        {errorMsg && !loading && (
          <div className="care-not-found-state">
            <div className="alert-banner alert-warning" style={{ justifyContent: "center" }}>
              <AlertTriangle size={18} />
              <div>{errorMsg}</div>
            </div>
            <div style={{ marginTop: "24px", display: "flex", gap: "12px", justifyContent: "center" }}>
              <button
                className="btn btn-primary"
                onClick={() =>
                  navigate("/assistant", {
                    state: { plantName: searchTerm || currentQuery },
                  })
                }
              >
                <Bot size={16} />
                <span>Ask AI Assistant about {searchTerm || currentQuery}</span>
              </button>
            </div>
          </div>
        )}

        {careData && !loading && (
          <div className="care-profile-content">
            {/* Top Botanical Profile Header */}
            <div className="care-header-box">
              <div className="care-title-group">
                <span className="care-taxonomy-badge">Verified Botanical Care Profile</span>
                <h2 className="care-common-heading">
                  {careData.common_name || careData.plant_name}
                </h2>
                {careData.plant_name && careData.plant_name !== careData.common_name && (
                  <div className="care-scientific-sub">
                    Taxonomic Name: <em>{careData.plant_name}</em>
                  </div>
                )}
              </div>

              <div className="care-meta-tag">
                {careData.source === "MySQL" && careData.id ? (
                  <span className="badge badge-forest">
                    <Database size={13} />
                    <span>MySQL Botanical Record #{careData.id}</span>
                  </span>
                ) : (
                  <span className="badge badge-forest" style={{ background: "rgba(16, 185, 129, 0.15)", borderColor: "rgba(16, 185, 129, 0.3)" }}>
                    <Sparkles size={13} style={{ color: "#34d399" }} />
                    <span>{careData.source || "AI Botanical Intelligence Guide"}</span>
                  </span>
                )}
              </div>
            </div>

            {/* Structured Care Parameter Cards Grid */}
            <div className="care-cards-grid">
              {/* Sunlight */}
              <div className="care-metric-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap sun-icon">
                    <Sun size={20} />
                  </div>
                  <h4>Sunlight</h4>
                </div>
                <div className="care-metric-body">
                  {careData.sunlight || "Bright natural sunlight required for optimal growth."}
                </div>
              </div>

              {/* Water */}
              <div className="care-metric-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap water-icon">
                    <Droplets size={20} />
                  </div>
                  <h4>Watering</h4>
                </div>
                <div className="care-metric-body">
                  {careData.water || "Water thoroughly when topsoil is dry; avoid standing water."}
                </div>
              </div>

              {/* Soil */}
              <div className="care-metric-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap soil-icon">
                    <Shovel size={20} />
                  </div>
                  <h4>Soil & Drainage</h4>
                </div>
                <div className="care-metric-body">
                  {careData.soil || "Rich, well-draining loamy potting soil with organic compost."}
                </div>
              </div>

              {/* Container */}
              <div className="care-metric-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap container-icon">
                    <Box size={20} />
                  </div>
                  <h4>Container & Pot</h4>
                </div>
                <div className="care-metric-body">
                  {careData.container || "Select a pot with ample drainage holes proportional to root ball."}
                </div>
              </div>

              {/* Location */}
              <div className="care-metric-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap location-icon">
                    <Compass size={20} />
                  </div>
                  <h4>Ideal Location</h4>
                </div>
                <div className="care-metric-body">
                  {careData.location || "Well-ventilated position with bright ambient indirect light."}
                </div>
              </div>

              {/* Fertilizer (Section 13, 32 requirement) */}
              <div className="care-metric-card fertilizer-card">
                <div className="care-metric-header">
                  <div className="metric-icon-wrap fertilizer-icon">
                    <Sparkles size={20} />
                  </div>
                  <h4>Fertilizer & Nutrition</h4>
                </div>
                <div className="care-metric-body">
                  {careData.fertilizer || "Apply balanced organic fertilizer during active growing season."}
                </div>
              </div>
            </div>

            {/* General Care Maintenance */}
            {careData.care && (
              <div className="care-summary-box">
                <div className="summary-title-row">
                  <HeartPulse size={18} className="summary-heart-icon" />
                  <h3>General Care & Maintenance</h3>
                </div>
                <p className="summary-text">{careData.care}</p>
              </div>
            )}

            {/* Common Problems & Prevention */}
            {careData.common_problems_and_prevention && (
              <div className="care-summary-box" style={{ marginTop: "16px", borderLeft: "4px solid #f59e0b", background: "rgba(254, 243, 199, 0.4)" }}>
                <div className="summary-title-row">
                  <AlertTriangle size={18} style={{ color: "#d97706" }} />
                  <h3 style={{ color: "#92400e" }}>Common Problems & Prevention</h3>
                </div>
                <p className="summary-text" style={{ color: "#78350f" }}>{careData.common_problems_and_prevention}</p>
              </div>
            )}

            {/* Assistant Jump Button */}
            <div className="care-footer-actions">
              <button
                className="btn btn-primary btn-care-assistant"
                onClick={() =>
                  navigate("/assistant", {
                    state: { plantName: careData.common_name || careData.plant_name },
                  })
                }
              >
                <Bot size={18} />
                <span>Ask AI Assistant Questions About {careData.common_name || careData.plant_name}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PlantDetails;
