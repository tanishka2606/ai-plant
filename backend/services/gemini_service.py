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
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH, override=False)

def _get_api_key() -> Optional[str]:
    """Safe retrieval of Gemini API Key strictly from environment or .env without wiping process env."""
    def _read_env_val():
        for var_name in ["GEMINI_API_KEY", "AI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY", "GEMINI_KEY"]:
            val = (os.getenv(var_name) or "").strip()
            if val:
                return val
        return None

    key = _read_env_val()
    if key:
        return key
    for p in [DOTENV_PATH, os.path.join(BASE_DIR, "..", ".env"), ".env"]:
        if os.path.exists(p):
            load_dotenv(p, override=False)
            k = _read_env_val()
            if k:
                return k
    return None

# Supported and verified model configuration:
# Primary: gemini-3.1-flash-lite (fast, multimodal, verified active)
# Fallback: gemini-flash-latest (backup model)
MODELS = ["gemini-3.1-flash-lite"]

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
            if resp.status_code == 429:
                import time
                time.sleep(1.2)
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
        "- identifying_features (list of 2-3 short, simple everyday English bullet points describing visible traits that help identify this plant, e.g. 'It has five flat petals', 'Leaves are thick and shiny', 'A pale line runs through the center of each leaf'. Avoid complex botanical jargon.)\n"
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
        "8. If the image is blurry, out-of-focus, or does NOT clearly depict a seed/grain/pit/pod (for example if it depicts a whole leafy plant, flower, fruit without visible seeds, person, animal, or unrelated object), set is_uncertain to true and explain that in uncertainty_note.\n\n"
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
        "You are PlantAI, a knowledgeable, friendly, and practical plant-care expert and conversational assistant.\n"
        "Your goal is to communicate naturally, understand the user's actual question, and provide helpful, accurate answers.\n\n"
        f"{p_str}"
        f"{ctx_str}"
        f"{hist_str}"
        f"User Message: '{question.strip()}'\n\n"
        "STRICT GUIDELINES:\n"
        "1. UNDERSTAND AND ANSWER THE ACTUAL QUESTION ASKED FIRST:\n"
        "   - Always address what the user specifically asked before adding any extra context.\n"
        "   - CONVERSATIONAL & LANGUAGE QUESTIONS: If the user asks whether you speak a language (e.g. 'Can you speak Marathi?'), answer them directly and warmly in English and that language (e.g. 'Yes, I can speak Marathi! हो, मी मराठी बोलू शकतो. मी तुम्हाला तुमच्या वनस्पतींच्या काळजीबद्दल कशी मदत करू शकतो?'). If the user speaks to you in Marathi, Hindi, or any other language, converse with them naturally in that language. Do NOT return unrelated plant-care tips when asked conversational or language questions.\n"
        "   - GREETINGS & IDENTITY: If the user says hello or asks who you are, introduce yourself warmly as PlantAI without dumping unprompted plant-care guides.\n"
        "   - GENERAL BOTANY & CONCEPTS: If the user asks about a general concept (e.g. 'What is photosynthesis?'), explain it clearly in simple terms.\n"
        "   - CONVERSATION CONTINUITY: Use conversation history to understand follow-ups without repeating the previous answer.\n\n"
        "2. PLANT-SPECIFIC PRACTICAL GUIDANCE:\n"
        "   - When answering plant-care questions, tailor your advice specifically to the plant species mentioned.\n"
        "   - Never assume every plant has the same requirements (e.g., succulents and cacti need soil to dry completely, while ferns and calatheas need consistent moisture).\n"
        "   - For simple questions (watering frequency, sunlight needs, pet safety), provide a concise, direct answer in 2 to 4 clear sentences.\n\n"
        "3. PRACTICAL PLANT-CARE SOLUTIONS FOR PROBLEMS:\n"
        "   - For issues such as yellow leaves, wilting, pests, or slow growth:\n"
        "     * Explain the most likely causes clearly in simple words.\n"
        "     * Tell the user what to check first (e.g. soil moisture 5 cm deep, drainage holes, leaf undersides).\n"
        "     * Provide clear, numbered steps on what action to take and what to avoid (e.g. do not fertilize stressed plants).\n"
        "     * Ask at most ONE helpful follow-up question if needed to narrow down the problem.\n\n"
        "4. HONESTY AND SAFETY:\n"
        "   - State all temperatures strictly in Celsius (°C). Never use Fahrenheit.\n"
        "   - Recommend safe, gentle treatments first. Avoid harsh chemicals indoors without good reason."
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

# =====================================================================
# 6. BOTANICAL IMAGE AUTHENTICITY & SUBJECT VALIDATION
# =====================================================================
def validate_image_authenticity_and_subject(
    image_bytes: bytes,
    expected_subject: str = "plant"
) -> Optional[Dict[str, Any]]:
    """
    Validates uploaded images before identification:
    1. Checks subject validity: authentic living plant vs seed vs unrelated (person, animal, car, etc.)
    2. Detects AI-generated images, digital art, drawings, cartoons, or 3D renders.
    3. Handles uncertainty cautiously without declaring borderline authentic photos fake.
    4. Detects blurry or unidentifiable subjects.
    """
    if not image_bytes or len(image_bytes) == 0:
        return {
            "is_valid": False,
            "detected_subject": "empty",
            "subject_type": "none",
            "authenticity": "uncertain",
            "rejection_reason": "The uploaded image file is empty."
        }

    opt_bytes = _optimize_image_for_gemini(image_bytes, max_dim=512)
    b64_image = base64.b64encode(opt_bytes).decode("utf-8")

    prompt = f"""
You are an expert botanical image validation and authenticity assessment system.
The user uploaded an image for '{expected_subject}' identification (expected subject: {expected_subject}).

Analyze the image carefully for:
1. SUBJECT VALIDITY:
   - If expected_subject is 'plant': Does the image genuinely contain a real botanical plant, flower, leaf, foliage, stem, tree, or succulent? If it depicts a person, animal, vehicle, building, food dish, electronic device, furniture, or other unrelated objects, is_valid must be false.
   - If expected_subject is 'seed': Does the image genuinely contain botanical seeds, grains, pits, nuts, kernels, or seed pods? If it depicts a whole leafy plant without seeds, fruit without visible seeds, person, animal, artificial beads, pebbles, or unrelated objects, is_valid must be false.
2. AUTHENTICITY & IMAGE INTEGRITY:
   - Check if the image appears to be an authentic photograph taken by a camera.
   - Check if the image appears to be AI-generated (e.g. synthetic textures, unnatural digital smoothness, hallucinated morphology), a digital illustration, cartoon, sketch, drawing, screenshot, or heavily manipulated artwork.
   - CRITICAL RULE: Do NOT claim AI-generated detection is 100% accurate. If authenticity cannot be determined reliably, set authenticity to 'uncertain' and do NOT declare it fake unless clear signs of illustration, cartoon, or generative artifacts exist.
3. SUITABILITY:
   - Check if the image is extremely blurry, out-of-focus, or lacks the actual subject needed for identification.

Return strictly a valid JSON object with keys:
- is_valid (bool: true ONLY if it is an authentic photo containing the expected subject)
- detected_subject (string: short description of what is in the image, e.g. 'cactus plant', 'cartoon car drawing', 'human face')
- subject_type (string: 'plant' | 'seed' | 'animal' | 'person' | 'vehicle' | 'object' | 'drawing' | 'other')
- authenticity (string: 'authentic_photo' | 'likely_ai_generated' | 'digital_art_or_drawing' | 'uncertain')
- is_blurry (bool: true if too blurry to identify, else false)
- rejection_reason (string: clear, polite user-facing error message if is_valid is false, otherwise empty string).
  Example rejection reasons:
  - If unrelated to plant: "This image does not appear to contain a valid plant. Please upload a clear plant photograph."
  - If unrelated to seed: "This image does not appear to contain a seed. Please upload a clear seed photograph."
  - If AI-generated or digital art/drawing: "This image may be digitally generated, illustrated, or manipulated. Please upload an original photograph."
  - If blurry: "The image is too blurry or out-of-focus to distinguish botanical features. Please upload a sharper photo."
"""

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

    result = _call_gemini_api(payload, timeout=18)
    if not result:
        return None

    return _extract_json(result["text"])

# =====================================================================
# 7. PLANT & SEED USES AND BENEFITS GENERATION
# =====================================================================
def generate_uses_and_benefits(
    name: str,
    scientific_name: str,
    item_type: str = "plant"
) -> Optional[Dict[str, Any]]:
    """
    Generates short, simple, everyday English uses and benefits for an identified plant or seed.
    Strictly omits undocumented or unverified categories. Never invents medicinal claims.
    """
    if not name and not scientific_name:
        return None

    if item_type == "plant":
        prompt = f"""
Provide simple, short, easy-to-understand uses and benefits for the plant '{name}' (scientific name: '{scientific_name}').

STRICT RULES:
1. Use simple everyday English and short sentences (under 15 words each).
2. Avoid lengthy explanations and complicated botanical or medical jargon.
3. Show only 1-2 useful bullet points per category.
4. Only include categories with reliable information. If a plant has no scientifically supported health benefits (or is toxic/inedible), omit health_benefits completely (set to empty list []).
5. Do NOT return placeholders like 'None' or 'No benefits available'.

Return strictly a valid JSON object with keys:
- common_uses: list of 1-2 short strings (e.g. 'Grown in gardens for its beautiful flowers.')
- health_benefits: list of 1-2 short strings (ONLY if scientifically supported, e.g. 'Contains compounds used in certain medicines.'; otherwise empty [])
- environmental_benefits: list of 1-2 short strings (e.g. 'Its flowers provide nectar for butterflies.')
- practical_uses: list of 1-2 short strings (e.g. 'Needs very little water and thrives in warm spots.')
"""
    else:
        prompt = f"""
Provide simple, short, easy-to-understand uses and benefits for the seed of '{name}' (scientific name: '{scientific_name}').

STRICT RULES:
1. Use simple everyday English and short sentences (under 15 words each).
2. Avoid complicated terminology or lengthy paragraphs.
3. Show only 1-2 useful bullet points per category.
4. Do NOT add identification confidence or match scores.
5. If the seed is inedible or lacks established nutritional value, set nutritional_benefits to empty [].
6. If a category is not supported, set it to empty []. Do NOT return 'None'.

Return strictly a valid JSON object with keys:
- common_uses: list of 1-2 short strings (e.g. 'Eaten raw or roasted as a crunchy snack.')
- nutritional_benefits: list of 1-2 short strings (e.g. 'Rich in Vitamin E and healthy fats.')
- health_benefits: list of 1-2 short strings (e.g. 'Healthy fats support heart wellness.')
- environmental_benefits: list of 1-2 short strings (e.g. 'Sunflower plants attract pollinating bees.')
- practical_uses: list of 1-2 short strings (e.g. 'Can be sprouted for fresh microgreens.')
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json"
        }
    }

    result = _call_gemini_api(payload, timeout=22)
    if not result:
        return None

    return _extract_json(result["text"])

