import React, { useState } from "react";
import { 
  Activity, 
  UploadCloud, 
  X, 
  AlertTriangle, 
  ShieldCheck, 
  ShieldAlert, 
  HelpCircle,
  Eye, 
  RotateCcw,
  Info,
  Droplets,
  CheckCircle2,
  Shield,
  AlertCircle
} from "lucide-react";
import { checkPlantHealth } from "../services/api";
import "./PlantHealth.css";

function PlantHealth() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);

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

  const handleDiagnose = async () => {
    if (!selectedFile) return;

    setDiagnosing(true);
    setResult(null);
    setErrorMsg("");

    try {
      const response = await checkPlantHealth(selectedFile);
      setResult(response);
      if (!response.success && response.status === "error") {
        setErrorMsg(response.message || "Plant health assessment service is temporarily unavailable.");
      }
    } catch (err) {
      console.error("Plant health diagnosis error:", err);
      setErrorMsg("Unable to connect to PlantAI. Please ensure the backend server is running.");
    } finally {
      setDiagnosing(false);
    }
  };

  const healthData = result?.data;
  const isAnalyzed = result?.success && result?.status === "analyzed";
  const healthStatus = healthData?.health_status || (result?.status === "uncertain" ? "uncertain" : "");
  const isHealthy = isAnalyzed && healthStatus === "healthy";
  const isDiseased = isAnalyzed && healthStatus === "possible_disease";
  const isUncertain = result?.status === "uncertain" || healthStatus === "uncertain";
  const isValidationErr = result?.status === "validation_error";

  // 1. Problem Level calculation (Low, Medium, High, None)
  const getProblemLevel = () => {
    if (isHealthy) {
      return {
        level: "None",
        badgeClass: "badge-level-none",
        description: "Healthy foliage with no visible signs of damage or distress on this leaf."
      };
    }

    const sev = (healthData?.severity || "").toLowerCase();
    if (sev.includes("extensive") || sev.includes(">50%") || sev.includes("high") || sev.includes("severe")) {
      return {
        level: "High",
        badgeClass: "badge-level-high",
        description: "Extensive visible damage on this leaf that needs closer inspection. This assessment applies only to the visible leaf; the whole-plant condition is unverified."
      };
    }
    if (sev.includes("moderate") || sev.includes("15") || sev.includes("medium")) {
      return {
        level: "Medium",
        badgeClass: "badge-level-medium",
        description: "Noticeable symptoms on this leaf that need attention. This assessment applies only to the visible leaf; the whole-plant condition is unverified."
      };
    }

    return {
      level: "Low",
      badgeClass: "badge-level-low",
      description: "Minor visible symptoms on this leaf. This assessment applies only to the visible leaf; the whole-plant condition is unverified."
    };
  };

  // 4. Simplify Scientific Names into plain English with a short explanation
  const getSimplifiedCondition = () => {
    if (!healthData?.condition) {
      return {
        name: "Foliar Stress",
        explanation: "The leaf may have visible signs of distress. Color changes and stress marks suggest this possibility."
      };
    }

    let clean = healthData.condition
      .replace(/^suspected\s*\/\s*possible:\s*/i, "")
      .replace(/^possible:\s*/i, "")
      .replace(/^suspected:\s*/i, "")
      .trim();

    const lower = clean.toLowerCase();

    if (lower.includes("rhytisma") || lower.includes("tar spot")) {
      return {
        name: "Rhytisma (Tar Spot)",
        explanation: "The leaf may have a fungal problem called Tar Spot. The dark spots suggest this possibility."
      };
    }
    if (lower.includes("puccinia") || lower.includes("rust")) {
      return {
        name: "Rust Fungus (Pucciniales)",
        explanation: "The leaf may have a fungal problem called Rust. The reddish-orange or yellow spots suggest this possibility."
      };
    }
    if (lower.includes("cercospora")) {
      return {
        name: "Cercospora Leaf Spot",
        explanation: "The leaf may have a fungal issue called Cercospora. The small circular brown spots suggest this possibility."
      };
    }
    if (lower.includes("alternaria")) {
      return {
        name: "Alternaria (Dark Leaf Spot)",
        explanation: "The leaf may have a fungal problem called Alternaria. The dark target-like spots suggest this possibility."
      };
    }
    if (lower.includes("septoria")) {
      return {
        name: "Septoria Leaf Spot",
        explanation: "The leaf may have a fungal issue called Septoria. The small dark spots with lighter centers suggest this possibility."
      };
    }
    if (lower.includes("mildew") || lower.includes("oidium") || lower.includes("erysiph")) {
      return {
        name: "Powdery Mildew",
        explanation: "The leaf may have a fungal problem called Powdery Mildew. The white or pale powdery coating suggests this possibility."
      };
    }
    if (lower.includes("colletotrichum") || lower.includes("anthracnose")) {
      return {
        name: "Anthracnose (Fungal Blight)",
        explanation: "The leaf may have a fungal issue called Anthracnose. The dark sunken spots suggest this possibility."
      };
    }
    if (lower.includes("xanthomonas") || lower.includes("pseudomonas") || lower.includes("bacteri")) {
      return {
        name: "Bacterial Leaf Spot",
        explanation: "The leaf may have a bacterial issue. The dark spots with yellow halos suggest this possibility."
      };
    }
    if (lower.includes("nutrient") || lower.includes("chlorosis") || lower.includes("deficiency") || lower.includes("nitrogen") || lower.includes("iron")) {
      return {
        name: "Nutrient Imbalance (Chlorosis)",
        explanation: "The leaf may have a nutrient shortage. The yellowing areas suggest the roots might need better nutrient absorption."
      };
    }
    if (lower.includes("water excess") || lower.includes("overwater") || lower.includes("rot")) {
      return {
        name: "Overwatering / Excess Moisture",
        explanation: "The plant may be receiving excess moisture. The yellowing foliage suggests the soil may be staying wet for too long."
      };
    }
    if (lower.includes("underwater") || lower.includes("dry")) {
      return {
        name: "Underwatering / Moisture Stress",
        explanation: "The plant may need more moisture. The dry or curled leaf areas suggest the soil may have dried out."
      };
    }
    if (lower.includes("pest") || lower.includes("mite") || lower.includes("thrip") || lower.includes("aphid") || lower.includes("scale")) {
      return {
        name: "Sap-Sucking Pests",
        explanation: "The leaf may have tiny garden pests. The small discolored specks suggest possible insect activity."
      };
    }

    return {
      name: clean,
      explanation: `The leaf may have signs of ${clean}. The visible color changes suggest this possibility.`
    };
  };

  // Section 3: 2–3 short bullet points about visible symptoms
  const getSimpleSymptoms = () => {
    if (isHealthy) {
      return [
        "Leaves have a healthy, uniform green color.",
        "No visible spots, holes, or pest damage on this leaf."
      ];
    }
    const raw = [
      ...(healthData?.gemini_insights?.confirmed_observations || []),
      ...(healthData?.gemini_insights?.visible_observations || []),
      ...(healthData?.symptoms || [])
    ].filter(Boolean);

    const cleaned = raw.map((item) => {
      let text = item
        .replace(/Chlorotic yellowing observed across [\d.]+% of sampled leaf surface\./i, "Yellowing visible across parts of the leaf surface.")
        .replace(/Necrotic lesions\/spots observed across [\d.]+% of sampled leaf surface\./i, "Dark spots or lesions visible on the leaf.")
        .replace(/Visible manifestations characteristic of .* on sampled leaf\./i, "Visible discoloration marks on the leaf.")
        .trim();
      return text;
    });

    const unique = Array.from(new Set(cleaned)).filter(Boolean);

    if (unique.length > 0) {
      return unique.slice(0, 3);
    }

    return [
      "Noticeable yellowing or color fading on the leaf.",
      "Visible patches or distress marks on leaf surface."
    ];
  };

  // Section 5: What To Do Now (2–3 practical actions)
  const getWhatToDoNow = () => {
    if (isHealthy) {
      return [
        "Keep following your normal routine—no changes or leaf pruning needed.",
        "Water only when the top 1 to 2 inches of soil feel dry to the touch.",
        "Keep the plant in bright, indirect natural sunlight."
      ];
    }

    const cond = (healthData?.condition || "").toLowerCase();
    const sev = (healthData?.severity || "").toLowerCase();
    const isHeavyDamage = sev.includes("extensive") || sev.includes(">50%") || sev.includes("high") || sev.includes("severe");
    const isFungal = cond.includes("rhytisma") || cond.includes("puccinia") || cond.includes("rust") || cond.includes("spot") || cond.includes("blight") || cond.includes("mildew") || cond.includes("fung");
    const isPest = cond.includes("pest") || cond.includes("mite") || cond.includes("thrip") || cond.includes("aphid") || cond.includes("scale");

    const actions = [];

    // Action 1: Check soil moisture depth and inspect under leaves before treatments
    if (isPest) {
      actions.push("Check under the leaves and along leaf stems for tiny pests, and gently wipe leaves with a damp cloth.");
    } else {
      actions.push("Check soil moisture 2 inches deep and inspect under the leaves before starting any treatments.");
    }

    // Action 2: Careful leaf removal advice (only if badly damaged/rotting, do not remove every spotted/yellow leaf)
    if (isHeavyDamage) {
      actions.push("If this leaf is badly damaged or rotting, gently snip it off with clean scissors to protect the rest of the plant.");
    } else {
      actions.push("Do not remove every yellow or spotted leaf. If the leaf is still mostly green, keep it on the plant so it can produce energy.");
    }

    // Action 3: Practical follow-up (avoid unnecessary treatments, heavy pruning, or repotting)
    if (isFungal) {
      actions.push("Water strictly at the soil base to keep leaves dry, and avoid chemical sprays unless spotting spreads.");
    } else if (isPest) {
      actions.push("Isolate the plant slightly and rinse foliage with clean water rather than harsh pesticides.");
    } else {
      actions.push("Ensure your pot drains properly and adjust watering gradually—avoid repotting or heavy pruning unless roots show rot.");
    }

    return actions.slice(0, 3);
  };

  // Section 6: Future Precautions (2–3 short tips specific to problem)
  const getFuturePrecautions = () => {
    if (isHealthy) {
      return [
        "Water at the soil base according to moisture, not on a fixed calendar schedule.",
        "Keep the plant in good airflow and bright, indirect light.",
        "Check leaves regularly for early signs of disease or pests."
      ];
    }

    const cond = (healthData?.condition || "").toLowerCase();

    if (cond.includes("rhytisma") || cond.includes("puccinia") || cond.includes("rust") || cond.includes("spot") || cond.includes("blight") || cond.includes("mildew") || cond.includes("fung")) {
      return [
        "Water at the base according to soil moisture so the leaves stay dry.",
        "Keep the plant in good airflow and suitable light to prevent moisture buildup.",
        "Clean gardening tools after touching diseased leaves so spores do not spread."
      ];
    }

    if (cond.includes("pest") || cond.includes("mite") || cond.includes("thrip") || cond.includes("aphid") || cond.includes("scale")) {
      return [
        "Check under leaves weekly with good light to catch pests early.",
        "Keep the plant in good airflow and wipe dust off leaves periodically.",
        "Clean gardening tools after touching affected foliage to avoid transferring pests."
      ];
    }

    if (cond.includes("water excess") || cond.includes("overwater") || cond.includes("rot")) {
      return [
        "Water at the base according to soil moisture—always feel 2 inches deep before adding water.",
        "Make sure the pot drains freely and never leave standing water in the saucer.",
        "Keep the plant in good airflow and suitable light to help soil dry evenly."
      ];
    }

    if (cond.includes("underwater") || cond.includes("dry")) {
      return [
        "Water at the base whenever the top inch of soil feels dry, soaking until drainage occurs.",
        "Keep the plant in suitable light away from drying heat vents or air conditioners.",
        "Check soil moisture regularly during hot or dry weather."
      ];
    }

    // Nutrient deficiency / chlorosis
    return [
      "Water at the base according to soil moisture so roots can absorb nutrients properly.",
      "Keep the plant in good airflow and suitable light so leaves produce healthy green chlorophyll.",
      "Clean gardening tools after trimming any damaged foliage."
    ];
  };

  const problemLevel = getProblemLevel();
  const simplifiedCondition = getSimplifiedCondition();
  const symptomsList = getSimpleSymptoms();
  const actionsList = getWhatToDoNow();
  const precautionsList = getFuturePrecautions();

  return (
    <div className="page-container">
      {/* Header */}
      <header className="page-header">
        <div className="page-badge">
          <Activity size={14} />
          <span>Plant Health Assistant</span>
        </div>
        <h1 className="page-title">Plant Health & Care Check</h1>
        <p className="page-subtitle">
          Upload a clear photo of your plant's leaf to quickly see if it's healthy, what might be wrong, and what simple steps to take.
        </p>
      </header>

      {/* 2-Column Workspace */}
      <div className="health-workspace-grid">
        {/* Left: Upload Workspace */}
        <div className="health-left-panel">
          <div className="plant-card health-upload-card">
            <h3 className="panel-title">Upload Leaf Photo</h3>
            <p className="panel-subtitle">Take or choose a clear close-up picture of the leaf</p>

            {!previewUrl ? (
              <div
                className={`dropzone ${isDragOver ? "active" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => document.getElementById("health-file-input").click()}
              >
                <div className="dropzone-icon-wrap">
                  <UploadCloud size={28} />
                </div>
                <div className="dropzone-text">Click to upload leaf photo or drag & drop</div>
                <div className="dropzone-hint">Clear, well-lit photos give the most accurate result</div>
                <input
                  id="health-file-input"
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={handleInputChange}
                  hidden
                />
              </div>
            ) : (
              <div className="uploaded-preview-wrapper">
                <div className="preview-container">
                  <img src={previewUrl} alt="Leaf Preview" className="preview-image" />
                  
                  {diagnosing && (
                    <>
                      <div className="scan-beam"></div>
                      <div className="scan-overlay-grid"></div>
                    </>
                  )}

                  <button
                    className="btn-remove-preview"
                    onClick={handleRemoveImage}
                    title="Remove image"
                    disabled={diagnosing}
                  >
                    <X size={16} />
                  </button>
                </div>

                <div className="preview-actions">
                  <button
                    className="btn btn-primary btn-analyze"
                    onClick={handleDiagnose}
                    disabled={diagnosing}
                  >
                    {diagnosing ? (
                      <>
                        <span className="spinner"></span>
                        <span>Checking leaf health...</span>
                      </>
                    ) : (
                      <>
                        <Activity size={18} />
                        <span>Check Plant Health</span>
                      </>
                    )}
                  </button>

                  <button
                    className="btn btn-outline btn-reset"
                    onClick={handleRemoveImage}
                    disabled={diagnosing}
                  >
                    <RotateCcw size={16} />
                    <span>Choose Another Photo</span>
                  </button>
                </div>
              </div>
            )}

            {isValidationErr && (
              <div className="alert-banner alert-warning" style={{ marginTop: "16px" }}>
                <AlertTriangle size={18} />
                <div>
                  <strong>{result.message}</strong>
                  <p style={{ marginTop: "4px", fontSize: "13px" }}>
                    Please make sure your picture shows a clear view of the plant leaf.
                  </p>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="alert-banner alert-error" style={{ marginTop: "16px" }}>
                <AlertTriangle size={18} />
                <div>{errorMsg}</div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Concise 7-Section Result Panel */}
        <div className="health-right-panel">
          <div className="plant-card health-result-panel-card">
            <div className="result-panel-header">
              <h3 className="panel-title">Health Report</h3>
              {isHealthy && (
                <span className="badge badge-success">
                  <ShieldCheck size={13} />
                  <span>Healthy</span>
                </span>
              )}
              {isDiseased && (
                <span className="badge badge-warning">
                  <ShieldAlert size={13} />
                  <span>Problem</span>
                </span>
              )}
              {isUncertain && (
                <span className="badge badge-neutral">
                  <HelpCircle size={13} />
                  <span>Needs Clearer Photo</span>
                </span>
              )}
            </div>

            {/* State 1: Ready / Empty State */}
            {!result && !diagnosing && (
              <div className="empty-analysis-state">
                <div className="empty-state-icon">
                  <Activity size={36} />
                </div>
                <h4>Ready to Check Your Plant</h4>
                <p>Upload a photo of your leaf to get a short, easy-to-understand health report.</p>
                <div className="guidelines-card">
                  <strong>Photo tips for best results:</strong>
                  <ul>
                    <li>Take a close, clear photo of the affected leaf</li>
                    <li>Use good natural light without heavy shadows</li>
                    <li>Hold the camera steady so the leaf is in focus</li>
                  </ul>
                </div>
              </div>
            )}

            {/* State 2: Diagnosing State */}
            {diagnosing && (
              <div className="loading-analysis-state">
                <div className="loading-radar-ring">
                  <div className="radar-pulse"></div>
                  <Activity size={32} className="radar-icon" />
                </div>
                <h4>Checking Leaf Health</h4>
                <p>Looking at leaf color, texture, and visible patterns...</p>
              </div>
            )}

            {/* State 3: Uncertain Assessment */}
            {isUncertain && (
              <div className="simple-report-card">
                <div className="alert-banner alert-warning">
                  <AlertTriangle size={20} />
                  <div>
                    <strong style={{ fontSize: "15px" }}>Needs a Clearer Photo</strong>
                    <p style={{ marginTop: "4px", fontSize: "13.5px" }}>
                      The image was too blurry or unclear to tell for sure.
                    </p>
                  </div>
                </div>

                <div className="simple-section">
                  <h4 className="simple-section-title">What To Do Now</h4>
                  <ul className="simple-bullet-list">
                    <li>Take a closer photo in bright natural daylight.</li>
                    <li>Make sure the leaf is in sharp focus before uploading.</li>
                  </ul>
                </div>

                <div className="simple-note-box">
                  <Info size={16} />
                  <span><strong>Note:</strong> Clear lighting and sharp focus help PlantAI give you an accurate suggestion.</span>
                </div>
              </div>
            )}

                        {/* State 4 & 5: Clean 6-Section Report */}
            {(isHealthy || isDiseased) && healthData && (
              <div className="simple-report-card">
                
                {/* 1. Plant Health */}
                <div className="simple-section simple-hero-section">
                  <div className="plant-health-header-block">
                    <div className="plant-health-status-wrap">
                      <span className={`status-pill ${isHealthy ? "status-pill-healthy" : "status-pill-disease"}`}>
                        {isHealthy ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
                        <span>{isHealthy ? "Healthy" : "Problem"}</span>
                      </span>
                    </div>

                    {healthData.plant_name && (
                      <div className="simple-specimen-line">
                        Plant Identified: <strong>{healthData.plant_name}</strong>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. Problem Level */}
                <div className="simple-section">
                  <div className="simple-section-header">
                    <AlertCircle size={17} className="text-amber" />
                    <h4 className="simple-section-title">
                      Problem Level: <span className={`problem-level-pill ${problemLevel.badgeClass}`}>{problemLevel.level}</span>
                    </h4>
                  </div>
                  <p className="problem-level-desc">{problemLevel.description}</p>
                </div>

                {/* 3. What I Found */}
                <div className="simple-section">
                  <div className="simple-section-header">
                    <Eye size={17} className="text-accent" />
                    <h4 className="simple-section-title">What I Found</h4>
                  </div>
                  <ul className="simple-bullet-list">
                    {symptomsList.map((sym, idx) => (
                      <li key={idx}>{sym}</li>
                    ))}
                  </ul>
                </div>

                {/* 4. Problem */}
                <div className="simple-section">
                  <div className="simple-section-header">
                    <Droplets size={17} className="text-amber" />
                    <h4 className="simple-section-title">Problem</h4>
                  </div>
                  {isHealthy ? (
                    <p className="simple-problem-text">
                      Your plant looks healthy with good green color and no major disease detected.
                    </p>
                  ) : (
                    <div className="problem-block">
                      <div className="problem-name">
                        <strong>{simplifiedCondition.name}</strong>
                      </div>
                      <p className="problem-desc">{simplifiedCondition.explanation}</p>
                    </div>
                  )}
                </div>

                {/* 5. What To Do Now */}
                <div className="simple-section">
                  <div className="simple-section-header">
                    <CheckCircle2 size={17} className="text-emerald" />
                    <h4 className="simple-section-title">What To Do Now</h4>
                  </div>
                  <ul className="simple-bullet-list action-bullets">
                    {actionsList.map((act, idx) => (
                      <li key={idx}>{act}</li>
                    ))}
                  </ul>
                </div>

                {/* 6. Future Precautions */}
                <div className="simple-section">
                  <div className="simple-section-header">
                    <Shield size={17} className="text-accent" />
                    <h4 className="simple-section-title">Future Precautions</h4>
                  </div>
                  <ul className="simple-bullet-list precaution-bullets">
                    {precautionsList.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>

              </div>
            )}

          

          </div>
        </div>
      </div>
    </div>
  );
}

export default PlantHealth;
