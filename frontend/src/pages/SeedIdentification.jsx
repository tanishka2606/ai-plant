import React, { useState } from "react";
import { 
  Sprout, 
  UploadCloud, 
  X, 
  AlertTriangle, 
  RotateCcw, 
  Sparkles,
  ArrowRight,
  Heart,
  Globe,
  CheckCircle2,
  Apple
} from "lucide-react";

const F_UNIT = "[°\\u00b0]?\\s*(?:Fahrenheit|F)\\b";
const F_STR = `(?:(?:\\d+(?:\\.\\d+)?\\s*${F_UNIT}\\s*(?:to|-|–)\\s*\\d+(?:\\.\\d+)?\\s*${F_UNIT})|(?:\\d+(?:\\.\\d+)?\\s*(?:to|-|–)\\s*\\d+(?:\\.\\d+)?\\s*${F_UNIT})|(?:\\d+(?:\\.\\d+)?\\s*${F_UNIT}))`;

const sanitizeCelsius = (text) => {
  if (!text || typeof text !== "string") return text;
  let cleaned = text;

  // 1. '68°F to 77°F (20°C to 25°C)' -> '20°C to 25°C'
  cleaned = cleaned.replace(
    new RegExp(F_STR + "\\s*\\(([^)]*[°\\u00b0]\\s*C[^)]*)\\)", "gi"),
    "$1"
  );

  // 2. If Celsius is already present in the text, safely strip companion Fahrenheit expressions
  if (/[°\u00b0]\s*C|Celsius/i.test(cleaned)) {
    cleaned = cleaned.replace(new RegExp("\\s*[/,]\\s*(?:approx\\.?\\s*)?" + F_STR, "gi"), "");
    cleaned = cleaned.replace(new RegExp("\\s*\\(\\s*(?:approx\\.?\\s*)?" + F_STR + "\\s*\\)", "gi"), "");
    cleaned = cleaned.replace(new RegExp("\\s*(?:approx\\.?\\s*)?" + F_STR, "gi"), "");
  } else {
    // 3. Celsius is NOT present, convert Fahrenheit to Celsius
    cleaned = cleaned.replace(
      new RegExp(F_STR, "gi"),
      (match) => {
        const nums = match.match(/\d+(?:\.\d+)?/g);
        if (nums && nums.length === 2) {
          const c1 = Math.round(((parseFloat(nums[0]) - 32) * 5) / 9);
          const c2 = Math.round(((parseFloat(nums[1]) - 32) * 5) / 9);
          const sep = /to/i.test(match) ? " to " : " - ";
          return `${c1}°C${sep}${c2}°C`;
        } else if (nums && nums.length === 1) {
          const c = Math.round(((parseFloat(nums[0]) - 32) * 5) / 9);
          return `${c}°C`;
        }
        return match;
      }
    );
  }

  return cleaned.replace(/\(\s*\)/g, "").replace(/\s{2,}/g, " ").trim();
};
import { identifySeed } from "../services/api";
import "./SeedIdentification.css";

function SeedIdentification() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [identifying, setIdentifying] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);

  // Clear previous state when a new image is selected
  const handleFile = (file) => {
    if (!file) return;

    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setErrorMsg("Unsupported file format. Please upload JPG, PNG, or WEBP.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg("File size exceeds 10MB limit. Please choose a smaller image.");
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setErrorMsg("");
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
  };

  const handleIdentify = async () => {
    if (!selectedFile) return;

    setIdentifying(true);
    setResult(null);
    setErrorMsg("");

    try {
      const response = await identifySeed(selectedFile);
      setResult(response);
      if (!response.success) {
        setErrorMsg(response.message || "Seed identification service is temporarily unavailable.");
      }
    } catch (err) {
      console.error("Seed identification error:", err);
      setErrorMsg("Unable to connect to PlantAI backend. Please check your connection.");
    } finally {
      setIdentifying(false);
    }
  };

  const seedData = result?.data || result;
  const isIdentified = Boolean(result?.success && (result?.status === "identified" || result?.seed_name));
  const isLowConfidence = result?.status === "low_confidence" || result?.status === "uncertain";

  // Uses and Benefits extraction
  const usesAndBenefits = seedData?.uses_and_benefits || result?.uses_and_benefits;
  const hasAnyUses = Boolean(
    usesAndBenefits && (
      (usesAndBenefits.common_uses && usesAndBenefits.common_uses.length > 0) ||
      (usesAndBenefits.nutritional_benefits && usesAndBenefits.nutritional_benefits.length > 0) ||
      (usesAndBenefits.nutritional_value && usesAndBenefits.nutritional_value.length > 0) ||
      (usesAndBenefits.health_benefits && usesAndBenefits.health_benefits.length > 0) ||
      (usesAndBenefits.environmental_benefits && usesAndBenefits.environmental_benefits.length > 0) ||
      (usesAndBenefits.practical_uses && usesAndBenefits.practical_uses.length > 0) ||
      (usesAndBenefits.practical_applications && usesAndBenefits.practical_applications.length > 0)
    )
  );

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <div className="page-badge">
          <Sprout size={14} />
          <span>Botanical Seed Recognition</span>
        </div>
        <h1 className="page-title">Seed Identification</h1>
        <p className="page-subtitle">
          Upload a clear close-up photograph of a seed, grain, or pod to determine its botanical species taxonomy.
        </p>
      </header>

      {/* 2-Column Seed Workspace */}
      <div className="seed-workspace-grid">
        {/* Left: Upload Workspace */}
        <div className="seed-left-panel">
          <div className="plant-card seed-upload-card">
            <h3 className="panel-title">Seed Specimen Upload</h3>
            <p className="panel-subtitle">Upload a macro or close-up photo of a seed on a contrasting background</p>

            {!previewUrl ? (
              <div
                className={`dropzone ${isDragOver ? "active" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById("seed-file-input").click()}
              >
                <div className="dropzone-icon-wrap">
                  <UploadCloud size={28} />
                </div>
                <div className="dropzone-text">Click to upload seed photo or drag & drop</div>
                <div className="dropzone-hint">Place seeds on a plain background for maximum recognition accuracy</div>
                <input
                  id="seed-file-input"
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={handleInputChange}
                  hidden
                />
              </div>
            ) : (
              <div className="uploaded-preview-wrapper">
                <div className="preview-container">
                  <img src={previewUrl} alt="Seed Specimen Preview" className="preview-image" />
                  
                  {/* Laser scan animation when analyzing */}
                  {identifying && (
                    <>
                      <div className="scan-beam"></div>
                      <div className="scan-overlay-grid"></div>
                    </>
                  )}

                  <button
                    className="btn-remove-preview"
                    onClick={handleRemoveImage}
                    title="Remove image"
                    disabled={identifying}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="preview-actions">
                  <button
                    className="btn btn-primary btn-analyze"
                    onClick={handleIdentify}
                    disabled={identifying}
                  >
                    {identifying ? (
                      <>
                        <span className="spinner"></span>
                        <span>Analyzing seed morphology...</span>
                      </>
                    ) : (
                      <>
                        <Sprout size={18} />
                        <span>Identify Seed</span>
                      </>
                    )}
                  </button>

                  <button
                    className="btn btn-outline btn-reset"
                    onClick={handleRemoveImage}
                    disabled={identifying}
                  >
                    <RotateCcw size={16} />
                    <span>Choose Another Seed</span>
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

        {/* Right: Result Panel */}
        <div className="seed-right-panel">
          <div className="plant-card seed-result-panel-card">
            <div className="result-panel-header">
              <h3 className="panel-title">Seed Classification</h3>
            </div>

            {/* State 1: Empty State */}
            {!result && !identifying && (
              <div className="empty-analysis-state">
                <div className="empty-state-icon">
                  <Sprout size={36} />
                </div>
                <h4>Ready for Seed Inspection</h4>
                <p>Upload a photograph of a seed, nut, grain, or pod to initiate optical taxonomy.</p>
                <div className="guidelines-card">
                  <strong>Photography tips for seed classification:</strong>
                  <ul>
                    <li>Use a neutral, plain background (such as white paper)</li>
                    <li>Ensure sharp camera focus on the seed coat and texture</li>
                    <li>Avoid extreme distance or blurry macro captures</li>
                  </ul>
                </div>
              </div>
            )}

            {/* State 2: Identifying Loading Animation */}
            {identifying && (
              <div className="loading-analysis-state">
                <div className="loading-radar-ring">
                  <div className="radar-pulse"></div>
                  <Sprout size={32} className="radar-icon" />
                </div>
                <h4>Analyzing Seed Morphology</h4>
                <p>Comparing seed coat texture, color gradients, and geometric contours with botanical taxonomy...</p>
                <div className="loading-step-list">
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Morphological contour segmentation</span>
                  </div>
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Taxonomic fruit/seed database matching</span>
                  </div>
                  <div className="loading-step active">
                    <span className="step-bullet"></span>
                    <span>Strict confidence threshold validation</span>
                  </div>
                </div>
              </div>
            )}

            {/* State 2b: Unsuccessful / API Notice */}
            {result && !result.success && !isLowConfidence && (
              <div className="alert-banner alert-error" style={{ marginTop: "16px" }}>
                <AlertTriangle size={20} />
                <div>
                  <strong style={{ fontSize: "15px" }}>Identification Notice</strong>
                  <p style={{ marginTop: "4px", fontSize: "13.5px" }}>
                    {result.message || "Kindwise could not identify this image. Please check your image or credentials."}
                  </p>
                </div>
              </div>
            )}

            {/* State 3: Low Confidence Warning */}
            {isLowConfidence && (
              <div className="low-confidence-result-state">
                <div className="alert-banner alert-warning">
                  <AlertTriangle size={20} />
                  <div>
                    <strong style={{ fontSize: "15px" }}>Low confidence identification</strong>
                    <p style={{ marginTop: "4px", fontSize: "13.5px" }}>
                      The image does not provide enough evidence for a reliable seed identification.
                    </p>
                    <p style={{ marginTop: "4px", fontSize: "13px", color: "var(--text-secondary)" }}>
                      Try placing the seed on a plain, contrasting surface with brighter ambient lighting.
                    </p>
                    
                  </div>
                </div>

                {seedData?.candidates && seedData.candidates.length > 0 && (
                  <div className="candidate-list">
                    <h5 className="candidates-heading">Possible Candidate Taxa:</h5>
                    {seedData.candidates.slice(0, 3).map((cand, idx) => (
                      <div key={idx} className="candidate-item">
                        <div className="candidate-names">
                          <strong>{cand.common_name || cand.scientific_name}</strong>
                          <em>({cand.scientific_name})</em>
                        </div>
                        
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* State 4: Successful Identification */}
            {isIdentified && seedData && (
              <div className="seed-identified-content">
                <div className="seed-result-card-inner">
                  <span className="species-tag">Seed Identified</span>
                  
                  <div className="seed-name-block">
                    <div className="field-group">
                      <span className="field-label">Common Name</span>
                      <h2 className="seed-common-name">
                        {seedData.common_name || seedData.seed_name}
                      </h2>
                    </div>

                    <div className="field-group" style={{ marginTop: "12px" }}>
                      <span className="field-label">Scientific Name</span>
                      <div className="seed-scientific-name">
                        <em>{seedData.scientific_name || seedData.seed_name}</em>
                      </div>
                      {seedData.class_index !== undefined && (
                        <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--text-muted)" }}>
                          <span>Model Class #{seedData.class_index}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Key Identification Features */}
                  {(seedData.seed_morphology || seedData.identifying_features || seedData.characteristics) && (
                    <div className="seed-section-card key-features-card">
                      <div className="seed-section-header">
                        <Sparkles size={16} className="text-emerald" />
                        <span className="seed-section-title">Key Identification Features</span>
                      </div>
                      {Array.isArray(seedData.identifying_features || seedData.characteristics) ? (
                        <ul className="seed-features-list">
                          {(seedData.identifying_features || seedData.characteristics).map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="seed-section-text">
                          {seedData.seed_morphology || seedData.identifying_features || seedData.characteristics}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Germination Guide */}
                  {seedData.germination_guide && (
                    <div className="seed-section-card germination-card">
                      <div className="seed-section-header">
                        <Sprout size={16} className="text-emerald" />
                        <span className="seed-section-title">Germination Guide</span>
                      </div>
                      {typeof seedData.germination_guide === "object" ? (
                        <div className="seed-guide-grid">
                          {seedData.germination_guide.preparation && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Seed Preparation</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.germination_guide.preparation)}</p>
                            </div>
                          )}
                          {seedData.germination_guide.germination_time && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Approximate Germination Time</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.germination_guide.germination_time)}</p>
                            </div>
                          )}
                          {seedData.germination_guide.conditions && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Germination Conditions</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.germination_guide.conditions)}</p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="seed-section-text">{sanitizeCelsius(seedData.germination_guide)}</p>
                      )}
                    </div>
                  )}

                  {/* Growing Instructions */}
                  {seedData.growing_instructions && (
                    <div className="seed-section-card growing-card">
                      <div className="seed-section-header">
                        <Sparkles size={16} className="text-accent" />
                        <span className="seed-section-title">Growing Instructions</span>
                      </div>
                      {typeof seedData.growing_instructions === "object" ? (
                        <div className="seed-guide-grid">
                          {seedData.growing_instructions.soil && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Soil & Growing Medium</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.growing_instructions.soil)}</p>
                            </div>
                          )}
                          {seedData.growing_instructions.planting_depth && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Planting Depth & Method</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.growing_instructions.planting_depth)}</p>
                            </div>
                          )}
                          {seedData.growing_instructions.watering && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Watering Instructions</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.growing_instructions.watering)}</p>
                            </div>
                          )}
                          {seedData.growing_instructions.sunlight && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Sunlight Requirements</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.growing_instructions.sunlight)}</p>
                            </div>
                          )}
                          {seedData.growing_instructions.transplanting && (
                            <div className="seed-guide-item">
                              <span className="seed-guide-label">Transplanting Guidance</span>
                              <p className="seed-guide-value">{sanitizeCelsius(seedData.growing_instructions.transplanting)}</p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="seed-section-text">{sanitizeCelsius(seedData.growing_instructions)}</p>
                      )}
                    </div>
                  )}

                  {/* Seed Uses and Benefits Section */}
                  {hasAnyUses && (
                    <div className="seed-section-card seed-uses-benefits-card">
                      <div className="seed-section-header">
                        <Sparkles size={16} className="text-emerald" />
                        <span className="seed-section-title">Uses and Benefits</span>
                      </div>

                      <div className="seed-uses-grid">
                        {/* 1. Common Uses */}
                        {usesAndBenefits.common_uses?.length > 0 && (
                          <div className="seed-use-item">
                            <div className="seed-use-item-header">
                              <Sparkles size={14} className="text-emerald" />
                              <span className="seed-use-item-title">Common Uses</span>
                            </div>
                            <ul className="seed-use-bullet-list">
                              {usesAndBenefits.common_uses.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* 2. Nutritional Benefits */}
                        {((usesAndBenefits.nutritional_benefits?.length > 0) || (usesAndBenefits.nutritional_value?.length > 0)) && (
                          <div className="seed-use-item seed-use-item-nutrition">
                            <div className="seed-use-item-header">
                              <Apple size={14} className="text-emerald" />
                              <span className="seed-use-item-title">Nutritional Benefits</span>
                            </div>
                            <ul className="seed-use-bullet-list">
                              {(usesAndBenefits.nutritional_benefits || usesAndBenefits.nutritional_value).map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* 3. Health Benefits */}
                        {usesAndBenefits.health_benefits?.length > 0 && (
                          <div className="seed-use-item">
                            <div className="seed-use-item-header">
                              <Heart size={14} className="text-emerald" />
                              <span className="seed-use-item-title">Health Benefits</span>
                            </div>
                            <ul className="seed-use-bullet-list">
                              {usesAndBenefits.health_benefits.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* 4. Environmental Benefits */}
                        {usesAndBenefits.environmental_benefits?.length > 0 && (
                          <div className="seed-use-item">
                            <div className="seed-use-item-header">
                              <Globe size={14} className="text-emerald" />
                              <span className="seed-use-item-title">Environmental Benefits</span>
                            </div>
                            <ul className="seed-use-bullet-list">
                              {usesAndBenefits.environmental_benefits.map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* 5. Other Practical Uses */}
                        {((usesAndBenefits.practical_uses?.length > 0) || (usesAndBenefits.practical_applications?.length > 0)) && (
                          <div className="seed-use-item seed-use-item-full">
                            <div className="seed-use-item-header">
                              <CheckCircle2 size={14} className="text-emerald" />
                              <span className="seed-use-item-title">Other Practical Uses</span>
                            </div>
                            <ul className="seed-use-bullet-list">
                              {(usesAndBenefits.practical_uses || usesAndBenefits.practical_applications).map((item, idx) => (
                                <li key={idx}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action button: Identify Another Seed */}
                <div style={{ marginTop: "24px", textAlign: "center" }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleRemoveImage}
                    style={{ width: "100%", padding: "13px" }}
                  >
                    <RotateCcw size={16} />
                    <span>Identify Another Seed</span>
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

export default SeedIdentification;
