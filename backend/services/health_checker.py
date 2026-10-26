import os
import requests
import json
import base64
import io
from PIL import Image
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .image_validator import validate_and_preprocess_image
from .gemini_service import analyze_plant_health as gemini_analyze_plant_health

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH, override=True)

PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
KINDWISE_API_KEY = os.getenv("KINDWISE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))

DISCLAIMER_TEXT = "This result is an AI-assisted botanical assessment and should not be treated as a definitive professional or scientific diagnosis."
SAFE_NEEM_GUIDANCE = "If considering neem oil or horticultural sprays, consult the manufacturer product label for exact dilution rates, perform a spot test on a single leaf first, and apply during dawn or dusk to prevent phototoxicity."

def _cautious_condition_name(name: Optional[str]) -> Optional[str]:
    """Ensures condition names are presented cautiously, never claiming confirmed diagnosis."""
    if not name:
        return None
    clean = name.strip()
    if clean.lower().startswith("suspected / possible:"):
        return clean
    if clean.lower().startswith("possible condition:"):
        return clean
    if clean.lower().startswith("suspected") or clean.lower().startswith("possible"):
        return f"Suspected / Possible: {clean.split(':', 1)[-1].strip()}"
    return f"Suspected / Possible: {clean}"

def _derive_severity(damage_ratio: float) -> str:
    """
    Evaluates foliar symptom severity on the uploaded leaf blade only.
    Explicitly avoids inferring whole-plant condition from a single leaf image.
    """
    if damage_ratio >= 0.50:
        return "Extensive foliar symptoms on sampled leaf (>50% leaf surface affected; whole-plant status unverified)"
    elif damage_ratio >= 0.15:
        return "Moderate foliar symptoms on sampled leaf (~15–50% leaf surface affected; whole-plant status unverified)"
    elif damage_ratio > 0.02:
        return "Mild foliar symptoms on sampled leaf (<15% leaf surface affected; whole-plant status unverified)"
    else:
        return "Foliar symptom severity uncertain on sampled leaf (whole-plant status unverified)"

def _estimate_visible_foliar_damage(image_bytes: bytes) -> Dict[str, Any]:
    """
    Evaluates chromatic distribution across foliage to measure chlorosis,
    necrosis/lesion area, and healthy chlorophyll.
    Excludes white/light studio background to accurately assess foliar surface.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_resized = img.resize((150, 150))
        pixels = list(img_resized.getdata())

        # Filter out white paper/studio background and extreme darkness
        foliage = [
            p for p in pixels 
            if not (p[0] > 230 and p[1] > 230 and p[2] > 230) 
            and not (p[0] < 20 and p[1] < 20 and p[2] < 20)
        ]
        if not foliage:
            foliage = pixels
        total_pixels = len(foliage)

        green_count = 0
        yellow_count = 0
        brown_count = 0
        white_count = 0

        for r, g, b in foliage:
            # Healthy green chlorophyll
            if g > r * 1.15 and g > b * 1.15 and g > 35:
                green_count += 1
            # Yellow / Chlorosis
            elif r > 115 and g > 115 and b < 100 and abs(r - g) < 55:
                yellow_count += 1
            # Necrotic brown / black spots / lesions
            elif r > 50 and g > 25 and b < 45 and r > g and r < 185 and g < 145:
                brown_count += 1
            # Powdery mildew (pale grayish foliar coating)
            elif 175 < r < 230 and 175 < g < 230 and 175 < b < 230 and abs(r - g) < 15 and abs(g - b) < 15:
                white_count += 1

        green_pct = green_count / total_pixels
        yellow_pct = yellow_count / total_pixels
        brown_pct = brown_count / total_pixels
        white_pct = white_count / total_pixels

        damage_ratio = yellow_pct + brown_pct + white_pct

        return {
            "green_pct": round(green_pct * 100, 1),
            "yellow_pct": round(yellow_pct * 100, 1),
            "brown_pct": round(brown_pct * 100, 1),
            "white_pct": round(white_pct * 100, 1),
            "damage_ratio": damage_ratio,
            "has_chlorosis": yellow_pct >= 0.08,
            "has_lesions": brown_pct >= 0.05,
            "has_powdery_film": white_pct >= 0.08
        }
    except Exception as e:
        print("Visible damage estimation error:", e)
        return {
            "green_pct": 50.0,
            "yellow_pct": 0.0,
            "brown_pct": 0.0,
            "white_pct": 0.0,
            "damage_ratio": 0.0,
            "has_chlorosis": False,
            "has_lesions": False,
            "has_powdery_film": False
        }

def _build_diagnostic_checks(condition_name: str = "", has_chlorosis: bool = False, has_lesions: bool = False) -> List[Dict[str, str]]:
    """
    Constructs 4 actionable physical diagnostic checks to verify root causes
    that cannot be definitively confirmed from a leaf photograph alone.
    """
    return [
        {
            "target": "Soil Moisture Depth",
            "action": "Probe 2 to 3 inches (5–7 cm) into the root zone with your finger or a calibrated soil moisture meter.",
            "interpretation": "Dense, waterlogged soil indicates overwatering or blocked container drainage; dry, crumbly soil indicates dehydration stress."
        },
        {
            "target": "Abaxial (Leaf Underside) Inspection",
            "action": "Examine the lower leaf surface and petiole junctions with a 10x magnifying lens or smartphone macro camera.",
            "interpretation": "Fine silk webbing signals spider mites; tiny moving yellow/black flecks indicate thrips, aphids, or scale colonies."
        },
        {
            "target": "Root System Health (If Symptoms Persist)",
            "action": "Only if foliar discoloration continues after watering adjustments, gently inspect the outer edge of the root ball.",
            "interpretation": "Healthy roots are firm and white or tan. Do not trim roots unless dark brown, soft, mushy tissue with a sour odor confirms root rot."
        },
        {
            "target": "Canopy & Light Exposure",
            "action": "Assess whether symptoms affect exclusively lower, older leaves or newly emerging upper crown growth.",
            "interpretation": "Basal foliage yellowing suggests mobile nutrient translocation (e.g. Nitrogen) or root stress; upper foliage scorching suggests intense direct sunlight or heat draft."
        }
    ]

def _filter_safe_treatments(treatments: List[str]) -> List[str]:
    """
    Filters out aggressive interventions (repotting, manure, fertilizer, foliar nutrients, root trimming)
    unless supported by physical evidence. Starts with soil-moisture and leaf-underside checks.
    """
    aggressive_keywords = [
        "replant", "repot", "fertiliz", "manure", "foliar nutrient",
        "trim root", "cut root", "root trim", "compost", "feed", "fertilise"
    ]
    safe = []
    for t in treatments:
        t_lower = t.lower()
        if not any(k in t_lower for k in aggressive_keywords):
            safe.append(t)
    return safe

def _build_yellow_leaf_investigation() -> Dict[str, Any]:
    """
    Constructs a dedicated multi-factor differential investigation for yellowing / chlorotic foliage.
    Presents probable contributing factors with supporting symptoms, diagnostic checks, and non-aggressive actions
    without fabricating comparative percentages. Avoids recommending repotting, manure, or fertilizers without evidence.
    """
    return {
        "title": "Foliar Chlorosis (Yellow Leaf) Differential Investigation",
        "description": "Leaf yellowing (chlorosis) indicates chlorophyll breakdown. It is frequently an abiotic disorder caused by cultural, moisture, or environmental imbalances rather than an isolated pathogen.",
        "factors": [
            {
                "factor_name": "Overwatering & Poor Drainage",
                "frequency": "Most Common",
                "supporting_symptoms": [
                    "Lower, older leaves turn pale yellow first and feel limp, soft, or soggy.",
                    "Potting soil remains saturated for days after watering; possible damp odor.",
                    "Roots may appear brown if oxygen starvation is prolonged."
                ],
                "diagnostic_check": "Probe 2 to 3 inches into the soil with your finger or a moisture meter. If damp and dense while leaves turn yellow, roots are starved of oxygen.",
                "corrective_actions": [
                    "Do not repot or trim roots without physical evidence of root rot. Start by testing soil moisture.",
                    "Withhold watering until the top 2-3 inches of soil dry out completely, and confirm container drainage holes are clear.",
                    "Ensure excess water does not stand in saucer trays."
                ]
            },
            {
                "factor_name": "Nutrient Deficiency (Nitrogen or Iron)",
                "frequency": "Common in container plants",
                "supporting_symptoms": [
                    "Nitrogen (N) Deficiency: Generalized, uniform pale yellowing starting on older bottom leaves as the plant translocates nitrogen to new growth.",
                    "Iron (Fe) Deficiency: Interveinal chlorosis where leaf tissue turns pale yellow or ivory while veins remain distinctly green, primarily on the newest top growth.",
                    "Magnesium (Mg) Deficiency: Chlorosis begins at leaf margins and advances inward between major veins."
                ],
                "diagnostic_check": "Determine whether yellowing started on the oldest lower leaves (mobile nutrients: Nitrogen) or youngest emerging top leaves (immobile nutrients: Iron).",
                "corrective_actions": [
                    "Do not apply fertilizers, manure, or foliar nutrients immediately, as excess salts can damage stressed roots.",
                    "Verify soil moisture depth first, as overwatering and root asphyxiation frequently mimic nutrient deficiencies.",
                    "If soil moisture is confirmed balanced and growth remains chlorotic, conduct a soil pH test before considering any light fertilizer."
                ]
            },
            {
                "factor_name": "Underwatering & Moisture Stress",
                "frequency": "Frequent in high-heat or dry climates",
                "supporting_symptoms": [
                    "Leaves turn pale yellow, brittle, and dry with crispy brown tips or margins.",
                    "Soil pulls away from the container edges and feels completely desiccated.",
                    "Foliage droops stiffly rather than feeling soggy or limp."
                ],
                "diagnostic_check": "Lift the pot to check weight or insert a wooden skewer. If lightweight and dry to the base, the root system is desiccated.",
                "corrective_actions": [
                    "Verify dryness 2-3 inches into the soil before watering thoroughly.",
                    "Hydrate slowly so moisture permeates the root zone evenly without waterlogging."
                ]
            },
            {
                "factor_name": "Natural Leaf Senescence (Aging)",
                "frequency": "Normal biological process",
                "supporting_symptoms": [
                    "Only the single lowest, oldest mature leaf gradually yellows and drops while new upper growth is vigorous and green.",
                    "No spots, webs, or systemic discoloration across remaining foliage."
                ],
                "diagnostic_check": "Check if yellowing is confined exclusively to the oldest basal leaves while all subsequent growth is healthy.",
                "corrective_actions": [
                    "No treatment or chemical application needed if only a single oldest lower leaf is aging.",
                    "Maintain regular watering checks and standard lighting."
                ]
            },
            {
                "factor_name": "Sap-Sucking Pests (Spider Mites, Thrips, Aphids)",
                "frequency": "Common indoor/greenhouse issue",
                "supporting_symptoms": [
                    "Stippled, mottled yellow flecks across the leaf blade rather than uniform color fading.",
                    "Fine webbing under leaves (spider mites) or sticky honeydew residue (aphids/scale).",
                    "Distorted, curled, or stunted new growth."
                ],
                "diagnostic_check": "Examine the underside of yellowing leaves with a magnifying lens or bright torch for tiny moving specks or webbing.",
                "corrective_actions": [
                    "Isolate the plant to prevent spreading.",
                    "Wipe leaf surfaces and undersides with lukewarm water to remove pests.",
                    SAFE_NEEM_GUIDANCE
                ]
            }
        ]
    }

def _derive_why_occurred(condition_name: str, is_healthy: bool) -> str:
    """Provides scientifically grounded explanations using possible contributing factors and verification steps."""
    if is_healthy:
        return (
            "The foliage demonstrates balanced chlorophyll synthesis, optimal turgor pressure, "
            "and an absence of pathogen colonization or visible environmental stress."
        )

    cond_lower = (condition_name or "").lower()

    if any(k in cond_lower for k in ["water excess", "overwater", "rot", "damping"]):
        return (
            "Possible contributing factors include excess root-zone moisture, compacted potting mix, or poor container drainage. "
            "Because foliar symptoms cannot confirm root asphyxiation or decay from a single photo, "
            "verify by probing soil moisture 2–3 inches deep and inspecting root firmness and color."
        )
    elif any(k in cond_lower for k in ["nutrient", "deficiency", "chlorosis", "nitrogen", "iron"]):
        return (
            "Possible contributing factors include nutrient uptake restrictions (such as nitrogen mobility or iron availability), "
            "soil pH imbalances, or moisture issues that restrict nutrient assimilation. "
            "Do not apply fertilizers or manure without physical evidence; verify soil moisture and test root health first."
        )
    elif any(k in cond_lower for k in ["rust", "puccinia"]):
        return (
            "Possible contributing factors include persistent foliar moisture and limited air circulation, "
            "which favor fungal spore germination. Verify by inspecting both leaf surfaces and adjacent leaves for active spore pustules."
        )
    elif any(k in cond_lower for k in ["spot", "blight", "cercospora", "alternaria", "septoria"]):
        return (
            "Possible contributing factors include overhead watering, water splash, or localized pathogen activity. "
            "Inspect whether spots are isolated dry lesions or spreading across multiple leaves."
        )
    elif any(k in cond_lower for k in ["mildew", "powdery"]):
        return (
            "Possible contributing factors include dry root medium combined with high ambient humidity and low light. "
            "Verify by gently wiping the surface to check if coating is superficial mycelium or mineral residue."
        )
    elif any(k in cond_lower for k in ["pest", "mite", "aphid", "scale", "thrip"]):
        return (
            "Possible contributing factors include sap-sucking pests puncturing foliar cells. "
            "Verify by inspecting the lower leaf surface and petiole junctions with a 10x magnifying lens."
        )
    else:
        return (
            "Possible contributing factors include cultural imbalances (moisture swings, lighting shifts) or opportunistic foliar stress. "
            "Physical inspection of soil moisture and root health is required to verify the underlying cause."
        )

def _identify_plant_name_safely(image_bytes: bytes) -> Optional[str]:
    """Identifies plant species via Pl@ntNet with strict timeout."""
    if not PLANTNET_API_KEY:
        return None
    try:
        url = "https://my-api.plantnet.org/v2/identify/all"
        res = requests.post(
            url,
            params={"api-key": PLANTNET_API_KEY, "lang": "en", "nb-results": 1},
            files={"images": ("plant.jpg", image_bytes, "image/jpeg")},
            data={"organs": ["leaf"]},
            timeout=10
        )
        if res.status_code == 200:
            results = res.json().get("results", [])
            if results:
                sp = results[0].get("species", {})
                sci = sp.get("scientificNameWithoutAuthor") or sp.get("scientificName")
                cnames = sp.get("commonNames", [])
                cname = cnames[0] if cnames else sci
                return f"{cname} ({sci})" if cname != sci else sci
    except Exception as e:
        print("Pl@ntNet identification non-blocking note:", e)
    return None

def check_health(
    image_bytes: bytes,
    filename: str = "health.jpg",
    content_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Accuracy-first Plant Health & Disease Assessment:
    1. Calibrated edge-density blur and exposure pre-flight validation.
    2. Local foliar chromatic pixel analysis (excluding studio backgrounds).
    3. Pl@ntNet species identification (non-blocking).
    4. Kindwise API pathology assessment.
    5. Google Gemini AI multimodal visual analysis (visible symptoms vs causes).
    6. Synergistic evaluation: NEVER marks diseased/yellow leaves as healthy.
    """
    # 1. Validation & Preprocessing
    is_valid, processed_bytes, val_error, quality_warning = validate_and_preprocess_image(
        image_bytes, filename, content_type, max_size=MAX_UPLOAD_SIZE
    )
    if not is_valid:
        return {
            "success": False,
            "status": "validation_error",
            "message": val_error or "Please upload a clear image of the plant or affected leaf.",
            "data": None
        }

    # 2. Local chromatic pixel analysis (excluding white/plain background)
    visual_stats = _estimate_visible_foliar_damage(processed_bytes)

    # 3. Identify plant species via Pl@ntNet
    identified_plant_name = _identify_plant_name_safely(processed_bytes)

    # 4. Call Kindwise API (if key available)
    kw_evaluated = False
    kw_data = None
    if KINDWISE_API_KEY:
        try:
            kw_url = "https://plant.id/api/v3/health_assessment?details=local_name,description,url,treatment,classification,common_names,cause"
            response = requests.post(
                kw_url,
                headers={"Api-Key": KINDWISE_API_KEY},
                files={"images": ("health.jpg", processed_bytes, "image/jpeg")},
                timeout=25
            )
            if response.status_code in (200, 201):
                kw_data = response.json().get("result", {})
                kw_evaluated = True
            elif response.status_code == 429:
                print("Kindwise API 429 Quota Exceeded. Failing over to Gemini Vision.")
        except Exception as e:
            print("Kindwise API request error:", e)

    # 5. Call Google Gemini AI Vision (image understanding)
    gemini_data = None
    if GEMINI_API_KEY:
        try:
            gemini_data = gemini_analyze_plant_health(
                processed_bytes,
                mime_type="image/jpeg",
                plant_name=identified_plant_name or ""
            )
        except Exception as e:
            print("Gemini Health Analysis non-blocking error:", e)

    # -------------------------------------------------------------
    # 6. Synergistic Evaluation & Conflict Resolution
    # -------------------------------------------------------------
    # If Gemini explicitly flagged image as uncertain or lacking clarity:
    if gemini_data and gemini_data.get("is_uncertain"):
        unc_note = gemini_data.get("uncertainty_note") or "The image lacks diagnostic clarity. Please upload a sharper close-up photograph in natural daylight."
        return {
            "success": False,
            "status": "uncertain",
            "message": unc_note,
            "data": {
                "plant_name": identified_plant_name,
                "is_healthy": False,
                "health_status": "uncertain",
                "condition": None,
                "confidence": None,
                "confidence_percent": None,
                "confidence_description": None,
                "severity": "Visible-leaf severity uncertain (Ambiguous image features)",
                "observation": gemini_data.get("evidence_from_image") or "Visual diagnostic features are ambiguous or insufficiently resolved on this leaf image.",
                "symptoms": gemini_data.get("visible_observations") or ["Indeterminate foliar texture"],
                "causes": gemini_data.get("possible_causes") or ["Inconclusive visual diagnostic evidence from single photograph"],
                "diagnostic_checks": _build_diagnostic_checks(),
                "why_occurred": unc_note,
                "immediate_treatments": [
                    "Check soil moisture 2 to 3 inches deep before watering.",
                    "Inspect leaf undersides with a magnifying lens for pest presence."
                ],
                "future_precautions": ["Monitor leaf growth for new discoloration."],
                "prevention": ["Maintain consistent watering and adequate container drainage."],
                "secondary_conditions": [],
                "yellow_leaf_analysis": _build_yellow_leaf_investigation() if visual_stats["has_chlorosis"] else None,
                "gemini_insights": None,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }
        }

    gemini_reports_disease = bool(
        gemini_data and
        gemini_data.get("is_healthy") is False and
        gemini_data.get("health_status") == "possible_disease"
    )
    has_chromatic_symptoms = visual_stats["has_chlorosis"] or visual_stats["has_lesions"]

    # CASE A: Kindwise evaluated the plant
    if kw_evaluated and kw_data:
        is_healthy_obj = kw_data.get("is_healthy", {})
        is_healthy_binary = bool(is_healthy_obj.get("binary", True))
        healthy_probability = float(is_healthy_obj.get("probability", 1.0))
        disease_sugs = kw_data.get("disease", {}).get("suggestions", [])

        # SAFEGUARD: Do not classify a leaf as healthy if disease symptoms are visible!
        is_truly_healthy = (
            is_healthy_binary and
            healthy_probability >= 0.50 and
            not gemini_reports_disease and
            not has_chromatic_symptoms
        )

        if is_truly_healthy:
            conf_val = round(healthy_probability, 3) if healthy_probability > 0 else None
            conf_pct = round(healthy_probability * 100, 1) if healthy_probability > 0 else None

            gemini_insights = None
            if gemini_data:
                gemini_insights = {
                    "confirmed_observations": gemini_data.get("visible_observations", ["Uniform green chlorophyll"]),
                    "evidence_from_image": gemini_data.get("evidence_from_image", "Foliage exhibits balanced green density."),
                    "specialist_recovery_plan": _filter_safe_treatments(gemini_data.get("immediate_treatments", ["Maintain current watering routine."])),
                    "botanical_prognosis": "Foliage in prime physiological health with no pathogen activity."
                }

            result_data = {
                "plant_name": identified_plant_name,
                "is_healthy": True,
                "health_status": "healthy",
                "condition": None,
                "confidence": conf_val,
                "confidence_percent": conf_pct,
                "confidence_description": "Classifier health pattern score (represents healthy foliar feature match; does not represent clinical diagnostic accuracy)",
                "severity": "None (Healthy Foliage)",
                "observation": f"Sampled leaf exhibits uniform chlorophyll coloration ({visual_stats['green_pct']}% green density) with no active foliar lesions detected.",
                "symptoms": ["Uniform green chlorophyll pigmentation", "No necrotic spots or systemic lesions"],
                "causes": ["Optimal natural lighting, balanced watering, and healthy root development"],
                "diagnostic_checks": [],
                "why_occurred": _derive_why_occurred("", is_healthy=True),
                "immediate_treatments": [
                    "Check soil moisture depth before watering; water when topsoil feels dry.",
                    "Keep foliage in bright, indirect natural sunlight."
                ],
                "future_precautions": [
                    "Inspect leaf undersides periodically for early pest presence.",
                    "Avoid overhead watering; keep foliage dry at night."
                ],
                "prevention": [
                    "Ensure potting container has bottom drainage holes.",
                    "Wipe dust off foliage periodically to promote maximum photosynthesis."
                ],
                "secondary_conditions": [],
                "yellow_leaf_analysis": None,
                "gemini_insights": gemini_insights,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }

            return {
                "success": True,
                "status": "analyzed",
                "message": "The plant appears healthy with no critical disease detected.",
                "data": result_data
            }

        else:
            # Condition detected (or override from false-healthy)
            if not is_healthy_binary and disease_sugs:
                top_sug = disease_sugs[0]
                raw_name = top_sug.get("name", "Foliar Stress")
                top_name = _cautious_condition_name(raw_name)
                top_prob = float(top_sug.get("probability", 0.0))
                details = top_sug.get("details", {}) or {}
                cond_conf_val = round(top_prob, 3) if top_prob > 0 else None
                cond_conf_pct = round(top_prob * 100, 1) if top_prob > 0 else None

                # Secondary conditions ONLY if original model response explicitly provided them
                secondary_conditions = []
                for s in disease_sugs[1:4]:
                    s_prob = float(s.get("probability", 0.0))
                    if s_prob >= 0.08:
                        s_details = s.get("details", {}) or {}
                        secondary_conditions.append({
                            "name": s.get("name"),
                            "confidence": round(s_prob, 3),
                            "confidence_percent": round(s_prob * 100, 1),
                            "description": "Secondary model pattern suggestion from classifier (not verified concurrent diagnosis)"
                        })

                treatments_obj = details.get("treatment", {}) or {}
                bio_treats = treatments_obj.get("biological", []) or []
                chem_treats = treatments_obj.get("chemical", []) or []
                prev_treats = treatments_obj.get("prevention", []) or []

                raw_treatments = []
                if bio_treats:
                    raw_treatments.extend([b for b in bio_treats[:2]])
                if chem_treats:
                    raw_treatments.extend([c for c in chem_treats[:1]])
                
                # Filter out aggressive repotting, fertilizer, manure, or root trimming
                filtered_treats = _filter_safe_treatments(raw_treatments)

                immediate_treatments = [
                    "Check soil moisture 2 to 3 inches deep before watering; allow damp soil to dry.",
                    "Inspect leaf undersides and petiole junctions with magnification for pests."
                ]
                if filtered_treats:
                    immediate_treatments.extend(filtered_treats[:2])
                immediate_treatments.append(SAFE_NEEM_GUIDANCE)

                future_precautions = [
                    "Water strictly at the soil base in the morning; avoid wetting foliage.",
                    "Ensure adequate container drainage and airflow around the plant canopy."
                ]
                prevention_list = _filter_safe_treatments(prev_treats) if prev_treats else [
                    "Maintain well-draining soil to prevent root waterlogging.",
                    "Disinfect pruning shears between plants to avoid pathogen transmission."
                ]
            else:
                # Kindwise did not have disease suggestion, but Gemini or chromatic analysis found symptoms
                gem_cond = gemini_data.get("primary_condition") if gemini_data else None
                raw_name = gem_cond or ("Foliar Chlorosis (Leaf Yellowing)" if visual_stats["has_chlorosis"] else "Foliar Stress")
                top_name = _cautious_condition_name(raw_name)
                cond_conf_val = None
                cond_conf_pct = None
                secondary_conditions = []
                
                gem_treatments = gemini_data.get("immediate_treatments", []) if gemini_data else []
                safe_gem_treatments = _filter_safe_treatments(gem_treatments)

                immediate_treatments = [
                    "Check soil moisture depth with a finger or meter before watering; allow damp soil to aerate.",
                    "Inspect leaf undersides with a magnifier for spider mites or scale insects."
                ]
                if safe_gem_treatments:
                    immediate_treatments.extend(safe_gem_treatments[:2])
                immediate_treatments.append(SAFE_NEEM_GUIDANCE)

                future_precautions = [
                    "Monitor newly emerging foliage for uniform green chlorophyll."
                ]
                prevention_list = [
                    "Ensure pot has clear bottom drainage and avoid prolonged standing water."
                ]

            # Severity estimation strictly for visible leaf symptoms
            severity_str = _derive_severity(visual_stats["damage_ratio"])

            # Symptoms & Causes synthesis
            symptoms_list = []
            if gemini_data and gemini_data.get("visible_observations"):
                symptoms_list.extend(gemini_data["visible_observations"])
            if visual_stats["has_chlorosis"] and not any("yellow" in s.lower() or "chlorosis" in s.lower() for s in symptoms_list):
                symptoms_list.append(f"Chlorotic yellowing observed across {visual_stats['yellow_pct']}% of sampled leaf surface.")
            if visual_stats["has_lesions"] and not any("spot" in s.lower() or "lesion" in s.lower() for s in symptoms_list):
                symptoms_list.append(f"Necrotic lesions/spots observed across {visual_stats['brown_pct']}% of sampled leaf surface.")
            if not symptoms_list:
                symptoms_list = [f"Visible manifestations characteristic of {top_name} on sampled leaf."]

            causes_list = []
            if gemini_data and gemini_data.get("possible_causes"):
                causes_list.extend(gemini_data["possible_causes"])
            if not causes_list:
                causes_list = [f"Potential environmental, moisture, or pathological factors associated with {top_name}."]

            is_yellow_issue = (
                any(k in top_name.lower() for k in ["nutrient", "deficiency", "water excess", "senescence", "yellow", "chlorosis"]) or
                visual_stats["has_chlorosis"] or
                any("yellow" in s.lower() for s in symptoms_list)
            )
            yellow_leaf_analysis = _build_yellow_leaf_investigation() if is_yellow_issue else None
            why_occurred_str = _derive_why_occurred(top_name, is_healthy=False)

            # Build Gemini insights block with cautious non-definitive prognosis
            gemini_insights = None
            if gemini_data:
                gemini_insights = {
                    "confirmed_observations": gemini_data.get("visible_observations", []),
                    "possible_causes": gemini_data.get("possible_causes", []),
                    "evidence_from_image": gemini_data.get("evidence_from_image", ""),
                    "specialist_recovery_plan": _filter_safe_treatments(gemini_data.get("immediate_treatments", [])),
                    "botanical_prognosis": "Prognosis: Dependent on verifying underlying cultural or environmental factors; physical diagnostic checks offer the best guidance."
                }

            result_data = {
                "plant_name": identified_plant_name,
                "is_healthy": False,
                "health_status": "possible_disease",
                "condition": top_name,
                "confidence": cond_conf_val,
                "confidence_percent": cond_conf_pct,
                "confidence_description": "Classifier feature similarity score (represents visual pattern match probability; does not indicate clinical diagnostic accuracy)",
                "severity": severity_str,
                "observation": (gemini_data.get("evidence_from_image") if gemini_data else None) or f"Visible foliar symptoms consistent with {top_name} detected on sampled leaf.",
                "symptoms": symptoms_list,
                "causes": causes_list,
                "diagnostic_checks": _build_diagnostic_checks(top_name, visual_stats["has_chlorosis"], visual_stats["has_lesions"]),
                "why_occurred": why_occurred_str,
                "immediate_treatments": immediate_treatments,
                "future_precautions": future_precautions,
                "prevention": prevention_list,
                "secondary_conditions": secondary_conditions,
                "yellow_leaf_analysis": yellow_leaf_analysis,
                "gemini_insights": gemini_insights,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }

            return {
                "success": True,
                "status": "analyzed",
                "message": f"Possible condition detected: {top_name}.",
                "data": result_data
            }

    # CASE B: Kindwise unavailable (Quota 429, network, etc.) -> Use Gemini Vision directly!
    if gemini_data:
        is_gem_healthy = bool(gemini_data.get("is_healthy", False)) and not has_chromatic_symptoms
        raw_name = gemini_data.get("primary_condition") or ("Healthy Foliage" if is_gem_healthy else "Foliar Stress")
        top_name = None if is_gem_healthy else _cautious_condition_name(raw_name)
        health_status = "healthy" if is_gem_healthy else "possible_disease"

        severity_str = "None (Healthy Foliage)" if is_gem_healthy else _derive_severity(visual_stats["damage_ratio"])

        symptoms_list = gemini_data.get("visible_observations") or (
            ["Uniform green chlorophyll"] if is_gem_healthy else ["Visible foliar discoloration"]
        )
        causes_list = gemini_data.get("possible_causes") or (
            ["Proper lighting and balanced moisture"] if is_gem_healthy else ["Cultural or environmental factors"]
        )

        is_yellow_issue = (
            any(k in raw_name.lower() for k in ["nutrient", "deficiency", "water excess", "senescence", "yellow", "chlorosis"]) or
            visual_stats["has_chlorosis"] or
            any("yellow" in s.lower() for s in symptoms_list)
        )

        gemini_insights = {
            "confirmed_observations": gemini_data.get("visible_observations", []),
            "possible_causes": gemini_data.get("possible_causes", []),
            "evidence_from_image": gemini_data.get("evidence_from_image", ""),
            "specialist_recovery_plan": _filter_safe_treatments(gemini_data.get("immediate_treatments", [])),
            "botanical_prognosis": "Prognosis: Dependent on verifying underlying cultural or environmental factors; physical diagnostic checks offer the best guidance."
        }

        result_data = {
            "plant_name": identified_plant_name,
            "is_healthy": is_gem_healthy,
            "health_status": health_status,
            "condition": top_name,
            "confidence": None,
            "confidence_percent": None,
            "confidence_description": None,
            "severity": severity_str,
            "observation": gemini_data.get("evidence_from_image") or ("Foliage structure appears healthy." if is_gem_healthy else f"Symptoms consistent with {top_name} on sampled leaf."),
            "symptoms": symptoms_list,
            "causes": causes_list,
            "diagnostic_checks": [] if is_gem_healthy else _build_diagnostic_checks(raw_name, visual_stats["has_chlorosis"], visual_stats["has_lesions"]),
            "why_occurred": _derive_why_occurred(raw_name, is_healthy=is_gem_healthy),
            "immediate_treatments": [
                "Check soil moisture depth with a finger or meter before watering; allow damp soil to dry.",
                "Inspect leaf undersides with a magnifier for spider mites or scale insects.",
                SAFE_NEEM_GUIDANCE
            ],
            "future_precautions": ["Monitor new foliage for consistent green color."],
            "prevention": ["Ensure pot has bottom drainage holes."],
            "secondary_conditions": [],
            "yellow_leaf_analysis": _build_yellow_leaf_investigation() if is_yellow_issue else None,
            "gemini_insights": gemini_insights,
            "disclaimer": DISCLAIMER_TEXT,
            "quality_warning": quality_warning
        }

        return {
            "success": True,
            "status": "analyzed",
            "message": "The plant appears healthy with no critical disease detected." if is_gem_healthy else f"Possible condition detected: {top_name}.",
            "data": result_data
        }

    # CASE C: Third Safety Net (Local chromatic heuristics if both APIs are unavailable)
    if visual_stats["has_chlorosis"] or visual_stats["has_lesions"]:
        if visual_stats["has_lesions"]:
            raw_cond = "Foliar Leaf Spot / Necrotic Lesions"
        else:
            raw_cond = "Foliar Chlorosis (Leaf Yellowing)"
        cond_name = _cautious_condition_name(raw_cond)
        severity_str = _derive_severity(visual_stats["damage_ratio"])

        return {
            "success": True,
            "status": "analyzed",
            "message": f"Visual foliar analysis completed: {cond_name} detected.",
            "data": {
                "plant_name": identified_plant_name,
                "is_healthy": False,
                "health_status": "possible_disease",
                "condition": cond_name,
                "confidence": None,
                "confidence_percent": None,
                "confidence_description": None,
                "severity": severity_str,
                "observation": f"Chromatic pattern analysis detected foliar discoloration across {round(visual_stats['damage_ratio'] * 100, 1)}% of sampled leaf surface.",
                "symptoms": [f"Visible discoloration consistent with {cond_name}"],
                "causes": ["Possible contributing factors include watering imbalance, root aeration restrictions, or foliar stress requiring physical verification"],
                "diagnostic_checks": _build_diagnostic_checks(raw_cond, visual_stats["has_chlorosis"], visual_stats["has_lesions"]),
                "why_occurred": _derive_why_occurred(raw_cond, is_healthy=False),
                "immediate_treatments": [
                    "Check soil moisture depth with a finger or meter before watering; allow damp soil to dry.",
                    "Inspect leaf undersides with a magnifier for pests.",
                    SAFE_NEEM_GUIDANCE
                ],
                "future_precautions": [
                    "Water strictly at the root base; keep foliage dry.",
                    "Ensure adequate ambient airflow around the pot."
                ],
                "prevention": [
                    "Ensure container has functional drainage holes."
                ],
                "secondary_conditions": [],
                "yellow_leaf_analysis": _build_yellow_leaf_investigation() if visual_stats["has_chlorosis"] else None,
                "gemini_insights": None,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }
        }
    elif visual_stats["green_pct"] >= 65.0 and visual_stats["damage_ratio"] < 0.05:
        return {
            "success": True,
            "status": "analyzed",
            "message": "The plant appears healthy with uniform chlorophyll coloration.",
            "data": {
                "plant_name": identified_plant_name,
                "is_healthy": True,
                "health_status": "healthy",
                "condition": None,
                "confidence": None,
                "confidence_percent": None,
                "confidence_description": None,
                "severity": "None (Healthy Foliage)",
                "observation": f"Uniform chlorophyll density ({visual_stats['green_pct']}% green) without visible necrotic lesions on sampled leaf.",
                "symptoms": ["Uniform green foliage", "No critical lesions detected"],
                "causes": ["Proper lighting and balanced moisture"],
                "diagnostic_checks": [],
                "why_occurred": _derive_why_occurred("", is_healthy=True),
                "immediate_treatments": ["Maintain current care regimen and check soil moisture before watering."],
                "future_precautions": ["Periodically inspect leaf undersides for pests."],
                "prevention": ["Ensure pot has bottom drainage."],
                "secondary_conditions": [],
                "yellow_leaf_analysis": None,
                "gemini_insights": None,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }
        }
    else:
        return {
            "success": False,
            "status": "uncertain",
            "message": "The available image is insufficient for a reliable conclusion. Please upload a clearer close-up photograph showing the affected leaf in bright natural light.",
            "data": {
                "plant_name": identified_plant_name,
                "is_healthy": False,
                "health_status": "uncertain",
                "condition": None,
                "confidence": None,
                "confidence_percent": None,
                "confidence_description": None,
                "severity": "Visible-leaf severity uncertain (Ambiguous image features)",
                "observation": "Image lacks distinct diagnostic features to confirm disease or healthy status.",
                "symptoms": ["Indeterminate foliar patterns"],
                "causes": ["Inconclusive visual diagnostic evidence from single photograph"],
                "diagnostic_checks": _build_diagnostic_checks(),
                "why_occurred": "Low contrast or ambiguous coloration prevents reliable automated pathology classification.",
                "immediate_treatments": [
                    "Inspect soil moisture depth and check foliage under natural daylight.",
                    "Examine leaf undersides for pests."
                ],
                "future_precautions": ["Monitor leaf growth for new discoloration."],
                "prevention": ["Maintain good airflow and well-draining soil."],
                "secondary_conditions": [],
                "yellow_leaf_analysis": None,
                "gemini_insights": None,
                "disclaimer": DISCLAIMER_TEXT,
                "quality_warning": quality_warning
            }
        }
