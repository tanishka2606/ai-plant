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
    "dieffenbachia", "peperomia", "sansevieria", "areca palm", "anthurium"
]

def _extract_plant_name(question: str, history: Optional[List[Dict[str, Any]]], db: Optional[Session]) -> str:
    """
    Infers the plant species from the question or recent conversation history.
    Searches both common houseplant names and the MySQL PlantCare database.
    """
    q_lower = (question or "").lower()

    # 1. Search in question against common plant list
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

    # 3. Search in recent conversation history (from newest to oldest)
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
    Botanical domain-knowledge fallback engine.
    Ensures natural, plant-specific, step-by-step guidance in simple English
    even when AI API is unavailable.
    """
    ql = question.lower().strip()
    p_label = plant_name or "your plant"

    # 1. Pet Safety & Toxicity (simple question: direct, concise, no follow-up question)
    if any(k in ql for k in ["toxic", "poison", "pet", "cat", "dog", "safe"]):
        toxic_plants = ["aloe vera", "snake plant", "peace lily", "monstera", "pothos", "jade plant", "zz plant", "philodendron", "dieffenbachia"]
        safe_plants = ["spider plant", "boston fern", "calathea", "peperomia", "areca palm", "cast iron plant", "money tree"]
        p_clean = plant_name.lower().strip()
        if any(tp in p_clean for tp in toxic_plants):
            return (
                f"No, {p_label} is mildly to moderately toxic to cats and dogs if chewed. "
                "The leaves and stems contain calcium oxalate crystals that cause mouth irritation, drooling, and stomach upset. "
                "Keep it safely on a high shelf or hanging hook out of your pets' reach."
            )
        elif any(sp in p_clean for sp in safe_plants):
            return (
                f"Yes, {p_label} is non-toxic and pet-safe for both cats and dogs. "
                "While it will not harm pets if nibbled, keeping it out of reach helps protect the foliage from chewing damage."
            )
        else:
            return (
                f"Toxicity depends on the exact plant variety. Common houseplants like peace lilies, pothos, and snake plants are toxic if eaten by pets, "
                f"while spider plants and Boston ferns are safe. If you are unsure, keeping {p_label} safely out of reach is the best choice."
            )

    # 2. Pruning / Trimming (practical steps)
    if any(k in ql for k in ["prune", "pruning", "cut off", "cut them", "cut leaf", "trim", "remove leaf", "snip"]):
        return "\n\n".join([
            f"Yes, you can safely remove yellow or dying leaves from {p_label}. Yellow leaves will not turn green again, and trimming them helps the plant direct its energy into healthy new foliage.",
            "1. Clean your tools: Wipe scissors or pruning shears with rubbing alcohol or soapy water.",
            "2. Cut near the stem: Snip each damaged leaf near the base of its stalk, avoiding healthy green tissue.",
            "3. What to avoid: Never cut off more than 20% to 25% of the plant's leaves at one time."
        ])

    # 3. Problem: Pests / bugs / insects (problem: multi-cause, steps, avoid, 1 follow-up)
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

    # 4. Problem: Fungal disease / mold / leaf spots
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

    # 5. Problem: Drooping / wilting
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

    # 6. Problem: Slow growth / not growing / stunted
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

    # 7. Problem: Yellow leaves or dropping foliage
    if any(k in ql for k in ["yellow", "yellowing", "dropping", "falling leaves", "brown spots", "leaves drop", "dying leaves"]):
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

    # 8. Topic: Watering (simple question: direct, 2-4 sentences, no follow-up question)
    if any(k in ql for k in ["water", "watering", "how often", "thirsty", "hydrate"]):
        if care_record and getattr(care_record, 'water', None):
            return (
                f"For {p_label}, {care_record.water}. "
                "Always check before watering: insert your finger about 5 cm into the soil. "
                "If it feels damp, wait a few days; if dry, water thoroughly until liquid drains from the bottom."
            )
        p_lower = p_label.lower()
        if any(s in p_lower for s in ["snake", "succulent", "cactus", "zz"]):
            return (
                f"Water {p_label} only when the soil is completely dry from top to bottom. "
                "This usually means watering every 2 to 3 weeks in warm months and less often in winter. "
                "Always empty the drainage tray so the roots do not sit in standing water."
            )
        elif any(f in p_lower for f in ["fern", "calathea", "peace lily"]):
            return (
                f"Keep the soil for {p_label} lightly moist but never soggy. "
                "Water when the top 2 to 3 cm of soil feels barely dry to the touch, and use room-temperature water."
            )
        else:
            return (
                f"Water {p_label} thoroughly whenever the top 3 to 5 cm of soil feels dry to the touch. "
                "Pour water evenly until it drains out the bottom holes, then discard any excess water in the saucer."
            )

    # 9. Topic: Sunlight (simple question: direct, 2-4 sentences, no follow-up question)
    if any(k in ql for k in ["sun", "sunlight", "light", "shade", "dark", "bright", "window"]):
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

    # 10. Topic: Soil & Repotting (simple question: direct, 2-4 sentences, no follow-up question)
    if any(k in ql for k in ["soil", "potting", "dirt", "pot", "repot", "container"]):
        if care_record and getattr(care_record, 'soil', None):
            return (
                f"For {p_label}, {care_record.soil}. "
                "When repotting, use a container with drainage holes that is 3 to 5 cm wider than the current root ball."
            )
        return (
            f"Use a well-draining potting mix with added perlite or coarse sand to keep the roots aerated for {p_label}. "
            "Always choose a pot with drainage holes at the bottom so excess water can escape easily."
        )

    # 11. Topic: Fertilizer (simple question: direct, 2-4 sentences, no follow-up question)
    if any(k in ql for k in ["fertilizer", "fertilize", "feed", "nutrients"]):
        return (
            f"Feed {p_label} with a balanced liquid houseplant fertilizer diluted to half strength once a month during spring and summer. "
            "Do not fertilize during winter or when the plant is stressed or recovering from disease."
        )

    # 12. Unclear question with no plant name (clarifying question)
    if not plant_name:
        return (
            "I would be glad to help! Most plant issues come down to light, watering, or soil drainage. "
            "Could you tell me the name of your plant and describe what its leaves look like right now?"
        )

    # 13. General care summary
    if care_record and getattr(care_record, 'care', None):
        return f"For {p_label}: {care_record.care} Place it in bright indirect light and water whenever the topsoil feels dry."

    return (
        f"For {p_label}, place it in bright indirect sunlight and water when the top 3 to 5 cm of soil feels dry. "
        "Ensure the pot has drainage holes, and inspect the leaves regularly for healthy growth."
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

    # Leverage Google Gemini AI Assistant with conversation history
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
                "message": "Answer generated successfully via Google Gemini AI.",
                "answer": gemini_answer,
                "plant_name": p_name,
                "suggestions": suggestions
            }
    except Exception as e:
        print("AI Assistant Gemini non-blocking note:", e)

    # Fallback to expert botanical domain-knowledge engine
    fallback_ans = _generate_expert_fallback(q, p_name, care_record, history)
    suggestions = [
        f"How much sunlight does {p_name or 'it'} need?",
        f"How often should I water {p_name or 'it'}?",
        f"What is the best soil for {p_name or 'it'}?"
    ]

    return {
        "success": True,
        "status": "answered",
        "message": "Response generated from botanical knowledge base.",
        "answer": fallback_ans,
        "plant_name": p_name,
        "suggestions": suggestions
    }
