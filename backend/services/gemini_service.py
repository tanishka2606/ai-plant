import os
import io
import json
import base64
import requests
from PIL import Image
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Absolute path to backend/.env
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH, override=True)

def _get_api_key() -> Optional[str]:
    """Safe retrieval of Gemini API Key strictly from environment."""
    load_dotenv(DOTENV_PATH, override=True)
    return (os.getenv("GEMINI_API_KEY") or os.getenv("AI_API_KEY") or "").strip() or None

# Supported and verified model configuration:
# Primary: gemini-3.1-flash-lite (fast, multimodal, verified active)
# Fallback: gemini-flash-latest (backup model)
MODELS = ["gemini-3.1-flash-lite", "gemini-flash-latest"]

DISCLAIMER_TEXT = "This result is an AI-assisted botanical assessment and should not be treated as a definitive professional or scientific diagnosis."

def _optimize_image_for_gemini(image_bytes: bytes, max_dim: int = 512) -> bytes:
    """
    Compresses image to ~25-40KB JPEG to guarantee fast uploads (<0.2s)
    and eliminate network timeouts while retaining sharp diagnostic detail.
    """
    try:
        im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        im.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82)
        return buf.getvalue()
    except Exception:
        return image_bytes

def _call_gemini_api(payload: Dict[str, Any], timeout: int = 22) -> Optional[Dict[str, Any]]:
    """
    Sends request to Gemini REST API across verified models with single attempt per model.
    Avoids duplicate or excessive retries to preserve API credits.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return {"model": model, "text": parts[0]["text"]}
            elif resp.status_code in (404, 503, 429):
                continue
            else:
                continue
        except requests.exceptions.RequestException:
            continue

    return None

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON object from Gemini response text."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2:
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        import re
        m = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None

# =====================================================================
# 1. PLANT HEALTH & DISEASE DETECTION
# =====================================================================
def analyze_plant_health(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    plant_name: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Analyzes leaf / plant images using Gemini multimodal vision.
    Strictly distinguishes confirmed visual observations from possible causes.
    Never invents disease names or fake confidence numbers.
    Does NOT classify a leaf as healthy simply because no specific disease is detected.
    """
    if not image_bytes or len(image_bytes) == 0:
        return None

    opt_bytes = _optimize_image_for_gemini(image_bytes)
    b64_image = base64.b64encode(opt_bytes).decode("utf-8")
    plant_context = f"Identified/Suspected Plant: {plant_name}. " if plant_name else ""

    prompt = (
        f"You are an expert plant pathologist and botanical specialist. {plant_context}\n"
        "Examine this leaf/plant image carefully.\n"
        "Follow these strict rules:\n"
        "1. Identify strictly VISIBLE SYMPTOMS observed directly in the image (e.g. yellowing, chlorosis, brown necrotic spots, wilting, holes, white powdery film, lesions, dry margins).\n"
        "2. Do not mark a leaf as healthy simply because a specific named disease is absent. If yellowing, browning, or spots are visible, classify health_status as 'possible_disease'. Only classify as 'healthy' if the foliage is uniformly green, vibrant, and shows no physical distress.\n"
        "3. Provide POSSIBLE CAUSES (e.g. overwatering, nutrient deficiency such as nitrogen or iron, fungal leaf spot, underwatering, pest damage, natural aging).\n"
        "4. Clearly distinguish confirmed visual observations from possible causes.\n"
        "5. If the image is blurry, out-of-focus, or lacks diagnostic clarity, set is_uncertain to true and describe what is unclear in uncertainty_note.\n"
        "6. Provide practical, plant-safe immediate treatment and prevention recommendations.\n"
        "7. Never invent disease names or fake confidence scores.\n\n"
        "Respond with a valid JSON object containing keys: "
        "is_healthy (bool), health_status (string: 'healthy', 'possible_disease', or 'uncertain'), "
        "primary_condition (string), visible_observations (list of strings), possible_causes (list of strings), "
        "evidence_from_image (string), severity (string: 'None', 'Low', 'Moderate', 'Severe', or 'Indeterminate'), "
        "immediate_treatments (list of strings), future_precautions (list of strings), prevention (list of strings), "
        "is_uncertain (bool), uncertainty_note (string)."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    }

    result = _call_gemini_api(payload, timeout=22)
    if not result:
        return None

    parsed = _extract_json(result["text"])
    if not parsed:
        return None

    parsed["disclaimer"] = DISCLAIMER_TEXT
    parsed["gemini_model"] = result.get("model")
    return parsed

# =====================================================================
# 2. PLANT IDENTIFICATION
# =====================================================================
def identify_plant(
    image_bytes: bytes,
    mime_type: str = "image/jpeg"
) -> Optional[Dict[str, Any]]:
    """
    Identifies plant species from image, returning common name, scientific name,
    visible morphological features, and uncertainty notes when appropriate.
    """
    if not image_bytes or len(image_bytes) == 0:
        return None

    opt_bytes = _optimize_image_for_gemini(image_bytes)
    b64_image = base64.b64encode(opt_bytes).decode("utf-8")
    prompt = (
        "You are a botanical taxonomic system. Examine this plant specimen image.\n"
        "Return strictly a valid JSON object with keys:\n"
        "- common_name (string: popular English common name)\n"
        "- scientific_name (string: binomial botanical taxon Genus species)\n"
        "- genus (string: botanical genus)\n"
        "- family (string: botanical family)\n"
        "- identifying_features (list of 2-4 strings describing visible morphological traits like leaf margin, shape, venation, floral structure)\n"
        "- is_uncertain (bool: true if image is blurry or species cannot be determined definitively, else false)\n"
        "- uncertainty_note (string: note explaining uncertainty if applicable, else empty string)\n"
        "Do not fabricate species if visual evidence is ambiguous."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    }

    result = _call_gemini_api(payload, timeout=20)
    if not result:
        return None

    return _extract_json(result["text"])

# =====================================================================
# 3. SEED IDENTIFICATION
# =====================================================================
def identify_seed(
    image_bytes: bytes,
    mime_type: str = "image/jpeg"
) -> Optional[Dict[str, Any]]:
    """
    Identifies seeds from images with tailored morphological characteristics,
    germination guide, and growing instructions.
    """
    if not image_bytes or len(image_bytes) == 0:
        return None

    opt_bytes = _optimize_image_for_gemini(image_bytes, max_dim=768)
    b64_image = base64.b64encode(opt_bytes).decode("utf-8")
    prompt = (
        "You are an expert seed morphologist, seed botanist, and agricultural specialist.\n"
        "Inspect this seed/pit/grain/nut image carefully.\n\n"
        "CRITICAL RULES:\n"
        "1. Identify the seed species accurately from visible morphology (shape, size ratio, coat texture, color, hilum/scar).\n"
        "2. Analyze the seed itself (including woody endocarps/pits like mango, avocado, peach, as well as true seeds like tomato, apple, sunflower, melon). Do not confuse fruit background with the seed.\n"
        "3. Provide realistic, accurate SEED MORPHOLOGICAL CHARACTERISTICS in simple, clear English suitable for students and everyday gardeners:\n"
        "   - Describe the visible shape, approximate relative size, color, surface texture, and visible features based on the actual identified seed.\n"
        "   - NEVER claim a seed is a caryopsis or has a ventral groove unless it is genuinely a cereal grain (wheat, barley, oat). Describe only what is true for THIS identified seed.\n"
        "   - Never claim seed viability (germination potential) can be verified from appearance alone.\n"
        "4. Provide a tailored GERMINATION GUIDE specific to this identified seed species:\n"
        "   - preparation: Specific preparation for this seed. Only recommend soaking if appropriate; mark optional methods as optional (e.g., soaking sunflower seeds is optional; removing papaya sarcotesta or opening mango husks is species-specific). Never recommend husk removal or shell peeling for seeds that do not need it.\n"
        "   - germination_time: Approximate days or weeks required for sprouts to emerge under favorable conditions.\n"
        "   - conditions: Optimal moisture, temperature range, and media for germination.\n"
        "5. Provide practical, concise GROWING INSTRUCTIONS specific to this identified seed:\n"
        "   - soil: Suitable soil mix or growing medium (aeration, drainage, pH preferences).\n"
        "   - planting_depth: Specific depth and planting orientation (e.g., 2.5 cm / 1 inch for sunflower, 1 to 1.5 cm for papaya, 3 to 5 cm for mango).\n"
        "   - watering: Proper watering frequency and moisture levels.\n"
        "   - sunlight: Lighting requirements during sprouting and early seedling growth.\n"
        "   - transplanting: Clear guidance on when and how to transplant into a larger pot or garden (e.g., sunflowers prefer direct sowing due to sensitive taproots; papayas transplant at 15-20 cm).\n"
        "6. TEMPERATURE RULE: Express ALL temperatures strictly in Celsius (°C), e.g. '20°C to 25°C'. NEVER mention Fahrenheit (°F), not even in parentheses.\n"
        "7. CONCISENESS RULE: Use simple English. Keep each subsection strictly concise—preferably 1 to 2 short sentences per subsection. Do NOT write long paragraphs.\n"
        "8. If the image is blurry, out-of-focus, or visually ambiguous, set is_uncertain to true and describe what is unclear.\n\n"
        "Output strictly a JSON object with keys:\n"
        "- common_name (string: popular English name of the seed/plant)\n"
        "- scientific_name (string: botanical binomial name)\n"
        "- seed_morphology (string: plain-English description of shape, color, surface texture, and visible features)\n"
        "- germination_guide (object with keys: preparation, germination_time, conditions)\n"
        "- growing_instructions (object with keys: soil, planting_depth, watering, sunlight, transplanting)\n"
        "- is_uncertain (bool: true/false)\n"
        "- uncertainty_note (string: explanation if ambiguous, else empty string)"
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64_image}}
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    }

    result = _call_gemini_api(payload, timeout=25)
    if not result:
        return None

    return _extract_json(result["text"])

# =====================================================================
# 4. PLANT CARE RECOMMENDATIONS
# =====================================================================
def generate_plant_care(plant_name: str) -> Optional[Dict[str, Any]]:
    """
    Generates structured, practical plant care instructions for plants not present in MySQL.
    """
    if not plant_name or not plant_name.strip():
        return None

    prompt = (
        f"You are a master horticulturist. Provide accurate, reliable care instructions for '{plant_name}'.\n"
        "Output strictly a JSON object with keys:\n"
        "- plant_name (string: scientific botanical binomial)\n"
        "- common_name (string: popular English common name)\n"
        "- sunlight (string: sunlight intensity, direct vs indirect, recommended hours)\n"
        "- water (string: watering routine, frequency, and soil dryness test)\n"
        "- soil (string: soil type, texture, aeration, drainage, and pH preferences)\n"
        "- container (string: pot specifications, drainage requirements, root space)\n"
        "- location (string: ideal temperature range in Celsius, humidity, indoor/outdoor placement)\n"
        "- fertilizer (string: organic vs balanced fertilizer recommendation and feeding schedule)\n"
        "- care (string: essential maintenance, pruning, wiping foliage, survival tips)\n"
        "- common_problems_and_prevention (string: frequent issues like overwatering, pests, chlorosis and how to prevent them)"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
    }

    result = _call_gemini_api(payload, timeout=18)
    if not result:
        return None

    return _extract_json(result["text"])

# =====================================================================
# 5. AI PLANT ASSISTANT
# =====================================================================
def ask_plant_assistant(
    question: str,
    plant_name: str = "",
    care_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """
    Answers user questions with natural, empathetic, plant-specific care guidance.
    Uses simple, understandable language and provides clear, practical, step-by-step solutions.
    """
    if not question or not question.strip():
        return None

    p_str = f"Target Plant: {plant_name}\n" if plant_name else ""
    ctx_str = ""
    if care_context:
        ctx_parts = [f"{k.capitalize()}: {v}" for k, v in care_context.items() if v]
        if ctx_parts:
            ctx_str = "Verified Care Knowledge (from database):\n" + "\n".join(f"- {p}" for p in ctx_parts) + "\n\n"

    hist_str = ""
    if history and isinstance(history, list):
        recent = []
        for turn in history[-6:]:
            sender = "User" if turn.get("sender") == "user" or turn.get("role") == "user" else "PlantAI"
            text = (turn.get("text") or turn.get("content") or "").strip()
            if text:
                recent.append(f"{sender}: {text}")
        if recent:
            hist_str = "Recent Conversation History (for context and follow-ups):\n" + "\n".join(recent) + "\n\n"

    prompt = (
        "You are PlantAI, a calm, friendly, and practical plant-care expert.\n"
        "Your goal is to communicate naturally, understand the user's actual question, and provide helpful solutions in simple, everyday English.\n\n"
        f"{p_str}"
        f"{ctx_str}"
        f"{hist_str}"
        f"User Message: '{question.strip()}'\n\n"
        "STRICT GUIDELINES:\n"
        "1. SIMPLE AND NATURAL LANGUAGE:\n"
        "   - Use short, clear sentences and familiar, everyday words.\n"
        "   - Avoid complicated scientific terms, filler phrases, and lengthy paragraphs.\n"
        "   - When a technical term is necessary, explain it immediately in plain English (e.g. explain root rot as 'roots suffocating and rotting from too much trapped water').\n"
        "   - Sound like a friendly, calm person explaining something clearly. Avoid repetitive greetings, excessive enthusiasm (no hype or exclamation marks on every sentence), and unnecessary bot intros (e.g. do NOT say 'Hello! I am PlantAI...', 'I'd be thrilled to help!', or 'Oh no, your green friend is sad!'). Just provide the answer directly and warmly.\n\n"
        "2. UNDERSTAND THE USER'S ACTUAL QUESTION:\n"
        "   - Answer what the user specifically asked before adding any extra detail.\n"
        "   - Keep your response strictly focused on their question.\n"
        "   - Use previous messages to understand follow-up questions smoothly.\n"
        "   - CRITICAL: Do NOT repeat your complete previous answer when the user asks a follow-up. Answer only the new question directly without re-summarizing earlier turns.\n"
        "   - For simple questions (e.g. watering frequency, pet safety, light needs), give a concise answer in 2 to 4 clear sentences. Do NOT ask follow-up questions on simple questions.\n\n"
        "3. PRACTICAL PLANT-CARE SOLUTIONS FOR PROBLEMS:\n"
        "   - For problems such as yellow leaves, falling leaves, slow growth, pests, or diseases:\n"
        "     * Explain the main possible causes in simple words.\n"
        "     * DO NOT assume one cause without enough evidence. For example, yellow leaves can be caused by overwatering, underwatering, pests, or low light—explain how each presents.\n"
        "     * Tell the user what to check first to identify the real cause.\n"
        "     * Give clear, numbered steps to solve the problem.\n"
        "     * Explain what to avoid (e.g. do not fertilize a stressed plant; do not water on a fixed calendar schedule).\n"
        "     * Ask ONE relevant follow-up question at the end to help narrow down the cause.\n\n"
        "4. HONESTY AND SAFETY:\n"
        "   - Never invent diagnoses, fake facts, or API scores.\n"
        "   - Never claim to have seen a photo unless an image was actually provided.\n"
        "   - Recommend safe, gentle solutions first (adjusting water, checking soil, wiping leaves, mild soapy water or diluted neem oil for pests). Avoid harsh chemicals without good reason.\n"
        "   - State all temperatures in Celsius only (°C). Never use Fahrenheit."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3
        }
    }

    result = _call_gemini_api(payload, timeout=20)
    if not result:
        return None

    return result.get("text", "").strip()
