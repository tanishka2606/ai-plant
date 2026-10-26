import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  UploadCloud, 
  Scan, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  BookOpen, 
  Bot, 
  Sparkles, 
  Dna, 
  Layers, 
  RotateCcw,
  ArrowRight,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { uploadPlant } from "../services/api";
import "./PlantScanner.css";

function PlantScanner() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedCandidateIndex, setSelectedCandidateIndex] = useState(null);

  // Clear previous state when a new file is picked
  const handleFile = (file) => {
    if (!file) return;

    // Validate type
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setErrorMsg("Unsupported file format. Please upload JPG, PNG, or WEBP.");
      return;
    }

    // Validate size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("File size exceeds 10MB limit. Please choose a smaller image.");
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setErrorMsg("");
    setSelectedCandidateIndex(null);
  };

  const handleInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleRemoveImage = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setErrorMsg("");
    setSelectedCandidateIndex(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setAnalyzing(true);
    setResult(null);
    setErrorMsg("");
    setSelectedCandidateIndex(null);

    try {
      const response = await uploadPlant(selectedFile);
      setResult(response);
      if (!response.success && response.status === "error") {
        setErrorMsg(response.message || "Failed to identify plant.");
      }
    } catch (err) {
      console.error("Plant identification error:", err);
      setErrorMsg("Unable to connect to PlantAI. Please ensure the backend server is running.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCandidateClick = (idx) => {
    setSelectedCandidateIndex((prev) => (prev === idx ? null : idx));
  };

  const plantData = result?.data;
  const isIdentified = result?.success && result?.status === "identified";
  const isLowConfidence = result?.status === "low_confidence";

  // Visible characteristics for "Why This Plant?"
  const whyThisPlantFeatures = 
    (plantData?.identifying_features && plantData.identifying_features.length > 0)
      ? plantData.identifying_features
      : (plantData?.characteristics && plantData.characteristics.length > 0)
        ? plantData.characteristics
        : [];

  // Alternative candidates (excluding the primary top result)
  const alternativeCandidates = 
    plantData?.candidates && plantData.candidates.length > 1
      ? plantData.candidates.slice(1, 5)
      : [];

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <div className="page-badge">
          <Scan size={14} />
          <span>Precision Botanical Vision</span>
        </div>
        <h1 className="page-title">AI Plant Scanner</h1>
        <p className="page-subtitle">
          Upload a clear photograph of a leaf, flower, or whole plant to identify its species and access plant care guidelines.
        </p>
      </header>

      {/* Main 2-Column Workspace */}
      <div className="scanner-workspace-grid">
        {/* Left Column: Upload Area */}
        <div className="scanner-left-panel">
          <div className="plant-card upload-card">
            <h3 className="panel-title">Specimen Upload</h3>
            <p className="panel-subtitle">Select or drop a botanical image for optical inspection</p>

            {!previewUrl ? (
              <div
                className={`dropzone ${isDragOver ? "active" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById("plant-file-input").click()}
              >
                <div className="dropzone-icon-wrap">
                  <UploadCloud size={28} />
                </div>
                <div className="dropzone-text">Click to upload or drag & drop</div>
                <div className="dropzone-hint">Supports JPG, JPEG, PNG, WEBP (Max 10MB)</div>
                <input
                  id="plant-file-input"
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={handleInputChange}
                  hidden
                />
              </div>
            ) : (
              <div className="uploaded-preview-wrapper">
                <div className="preview-container">
                  <img src={previewUrl} alt="Specimen Preview" className="preview-image" />
                  
                  {/* Laser scan animation when analyzing */}
                  {analyzing && (
                    <>
                      <div className="scan-beam"></div>
                      <div className="scan-overlay-grid"></div>
                    </>
                  )}

                  <button
                    className="btn-remove-preview"
                    onClick={handleRemoveImage}
                    title="Remove image"
                    disabled={analyzing}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="preview-actions">
                  <button
                    className="btn btn-primary btn-analyze"
                    onClick={handleAnalyze}
                    disabled={analyzing}
                  >
                    {analyzing ? (
                      <>
                        <span className="spinner"></span>
                        <span>Analyzing botanical features...</span>
                      </>
                    ) : (
                      <>
                        <Scan size={18} />
                        <span>Analyze Plant</span>
                      </>
                    )}
                  </button>

                  <button
                    className="btn btn-outline btn-reset"
                    onClick={handleRemoveImage}
                    disabled={analyzing}
                  >
                    <RotateCcw size={16} />
                    <span>Choose Another</span>
                  </button>
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMsg && (
              <div className="alert-banner alert-error">
                <AlertTriangle size={18} />
                <div>{errorMsg}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Analysis Result Panel */}
        <div className="scanner-right-panel">
          <div className="plant-card result-panel-card">
            <div className="result-panel-header">
              <h3 className="panel-title">Plant Identification</h3>
              {isIdentified && (
                <span className="badge badge-success">
                  <CheckCircle2 size={12} />
                  <span>Plant Identified</span>
                </span>
              )}
            </div>

            {/* State 1: Empty / Waiting State */}
            {!result && !analyzing && (
              <div className="empty-analysis-state">
                <div className="empty-state-icon">
                  <Scan size={36} />
                </div>
                <h4>Ready for Specimen</h4>
                <p>Upload a clear photo on the left and click "Analyze Plant" to initiate botanical classification.</p>
                <div className="guidelines-card">
                  <strong>For optimal identification:</strong>
                  <ul>
                    <li>Photograph in natural daylight without strong glare</li>
                    <li>Ensure leaves, flowers, or fruit are in sharp focus</li>
                    <li>Avoid extreme distance or crowded multi-species backgrounds</li>
                  </ul>
                </div>
              </div>
            )}

            {/* State 2: Loading Analysis State */}
            {analyzing && (
              <div className="loading-analysis-state">
                <div className="loading-radar-ring">
                  <div className="radar-pulse"></div>
                  <Scan size={32} className="radar-icon" />
                </div>
                <h4>Examining Specimen Features</h4>
                <p>Analyzing botanical features against reference observations...</p>
                <div className="loading-step-list">
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Image quality and lighting validation</span>
                  </div>
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Morphological feature extraction</span>
                  </div>
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Botanical species matching</span>
                  </div>
                </div>
              </div>
            )}

            {/* State 3: Low Confidence State */}
            {isLowConfidence && (
              <div className="low-confidence-result-state">
                <div className="alert-banner alert-warning">
                  <AlertTriangle size={18} />
                  <div>
                    <strong>Low Confidence Identification</strong>
                    <p style={{ marginTop: "4px" }}>
                      Try uploading a clearer photo showing the leaves, flower, stem, or whole plant.
                    </p>
                    {plantData?.confidence_percent !== undefined && (
                      <div className="threshold-meta">
                        Confidence: <strong>{plantData.confidence_percent}%</strong> (Below identification threshold).
                      </div>
                    )}
                  </div>
                </div>

                {plantData?.candidates && plantData.candidates.length > 0 && (
                  <div className="candidate-list">
                    <h5 className="candidates-heading">Potential Candidate Matches:</h5>
                    {plantData.candidates.slice(0, 3).map((cand, idx) => (
                      <div key={idx} className="candidate-item">
                        <div className="candidate-names">
                          <strong>{cand.common_name || cand.scientific_name}</strong>
                          <em>({cand.scientific_name})</em>
                        </div>
                        <span className="confidence-badge confidence-medium">
                          Confidence: {cand.confidence_percent}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* State 4: Identified Result */}
            {isIdentified && plantData && (
              <div className="identified-result-state">
                {/* Primary Identification Box: Plant name & single confidence score */}
                <div className="primary-identification-box">
                  <div className="ident-top-row">
                    <div className="ident-title-col">
                      <span className="species-tag">Plant Identified</span>
                      <h2 className="plant-common-name">
                        {plantData.common_name || plantData.plant_name}
                      </h2>
                      <div className="plant-scientific-name">
                        <em>{plantData.scientific_name}</em>
                      </div>
                    </div>
                    <div className="confidence-pill-container">
                      <span className="confidence-pill">
                        Confidence: {plantData.confidence_percent}%
                      </span>
                    </div>
                  </div>

                  {/* Clean Visual Confidence Bar (without duplicate label) */}
                  <div className="confidence-bar-wrap">
                    <div 
                      className={`confidence-bar-fill ${plantData.confidence >= 0.70 ? "high" : "medium"}`}
                      style={{ width: `${Math.min(100, Math.max(15, plantData.confidence_percent))}%` }}
                    ></div>
                  </div>
                </div>

                {/* Botanical Metadata Cards */}
                <div className="botanical-meta-grid">
                  <div className="meta-card">
                    <div className="meta-card-label">
                      <Dna size={14} />
                      <span>Species</span>
                    </div>
                    <div className="meta-card-val" title={plantData.species || plantData.scientific_name}>
                      <em>{plantData.species || plantData.scientific_name}</em>
                    </div>
                  </div>

                  <div className="meta-card">
                    <div className="meta-card-label">
                      <Layers size={14} />
                      <span>Genus</span>
                    </div>
                    <div className="meta-card-val" title={plantData.genus || "Not available"}>
                      {plantData.genus || "Not available"}
                    </div>
                  </div>

                  {plantData.family && (
                    <div className="meta-card">
                      <div className="meta-card-label">
                        <Sparkles size={14} />
                        <span>Family</span>
                      </div>
                      <div className="meta-card-val" title={plantData.family}>
                        {plantData.family}
                      </div>
                    </div>
                  )}
                </div>

                {/* Section 2: Why This Plant? */}
                {whyThisPlantFeatures.length > 0 && (
                  <div className="why-this-plant-card">
                    <div className="why-this-plant-header">
                      <Sparkles size={16} className="why-icon" />
                      <h4 className="why-this-plant-title">Why This Plant?</h4>
                    </div>
                    <p className="why-this-plant-subtitle">
                      Visible characteristics that support this identification:
                    </p>
                    <ul className="why-this-plant-list">
                      {whyThisPlantFeatures.map((trait, tIdx) => (
                        <li key={tIdx}>{trait}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Section 3: Alternative Candidates (Visually organized & interactive) */}
                {alternativeCandidates.length > 0 && (
                  <div className="alternative-candidates-section">
                    <div className="candidates-section-header">
                      <h4 className="candidates-heading">Alternative Candidates</h4>
                      <p className="candidates-subtext">
                        Other possible matches based on image analysis. Click any candidate to view its botanical details.
                      </p>
                    </div>

                    <div className="candidates-list-interactive">
                      {alternativeCandidates.map((cand, idx) => {
                        const isSelected = selectedCandidateIndex === idx;
                        return (
                          <div
                            key={idx}
                            className={`candidate-card ${isSelected ? "selected" : ""}`}
                          >
                            <div
                              className="candidate-card-summary"
                              onClick={() => handleCandidateClick(idx)}
                              role="button"
                              tabIndex={0}
                            >
                              <div className="candidate-names-wrap">
                                <div className="candidate-primary-name">
                                  {cand.common_name || cand.scientific_name}
                                </div>
                                <div className="candidate-scientific-name">
                                  <em>{cand.scientific_name}</em>
                                </div>
                              </div>
                              <div className="candidate-meta-right">
                                <span className="candidate-confidence-pill">
                                  Confidence: {cand.confidence_percent}%
                                </span>
                                <span className="candidate-toggle-link">
                                  {isSelected ? (
                                    <>
                                      <span>Hide details</span>
                                      <ChevronUp size={14} />
                                    </>
                                  ) : (
                                    <>
                                      <span>View details</span>
                                      <ChevronDown size={14} />
                                    </>
                                  )}
                                </span>
                              </div>
                            </div>

                            {/* Expanded botanical details when selected */}
                            {isSelected && (
                              <div className="candidate-expanded-content">
                                <div className="candidate-botanical-info">
                                  <span className="candidate-info-title">Basic Botanical Information</span>
                                  <div className="candidate-info-grid">
                                    <div className="candidate-info-cell">
                                      <span className="info-cell-label">Species</span>
                                      <span className="info-cell-val"><em>{cand.scientific_name}</em></span>
                                    </div>
                                    {cand.genus && (
                                      <div className="candidate-info-cell">
                                        <span className="info-cell-label">Genus</span>
                                        <span className="info-cell-val">{cand.genus}</span>
                                      </div>
                                    )}
                                    {cand.family && (
                                      <div className="candidate-info-cell">
                                        <span className="info-cell-label">Family</span>
                                        <span className="info-cell-val">{cand.family}</span>
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {cand.characteristics && cand.characteristics.length > 0 ? (
                                  <div className="candidate-traits-box">
                                    <span className="candidate-traits-title">Identifying Characteristics:</span>
                                    <ul className="candidate-traits-list">
                                      {cand.characteristics.map((charItem, cIdx) => (
                                        <li key={cIdx}>{charItem}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ) : (
                                  <div className="candidate-traits-empty">
                                    <em>Detailed morphological characteristics not cataloged for this alternative candidate.</em>
                                  </div>
                                )}

                                <div className="candidate-action-bar">
                                  <button
                                    type="button"
                                    className="btn btn-outline btn-candidate-care"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      navigate(`/plant-care/${encodeURIComponent(cand.scientific_name)}`, {
                                        state: {
                                          plantName: cand.scientific_name,
                                          commonName: cand.common_name,
                                        },
                                      });
                                    }}
                                  >
                                    <BookOpen size={14} />
                                    <span>View Care Guide for {cand.common_name || cand.scientific_name}</span>
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Primary Action Buttons */}
                <div className="identification-action-row">
                  <button
                    className="btn btn-primary btn-action-care"
                    onClick={() =>
                      navigate(`/plant-care/${encodeURIComponent(plantData.scientific_name)}`, {
                        state: {
                          plantName: plantData.scientific_name,
                          commonName: plantData.common_name,
                        },
                      })
                    }
                  >
                    <BookOpen size={16} />
                    <span>View Care Guide</span>
                  </button>

                  <button
                    className="btn btn-outline btn-action-assistant"
                    onClick={() =>
                      navigate("/assistant", {
                        state: {
                          plantName: plantData.common_name || plantData.scientific_name,
                        },
                      })
                    }
                  >
                    <Bot size={16} />
                    <span>Ask AI Assistant</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PlantScanner;
