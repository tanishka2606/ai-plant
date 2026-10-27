import re
import os
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models import PlantCare

COMMON_PLANTS = [
    "snake plant", "peace lily", "monstera", "pothos", "spider plant",
    "money plant", "zz plant", "aloe vera", "jade plant", "rubber plant",
    "fiddle leaf fig", "tulsi", "holy basil", "neem", "rose", "hibiscus",
    "tulip", "lavender", "tomato", "basil", "mint", "cactus", "succulent",
    "boston fern", "calathea", "philodendron", "orchid", "begonia", "dracaena",
    "dieffenbachia", "peperomia", "sansevieria", "areca palm", "anthurium",
    "marigold", "jasmine", "curry leaf", "bamboo", "croton"
]

SPECIES_PROFILES = {
    "snake plant": {
        "water": "Snake plants store water in their thick leaves. Water only when the potting soil is 100% bone-dry from top to bottom (usually every 2 to 4 weeks in warm months, and once every 6 weeks in winter). Always empty the drainage saucer.",
        "sunlight": "Snake plants are very adaptable. They thrive in bright indirect sunlight, but also tolerate low-light rooms and north-facing windows well without losing color.",
        "soil": "Use a gritty, fast-draining cactus and succulent mix with added perlite or coarse sand in a container with drainage holes.",
        "general": "Snake plants (Sansevieria) are virtually indestructible. They thrive on neglect, require very little water, tolerate low light, and purify indoor air. The #1 danger is overwatering."
    },
    "cactus": {
        "water": "Cacti are desert plants that need the 'soak and dry' method. Water thoroughly until liquid runs out the bottom drainage holes, then wait until the soil is completely dry before watering again (every 3 to 4 weeks in summer; once every 6 to 8 weeks in winter).",
        "sunlight": "Cacti require full direct sunlight (at least 4 to 6 hours daily) on a south- or west-facing windowsill. Low light causes weak, stretched growth.",
        "soil": "Use an airy, gritty cactus mix with pumice, perlite, and coarse sand. Dense garden soil or heavy potting mix will cause root rot.",
        "general": "Cacti love bright direct sunlight, warm room temperatures (18°C to 28°C), and very infrequent watering. Always ensure the pot has drainage holes."
    },
    "monstera": {
        "water": "Water your Monstera when the top 5 cm of soil feels dry to the touch (typically once every 7 to 10 days). Pour evenly until water drains out the bottom holes.",
        "sunlight": "Monsteras thrive in bright, indirect sunlight. Direct hot sun will scorch their leaves, while too little light prevents leaves from developing fenestrations (splits).",
        "soil": "Use a chunky, well-aerated aroid potting mix containing coco coir, perlite, and orchid bark.",
        "general": "Monstera deliciosa thrives in bright indirect light, moderate humidity (50%+), and warm room temperatures (18°C to 28°C). Wipe large leaves with a damp cloth monthly to remove dust."
    },
    "peace lily": {
        "water": "Keep the soil lightly moist but not soggy. Peace lilies will visibly droop when thirsty and recover quickly once watered. Use room-temperature filtered water if possible.",
        "sunlight": "Peace lilies thrive in low to medium indirect light. Harsh direct sunlight scorches and bleaches their leaves.",
        "soil": "A rich, well-draining potting soil with peat moss and perlite that retains light moisture while draining freely.",
        "general": "Peace lilies (Spathiphyllum) prefer warm temperatures (18°C to 26°C) and higher humidity. Note: peace lilies are mildly toxic to pets if chewed."
    },
    "spider plant": {
        "water": "Water when the top 3 to 5 cm of soil feels dry. They are moderately drought-tolerant. Use tap water left out overnight to prevent brown leaf tips caused by fluoride.",
        "sunlight": "Bright, indirect light encourages rapid growth and producing baby 'spiderettes'. Avoid direct midday sun.",
        "soil": "Standard well-draining houseplant potting mix with perlite.",
        "general": "Spider plants (Chlorophytum comosum) are extremely resilient, easy to grow, and 100% non-toxic and pet-safe for cats and dogs."
    },
    "pothos": {
        "water": "Water whenever the top 5 cm of soil feels dry. Pothos leaves will droop slightly when thirsty, making it easy to know when to water. Yellow leaves indicate overwatering.",
        "sunlight": "Very forgiving; thrives in medium to bright indirect light and tolerates low light or fluorescent office lighting.",
        "soil": "Standard well-draining indoor potting mix in a pot with drainage holes.",
        "general": "Pothos (Epipremnum aureum / Money plant) is one of the easiest trailing houseplants to care for. It purifies indoor air and propagates easily in water."
    },
    "aloe vera": {
        "water": "Water deeply but infrequently—only when the soil is completely bone dry (every 3 to 4 weeks). Overwatering causes mushy, brown leaves.",
        "sunlight": "Needs at least 4 to 6 hours of bright, direct sunlight daily on a sunny windowsill.",
        "soil": "Fast-draining cactus and succulent mix with perlite or pumice.",
        "general": "Aloe vera is a drought-hardy medicinal succulent that loves bright sun, warm temperatures (15°C to 27°C), and well-draining soil."
    },
    "rose": {
        "water": "Roses need deep watering at the soil base 2 to 3 times a week (about 2.5 cm of water weekly). Never wet the foliage to avoid black spot and powdery mildew.",
        "sunlight": "Full direct sun (at least 6 hours of direct sunlight every day) is required for vigorous blooms.",
        "soil": "Rich, loamy, well-drained soil with a pH of 6.0 to 6.5, enriched with organic compost.",
        "general": "Roses thrive in full sun and well-drained soil. Feed monthly during the blooming season with a balanced rose fertilizer, and prune dead canes in late winter."
    },
    "tulsi": {
        "water": "Keep soil evenly moist. In hot summers, water daily; in cooler seasons, water when the top 2 cm feels dry.",
        "sunlight": "Full direct sunlight (at least 4 to 6 hours daily) keeps Tulsi bushy and fragrant.",
        "soil": "Fertile, loamy, well-drained potting soil enriched with organic compost.",
        "general": "Holy Basil (Tulsi) is a revered herb that loves warm weather and abundant sun. Pinch off flowering tips regularly to encourage dense, bushy leaf growth."
    },
    "zz plant": {
        "water": "Water only when the soil is completely dry from top to bottom (every 3 to 4 weeks). Its underground tubers store plenty of water.",
        "sunlight": "Thrives in low, medium, or bright indirect light. Avoid harsh direct sun.",
        "soil": "Well-draining houseplant mix with added perlite.",
        "general": "ZZ Plant (Zamioculcas zamiifolia) is nearly indestructible and thrives in offices or rooms with low light. The only way to harm it is by overwatering."
    }
}

def is_conversational_or_language_query(q_lower: str) -> bool:
    """
    Identifies whether the question is conversational, asking about a language,
    greeting, or general identity question rather than a plant-care diagnostic request.
    """
    patterns = [
        r"\bmarathi\b", r"\bhindi\b", r"\blanguage\b", r"\blanguages\b",
        r"\bमराठी\b", r"\bहिंदी\b", r"\bbol\b", r"\bspeak\b",
        r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bgood morning\b", r"\bgood evening\b", r"\bgood afternoon\b",
        r"\bnamaste\b", r"\bnamaskar\b",
        r"\bwho are you\b", r"\bwhat are you\b", r"\bwhat can you do\b", r"\bhow are you\b",
        r"\bthank\b", r"\bthanks\b", r"\bdhanyawad\b", r"\bshukriya\b"
    ]
    return any(re.search(pat, q_lower) for pat in patterns)

def _extract_plant_name(question: str, history: Optional[List[Dict[str, Any]]], db: Optional[Session]) -> str:
    """
    Infers the plant species from the question or recent conversation history.
    Searches both common houseplant names and the MySQL PlantCare database.
    """
    q_lower = (question or "").lower()

    # 1. Search in current question against common plant list
    for p in COMMON_PLANTS:
        if re.search(rf"\b{re.escape(p)}\b", q_lower):
            return p.title()

    # 2. Search in question against MySQL PlantCare database
    if db:
        try:
            records = db.query(PlantCare.common_name, PlantCare.plant_name).all()
            for c_name, p_name in records:
                if c_name and re.search(rf"\b{re.escape(c_name.lower())}\b", q_lower):
                    return c_name.strip()
                if p_name and re.search(rf"\b{re.escape(p_name.lower())}\b", q_lower):
                    return p_name.strip()
        except Exception:
            pass

    # If the user is asking a conversational, greeting, or language question,
    # DO NOT infer a plant name from previous history turns!
    if is_conversational_or_language_query(q_lower):
        return ""

    # 3. Search in recent conversation history (from newest to oldest) for plant-care follow-ups
    if history and isinstance(history, list):
        for turn in reversed(history[-6:]):
            text = (turn.get("text") or turn.get("content") or "").lower()
            for p in COMMON_PLANTS:
                if re.search(rf"\b{re.escape(p)}\b", text):
                    return p.title()
            if db:
                try:
                    for c_name, p_name in records:
                        if c_name and re.search(rf"\b{re.escape(c_name.lower())}\b", text):
                            return c_name.strip()
                except Exception:
                    pass

    return ""

def _generate_expert_fallback(
    question: str,
    plant_name: str = "",
    care_record: Optional[Any] = None,
    history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Botanical domain-knowledge and conversational fallback engine.
    Ensures natural, plant-specific, step-by-step guidance in simple English
    even when external AI API is unavailable.
    """
    ql = question.lower().strip()
    p_clean = (plant_name or "").lower().strip()
    p_label = plant_name or "your plant"

    # 1. Language Inquiries (e.g. Marathi, Hindi, etc.)
    if any(k in ql for k in ["marathi", "मराठी"]):
        return (
            "Yes, I can understand and speak Marathi! हो, मी मराठी बोलू शकतो. "
            "मी तुम्हाला तुमच्या वनस्पतींची काळजी घेण्यासाठी (plant care) कशी मदत करू शकतो? "
            "Feel free to ask your questions about watering, sunlight, soil, or plant problems in Marathi or English!"
        )

    if any(k in ql for k in ["hindi", "हिंदी"]):
        return (
            "Yes, I can understand and speak Hindi! हाँ, मैं हिंदी में बात कर सकता हूँ। "
            "मैं आपके पौधों की देखभाल, पानी, धूप या किसी समस्या के बारे में क्या मदद कर सकता हूँ? "
            "Feel free to ask your plant-care questions in Hindi or English!"
        )

    if any(k in ql for k in ["what language", "which language", "other language", "speak language", "can you speak"]):
        return (
            "I can understand and communicate in multiple languages including English, Marathi, Hindi, and more. "
            "Feel free to ask your plant-care questions in whichever language you feel most comfortable with!"
        )

    # 2. Greetings & Social Interactions
    if any(re.search(rf"\b{re.escape(g)}\b", ql) for g in ["hi", "hello", "hey", "namaste", "namaskar"]) or any(k in ql for k in ["good morning", "good evening", "good afternoon"]):
        return "Hello! I am your PlantAI assistant. How can I help you with your plants today?"

    if any(re.search(rf"\b{re.escape(t)}\b", ql) for t in ["thank", "thanks", "dhanyawad", "shukriya"]):
        return "You're very welcome! Feel free to ask anytime you need help keeping your plants healthy and thriving."

    if any(k in ql for k in ["who are you", "what are you", "what can you do"]):
        return (
            "I am PlantAI, your smart plant-care assistant. I can help diagnose yellow leaves, guide you on watering and sunlight, "
            "advise on soil and repotting, identify plant pests, and provide care tips tailored to your specific plants."
        )

    if "how are you" in ql:
        return "I'm doing well, thank you for asking! How are your plants doing today? Let me know if you need any care tips."

    # 3. General Botany & Plant Concepts
    if "photosynthesis" in ql:
        return (
            "Photosynthesis is the chemical process where plants absorb sunlight, water, and carbon dioxide to create glucose (food) and release oxygen. "
            "Providing your plants with their ideal lighting allows them to photosynthesize efficiently and grow strong."
        )

    if any(k in ql for k in ["propagate", "propagation", "cutting", "cuttings"]):
        return "\n\n".join([
            f"Plant propagation allows you to grow new plants from stem cuttings, leaf cuttings, or root division.",
            "Here is how to propagate most common houseplants (like pothos, monstera, or philodendron) in water:\n"
            "1. Choose a healthy stem: Select a healthy green vine with at least 2 to 3 leaves.\n"
            "2. Cut below a node: Use clean, sharp scissors to cut about 1 cm below a brown root node or leaf joint.\n"
            "3. Place in water: Put the cutting in a glass of room-temperature water, keeping the leaves dry above water.\n"
            "4. Provide bright light: Keep in bright, indirect sunlight and change the water once a week.\n"
            "5. Pot up: Once roots reach 5 cm long (in 3 to 4 weeks), plant the cutting in well-draining potting soil."
        ])

    # 4. Pet Safety & Toxicity
    if any(k in ql for k in ["toxic", "poison", "pet", "cat", "dog", "safe"]):
        toxic_plants = ["aloe vera", "snake plant", "peace lily", "monstera", "pothos", "jade plant", "zz plant", "philodendron", "dieffenbachia"]
        safe_plants = ["spider plant", "boston fern", "calathea", "peperomia", "areca palm", "cast iron plant", "money tree"]
        if any(tp in p_clean for tp in toxic_plants):
            return (
                f"No, {p_label} is mildly to moderately toxic to cats and dogs if chewed. "
                "The foliage contains calcium oxalate crystals that cause mouth irritation, drooling, and digestive upset. "
                "Keep it safely on a high shelf or hanging hook out of your pets' reach."
            )
        elif any(sp in p_clean for sp in safe_plants):
            return (
                f"Yes, {p_label} is non-toxic and pet-safe for both cats and dogs. "
                "While it will not harm pets if nibbled, keeping it out of reach helps protect the foliage from chewing damage."
            )
        else:
            return (
                f"Toxicity depends on the exact plant variety. Common houseplants like peace lilies, pothos, and snake plants are toxic to pets if chewed, "
                f"while spider plants and Boston ferns are safe. If you are unsure, keeping {p_label} safely out of reach is the best choice."
            )

    # 5. Pruning / Trimming
    if any(k in ql for k in ["prune", "pruning", "cut off", "cut them", "cut leaf", "trim", "remove leaf", "snip"]):
        return "\n\n".join([
            f"Yes, you can safely remove yellow or dying leaves from {p_label}. Yellow leaves will not turn green again, and trimming them helps the plant direct its energy into healthy new foliage.",
            "1. Clean your tools: Wipe scissors or pruning shears with rubbing alcohol or soapy water.\n"
            "2. Cut near the stem: Snip each damaged leaf near the base of its stalk, avoiding healthy green tissue.\n"
            "3. What to avoid: Never cut off more than 20% to 25% of the plant's leaves at one time."
        ])

    # 6. Problem: Pests / bugs / insects
    if any(k in ql for k in ["pest", "bug", "insect", "aphid", "mite", "mealybug", "scale", "webbing", "sticky"]):
        return "\n\n".join([
            f"Pests such as spider mites, aphids, or mealybugs can weaken {p_label} by feeding on plant sap.",
            "Here is what to check first and how to treat it:\n"
            "1. Check first: Inspect the undersides of leaves and leaf joints for fine webbing, sticky drops, or tiny moving specks.\n"
            "2. Isolate the plant: Move it away from other houseplants immediately so pests do not spread.\n"
            "3. Wash the foliage: Wipe the leaves with a soft damp cloth, or gently rinse the plant with lukewarm water.\n"
            "4. Safe treatment: Spray the foliage in the evening with diluted neem oil or mild soapy water (1 teaspoon of mild liquid soap per liter of water).\n"
            "5. What to avoid: Avoid spraying in direct sunlight, and do not use harsh chemical pesticides indoors.",
            "Do you see fine webbing, white cottony fluff, or tiny spots under the leaves?"
        ])

    # 7. Problem: Fungal disease / mold / leaf spots
    if any(k in ql for k in ["fungus", "mold", "mildew", "leaf spot", "black spot", "disease", "rot"]):
        return "\n\n".join([
            f"Fungal spots and mold on {p_label} are usually caused by excess moisture, poor air circulation, or wet leaves.",
            "Here is what to check first and how to fix it:\n"
            "1. Check first: Look at the spots to see if they are soft, powdery, or spreading, and check if the soil stays waterlogged.\n"
            "2. Improve air flow: Move the plant to an open area with good natural room ventilation.\n"
            "3. Remove infected leaves: Trim severely spotted leaves with clean scissors and dispose of them.\n"
            "4. Water carefully: Water only at the soil level; keep the leaves dry.\n"
            "5. What to avoid: Avoid misting leaves with water while treating fungal issues, and do not let water sit on the leaves overnight.",
            "Are the spots dry and brown, or is there a white, powdery film on the surface?"
        ])

    # 8. Problem: Drooping / wilting
    if any(k in ql for k in ["droop", "drooping", "wilt", "wilting", "limp"]):
        return "\n\n".join([
            f"Drooping leaves on {p_label} mean the stems are not receiving enough water from the roots. "
            "This can happen from underwatering (dry soil), overwatering (damaged roots that can no longer absorb moisture), or sudden cold drafts.",
            "Here is what to do:\n"
            "1. Check first: Push your finger 5 cm into the soil. If it is bone dry, the plant needs water. If it is soggy and heavy, the plant has had too much water.\n"
            "2. If dry: Give the plant a thorough, slow watering until water drains from the bottom holes.\n"
            "3. If soggy: Move the plant to a warm, bright spot with indirect light and allow the soil to dry out.\n"
            "4. What to avoid: Do not fertilize a wilting plant, and keep it away from cold air conditioners or hot radiators.",
            "When did you last water it, and does the soil feel wet or dry right now?"
        ])

    # 9. Problem: Slow growth / not growing / stunted
    if any(k in ql for k in ["slow growth", "slowly", "not growing", "stopped growing", "stunted"]):
        return "\n\n".join([
            f"Slow growth in {p_label} can happen for several reasons. The most common causes are low light, cramped roots, lack of nutrients, or natural resting during cooler seasons.",
            "Here is what to check first and how to help it grow:\n"
            "1. Check first: Check how much light the plant receives each day, and see if roots are pushing out of the bottom drainage holes.\n"
            "2. Increase light: Move the plant closer to a window with bright, indirect sunlight.\n"
            "3. Inspect the pot: If the plant has been in the same small pot for over a year and roots are tightly packed, repot it into a container 3 to 5 cm larger with fresh potting mix.\n"
            "4. Seasonal feeding: During spring and summer, feed with a balanced liquid houseplant fertilizer diluted to half strength once a month.\n"
            "5. What to avoid: Do not pour in excess fertilizer or overwater to force growth, as this burns roots and causes rot.",
            "How far is the plant currently sitting from your nearest window?"
        ])

    # 10. Problem: Yellow leaves or dropping foliage
    if any(k in ql for k in ["yellow", "yellowing", "dropping", "falling leaves", "brown spots", "leaves drop", "dying leaves"]):
        # Plant-specific tailoring for yellow leaves
        if any(s in p_clean for s in ["snake", "succulent", "cactus", "zz"]):
            return "\n\n".join([
                f"Yellow leaves on a {p_label} are almost always a sign of **overwatering**.",
                "Here is what to check and how to fix it:\n"
                "1. Check first: Insert your finger 5 cm into the soil. If the soil is damp or soggy, the plant is getting too much water.\n"
                "2. Let it dry out: Snake plants and succulents prefer their soil to dry out completely between waterings.\n"
                "3. Check drainage: Ensure your pot has drainage holes at the bottom and never let it sit in standing saucer water.\n"
                "4. Future schedule: Only water when the soil is completely bone-dry (every 2 to 4 weeks in warm weather, 4 to 6 weeks in winter).",
                "Does the soil feel wet or damp right now?"
            ])
        return "\n\n".join([
            f"Yellow or falling leaves on {p_label} can be caused by several factors. "
            "The most common causes are overwatering, underwatering, low sunlight, or sap-sucking pests.",
            "Here is what to check first and how to solve it:\n"
            "1. Check first: Push your finger about 5 cm into the soil to test moisture, and check under the leaves for tiny bugs.\n"
            "2. If soil is soggy: Let the soil dry out before watering again, and ensure the pot drains freely.\n"
            "3. If soil is dry: Give the plant a thorough drink until water trickles out the bottom holes.\n"
            "4. Provide good light: Place the plant in bright, indirect sunlight to help it recover.\n"
            "5. What to avoid: Do not fertilize a stressed plant with yellow leaves, and never leave the pot sitting in a saucer of standing water.",
            "Does the soil feel wet or dry right now, and are the yellow leaves soft or dry and crispy?"
        ])

    # 11. Topic: Watering
    if any(k in ql for k in ["water", "watering", "how often", "thirsty", "hydrate"]):
        for sp_key, profile in SPECIES_PROFILES.items():
            if sp_key in p_clean:
                return profile["water"]
        if care_record and getattr(care_record, 'water', None):
            return (
                f"For {p_label}, {care_record.water}. "
                "Always check before watering: insert your finger about 5 cm into the soil. "
                "If it feels damp, wait a few days; if dry, water thoroughly until liquid drains from the bottom."
            )
        return (
            f"Water {p_label} thoroughly whenever the top 3 to 5 cm of soil feels dry to the touch. "
            "Pour water evenly until it drains out the bottom holes, then discard any excess water in the saucer."
        )

    # 12. Topic: Sunlight
    if any(k in ql for k in ["sun", "sunlight", "light", "shade", "dark", "bright", "window"]):
        for sp_key, profile in SPECIES_PROFILES.items():
            if sp_key in p_clean:
                return profile["sunlight"]
        if care_record and getattr(care_record, 'sunlight', None):
            return (
                f"For {p_label}, {care_record.sunlight}. "
                "Bright indirect light near an east- or north-facing window is ideal. "
                "Keep it protected from harsh, direct midday sunbeams that can burn the leaves."
            )
        return (
            f"{p_label} grows best in bright, indirect sunlight. "
            "If the stems stretch and become tall or leggy, move it closer to light. "
            "If leaves develop brown scorch marks, move it slightly back from direct sun."
        )

    # 13. Topic: Soil & Repotting
    if any(k in ql for k in ["soil", "potting", "dirt", "pot", "repot", "container"]):
        for sp_key, profile in SPECIES_PROFILES.items():
            if sp_key in p_clean:
                return profile["soil"]
        if care_record and getattr(care_record, 'soil', None):
            return (
                f"For {p_label}, {care_record.soil}. "
                "When repotting, use a container with drainage holes that is 3 to 5 cm wider than the current root ball."
            )
        return (
            f"Use a well-draining potting mix with added perlite or coarse sand to keep the roots aerated for {p_label}. "
            "Always choose a pot with drainage holes at the bottom so excess water can escape easily."
        )

    # 14. Topic: Fertilizer
    if any(k in ql for k in ["fertilizer", "fertilize", "feed", "nutrients"]):
        return (
            f"Feed {p_label} with a balanced liquid houseplant fertilizer diluted to half strength once a month during spring and summer. "
            "Do not fertilize during winter or when the plant is stressed or recovering from disease."
        )

    # 15. Plant-Specific General Care Summary
    for sp_key, profile in SPECIES_PROFILES.items():
        if sp_key in p_clean:
            return profile["general"]

    if care_record and getattr(care_record, 'care', None):
        return f"For {p_label}: {care_record.care} Place it in bright indirect light and water whenever the topsoil feels dry."

    if plant_name:
        return (
            f"For {p_label}, provide bright, indirect sunlight and water when the top 3 to 5 cm of soil feels dry. "
            "Ensure the pot has adequate drainage holes, and keep it in a comfortable room temperature between 18°C and 26°C."
        )

    # 16. General plant question without a plant name
    if any(k in ql for k in ["care", "plant", "grow", "houseplant", "indoor", "outdoor", "garden", "flower", "leaf", "leaves"]):
        return (
            "I would be glad to help! Plant care depends heavily on the specific plant species—for example, succulents need dry soil and full sun, "
            "while ferns need high humidity and indirect light. Which plant would you like care guidance for?"
        )

    # 17. Honest fallback for out-of-scope non-plant queries when AI service is unavailable
    return (
        "I am currently in botanical offline mode, so I can only answer questions related to plants, gardening, and plant care. "
        "Feel free to ask me about watering, sunlight, soil, fertilizers, or troubleshooting plant problems!"
    )

def ask_assistant(
    question: str,
    plant_name: str = "",
    db: Optional[Session] = None,
    history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    AI Plant Assistant Service:
    Provides context-aware botanical advice leveraging MySQL care data,
    conversation history continuity, and Gemini AI with an expert fallback engine.
    """
    q = (question or "").strip()
    p_name = (plant_name or "").strip()

    if not q:
        return {
            "success": False,
            "status": "error",
            "message": "Question cannot be empty.",
            "answer": "Please ask a question about plant care, watering, sunlight, soil, fertilizers, or troubleshooting.",
            "plant_name": p_name,
            "suggestions": ["How often should I water?", "What kind of sunlight does it need?", "Why are the leaves yellow?"]
        }

    # If the user asks a conversational or language question (e.g. 'Can you speak Marathi?'),
    # clear any lingering plant_name so it does not contaminate the conversational response
    if is_conversational_or_language_query(q.lower()):
        # Only retain plant name if explicitly mentioned in the CURRENT question
        has_plant_in_q = any(re.search(rf"\b{re.escape(p)}\b", q.lower()) for p in COMMON_PLANTS)
        if not has_plant_in_q:
            p_name = ""

    # If plant_name was not provided, infer from question or history
    if not p_name:
        inferred = _extract_plant_name(q, history, db)
        if inferred:
            p_name = inferred

    # Fetch care record from database if plant_name is available
    care_record = None
    if p_name and db:
        try:
            search_clean = p_name.lower().strip()
            care_record = db.query(PlantCare).filter(
                (PlantCare.plant_name.ilike(f"%{search_clean}%")) |
                (PlantCare.common_name.ilike(f"%{search_clean}%"))
            ).first()
        except Exception as db_err:
            print("PlantCare DB lookup note:", db_err)

    # 1. Primary: Leverage Google Gemini AI Assistant with conversation history
    try:
        from .gemini_service import ask_plant_assistant as gemini_ask_assistant
        care_context = None
        if care_record:
            care_context = {
                "sunlight": care_record.sunlight,
                "water": care_record.water,
                "soil": care_record.soil,
                "location": care_record.location,
                "care": care_record.care
            }
        gemini_answer = gemini_ask_assistant(
            q,
            plant_name=p_name,
            care_context=care_context,
            history=history
        )
        if gemini_answer:
            suggestions = [
                f"How often should I water {p_name or 'it'}?",
                f"How much sunlight does {p_name or 'it'} need?",
                f"Why are {p_name or 'plant'} leaves turning yellow?"
            ]
            return {
                "success": True,
                "status": "answered",
                "source": "gemini_ai",
                "message": "Answer generated successfully via Google Gemini AI.",
                "answer": gemini_answer,
                "plant_name": p_name,
                "suggestions": suggestions
            }
    except Exception as e:
        print("AI Assistant Gemini non-blocking note:", e)

    # 2. Secondary: Fallback to expert botanical domain-knowledge & conversational engine
    fallback_ans = _generate_expert_fallback(q, p_name, care_record, history)
    suggestions = [
        f"How much sunlight does {p_name or 'it'} need?",
        f"How often should I water {p_name or 'it'}?",
        f"What is the best soil for {p_name or 'it'}?"
    ]

    return {
        "success": True,
        "status": "answered",
        "source": "botanical_assistant",
        "message": "Answer provided by PlantAI assistant engine.",
        "answer": fallback_ans,
        "plant_name": p_name,
        "suggestions": suggestions
    }
