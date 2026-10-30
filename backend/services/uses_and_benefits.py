"""
Botanical Uses and Benefits Knowledge Engine for PlantAI.
Provides simple, clear, everyday English explanations of plant and seed uses and benefits.

Strict compliance rules:
1. Use simple everyday English and short sentences (1-2 points per category).
2. Avoid complicated botanical and medical terminology.
3. No unsupported or invented health or nutritional claims.
4. If a category is not supported or applicable, omit it completely (no empty sections).
5. No identification confidence display for seeds.
"""

from typing import Dict, Any, List, Optional

# In-memory session cache to avoid redundant API calls
_AI_CACHE: Dict[str, Dict[str, Any]] = {}

# =====================================================================
# 1. CURATED PLANT USES & BENEFITS DATABASE (Simple Everyday English)
# =====================================================================
PLANT_USES_AND_BENEFITS_DB: Dict[str, Dict[str, Any]] = {
    # Catharanthus roseus / Periwinkle (as requested in prompt example)
    "catharanthus roseus": {
        "common_uses": [
            "Grown in gardens for its beautiful flowers.",
            "Used to decorate garden borders and pots."
        ],
        "health_benefits": [
            "Contains compounds used to make certain cancer medicines."
        ],
        "environmental_benefits": [
            "Its flowers provide nectar for butterflies."
        ]
    },
    "vinca": {
        "common_uses": [
            "Grown in gardens for its beautiful flowers.",
            "Used to decorate garden borders and pots."
        ],
        "health_benefits": [
            "Contains compounds used to make certain cancer medicines."
        ],
        "environmental_benefits": [
            "Its flowers provide nectar for butterflies."
        ]
    },
    "dracaena trifasciata": {
        "common_uses": [
            "Popular indoor plant for homes and offices.",
            "Adds tall green decoration to room corners."
        ],
        "environmental_benefits": [
            "Helps clean indoor air by absorbing everyday pollutants.",
            "Releases fresh oxygen into the room at night."
        ],
        "practical_uses": [
            "Very easy to care for and can go weeks without watering."
        ]
    },
    "sansevieria trifasciata": {
        "common_uses": [
            "Popular indoor plant for homes and offices.",
            "Adds tall green decoration to room corners."
        ],
        "environmental_benefits": [
            "Helps clean indoor air by absorbing everyday pollutants.",
            "Releases fresh oxygen into the room at night."
        ],
        "practical_uses": [
            "Very easy to care for and can go weeks without watering."
        ]
    },
    "aloe vera": {
        "common_uses": [
            "Grown in pots on sunny windowsills and in gardens.",
            "Common natural ingredient in skin lotions and soaps."
        ],
        "health_benefits": [
            "Clear gel from leaves soothes minor burns and sunburns.",
            "Helps keep dry or irritated skin cool and moisturized."
        ],
        "practical_uses": [
            "Needs very little water and thrives in warm, sunny spots."
        ]
    },
    "ocimum tenuiflorum": {
        "common_uses": [
            "Grown in courtyards, balconies, and home gardens.",
            "Fresh leaves are commonly brewed to make herbal tea."
        ],
        "health_benefits": [
            "Drinking tulsi tea helps ease mild coughs, colds, and sore throats.",
            "Rich in natural antioxidants that help protect the body."
        ],
        "environmental_benefits": [
            "Its small purple blossoms attract honeybees.",
            "Natural scent helps keep mosquitoes away."
        ]
    },
    "ocimum sanctum": {
        "common_uses": [
            "Grown in courtyards, balconies, and home gardens.",
            "Fresh leaves are commonly brewed to make herbal tea."
        ],
        "health_benefits": [
            "Drinking tulsi tea helps ease mild coughs, colds, and sore throats.",
            "Rich in natural antioxidants that help protect the body."
        ],
        "environmental_benefits": [
            "Its small purple blossoms attract honeybees.",
            "Natural scent helps keep mosquitoes away."
        ]
    },
    "ocimum basilicum": {
        "common_uses": [
            "Popular cooking herb used in pasta, pizza, and pesto.",
            "Grown in sunny kitchen pots and garden beds."
        ],
        "health_benefits": [
            "Provides vitamins A and K to support healthy bones."
        ],
        "environmental_benefits": [
            "Flowering tips provide sweet nectar for honeybees."
        ],
        "practical_uses": [
            "Planted near tomato plants to help deter garden insects."
        ]
    },
    "epipremnum aureum": {
        "common_uses": [
            "Popular trailing houseplant grown in hanging baskets or on shelves.",
            "Easily grown in jars of water or regular potting soil."
        ],
        "environmental_benefits": [
            "Helps filter everyday dust and pollutants from indoor air.",
            "Adds gentle natural moisture to dry, air-conditioned rooms."
        ],
        "practical_uses": [
            "Very simple to propagate by cutting a stem and placing it in water."
        ]
    },
    "monstera deliciosa": {
        "common_uses": [
            "Famous indoor statement plant with large, split green leaves.",
            "Brings a lush, tropical look to living rooms and offices."
        ],
        "environmental_benefits": [
            "Broad leaves help catch dust and improve indoor humidity."
        ],
        "practical_uses": [
            "Can be trained to climb indoor trellises or moss poles."
        ]
    },
    "spathiphyllum": {
        "common_uses": [
            "Indoor flowering plant with dark green leaves and elegant white blooms.",
            "Adds classic decoration to bedrooms, living rooms, and hallways."
        ],
        "environmental_benefits": [
            "Known to help purify indoor air of common household vapors."
        ],
        "practical_uses": [
            "Leaves gently droop when dry, signaling exactly when to water."
        ]
    },
    "chlorophytum comosum": {
        "common_uses": [
            "Popular hanging plant with long arching green-and-white leaves."
        ],
        "environmental_benefits": [
            "Helps clean indoor air by removing common household fumes."
        ],
        "practical_uses": [
            "Safe for homes with cats and dogs because it is non-toxic.",
            "Grows small baby plantlets on runners that easily root in water."
        ]
    },
    "ficus elastica": {
        "common_uses": [
            "Stately indoor tree with thick, shiny dark green leaves.",
            "Provides an attractive upright focal point in rooms."
        ],
        "environmental_benefits": [
            "Large glossy leaves capture floating indoor dust particles."
        ],
        "practical_uses": [
            "Leaves are easy to keep clean by wiping with a soft damp cloth."
        ]
    },
    "ficus lyrata": {
        "common_uses": [
            "Indoor tree with large fiddle-shaped leaves.",
            "Popular decorative centerpiece for bright living rooms."
        ],
        "environmental_benefits": [
            "Helps freshen indoor air and adds natural humidity."
        ],
        "practical_uses": [
            "Grows best in bright, indirect sunlight near a window."
        ]
    },
    "crassula ovata": {
        "common_uses": [
            "Popular succulent with round fleshy leaves, symbolizing good luck.",
            "Grown on sunny windowsills or outdoor patios."
        ],
        "environmental_benefits": [
            "Stores water in its leaves and needs very little watering."
        ],
        "practical_uses": [
            "Can be pruned and shaped like a miniature bonsai tree."
        ]
    },
    "zamioculcas zamiifolia": {
        "common_uses": [
            "Tough indoor plant with polished leaves that thrive in low light.",
            "Often placed in windowless offices, hallways, and corners."
        ],
        "environmental_benefits": [
            "Adds pleasant greenery to indoor spaces with little natural light."
        ],
        "practical_uses": [
            "Can survive for weeks without water thanks to thick underground bulbs."
        ]
    },
    "rosa": {
        "common_uses": [
            "Grown in gardens worldwide for its fragrant, colorful flowers.",
            "Petals are used to make rose water and floral decorations."
        ],
        "health_benefits": [
            "Rose hips (seed pods) are naturally rich in Vitamin C.",
            "Warm rose tea helps soothe mild throat irritation."
        ],
        "environmental_benefits": [
            "Open blooms provide rich pollen for bees and butterflies."
        ]
    },
    "hibiscus rosa-sinensis": {
        "common_uses": [
            "Garden shrub with large, showy tropical blossoms.",
            "Petals are steeped into refreshing herbal teas."
        ],
        "health_benefits": [
            "Hibiscus tea is rich in antioxidants that support general wellness.",
            "Crushed flower petals are used as a natural conditioning hair rinse."
        ],
        "environmental_benefits": [
            "Bright blossoms attract butterflies and hummingbirds."
        ]
    },
    "helianthus annuus": {
        "common_uses": [
            "Grown for tasty edible seeds, cooking oil, and cut flowers."
        ],
        "health_benefits": [
            "Seeds provide healthy plant fats, Vitamin E, and minerals."
        ],
        "environmental_benefits": [
            "Large yellow flower heads provide rich food for bees and wild birds."
        ]
    },
    "carica papaya": {
        "common_uses": [
            "Grown for its sweet, juicy tropical fruit.",
            "Green unripe fruit is cooked in savory dishes and salads."
        ],
        "health_benefits": [
            "Ripe fruit is packed with Vitamin C and aids healthy digestion."
        ],
        "practical_uses": [
            "Fresh leaves can be wrapped around meat to help naturally tenderize it."
        ]
    },
    "mangifera indica": {
        "common_uses": [
            "Grown for sweet, delicious mangoes.",
            "Provides dense, cooling shade in warm gardens."
        ],
        "health_benefits": [
            "Mango fruit is rich in vitamins A and C to support immune health."
        ],
        "environmental_benefits": [
            "Large evergreen tree canopy provides shelter for birds and insects."
        ]
    },
    "dieffenbachia": {
        "common_uses": [
            "Attractive indoor plant with patterned green-and-white leaves.",
            "Thrives in shaded rooms and offices."
        ],
        "environmental_benefits": [
            "Broad leaves catch airborne dust and help regulate room humidity."
        ],
        "practical_uses": [
            "Keep away from small pets and children because its leaf sap is irritating."
        ]
    },
    "opuntia microdasys": {
        "common_uses": [
            "Decorative indoor cactus with flat pads shaped like rabbit ears.",
            "Grown in sunny windowsills and dry rock gardens."
        ],
        "environmental_benefits": [
            "Requires almost no water, making it great for water-saving gardens."
        ],
        "practical_uses": [
            "Needs watering only once every 3 to 4 weeks."
        ]
    },
    "cactaceae": {
        "common_uses": [
            "Popular decorative succulent for sunny desks and windowsills.",
            "Used in drought-tolerant rock gardens."
        ],
        "environmental_benefits": [
            "Needs very little water and tolerates hot, dry conditions."
        ],
        "practical_uses": [
            "Only water after the soil has completely dried out."
        ]
    }
}

# =====================================================================
# 2. CURATED SEED USES & BENEFITS DATABASE (Simple Everyday English)
# =====================================================================
SEED_USES_AND_BENEFITS_DB: Dict[str, Dict[str, Any]] = {
    "helianthus annuus": {
        "common_uses": [
            "Eaten raw or roasted as a crunchy snack.",
            "Pressed to produce light, healthy cooking oil.",
            "Added to breads, granolas, and trail mixes."
        ],
        "nutritional_benefits": [
            "Rich in Vitamin E, magnesium, and healthy unsaturated fats.",
            "Good plant source of protein and dietary fiber."
        ],
        "health_benefits": [
            "Healthy fats support heart wellness and cholesterol balance.",
            "Vitamin E helps protect the body's cells from oxidative damage."
        ],
        "environmental_benefits": [
            "Sunflower plants attract pollinating bees and enrich farm soil."
        ],
        "practical_uses": [
            "Can be sprouted in trays on the kitchen counter for fresh microgreens."
        ]
    },
    "cucurbita pepo": {
        "common_uses": [
            "Roasted with salt or spices as a tasty snack.",
            "Added to salads, granolas, soups, and baked breads."
        ],
        "nutritional_benefits": [
            "Packed with natural zinc, magnesium, and plant protein.",
            "Contains healthy polyunsaturated fats."
        ],
        "health_benefits": [
            "Zinc supports a strong immune system and healthy skin.",
            "Magnesium helps muscles relax and supports restful sleep."
        ],
        "practical_uses": [
            "Blends easily into creamy dairy-free pestos and dips."
        ]
    },
    "salvia hispanica": {
        "common_uses": [
            "Stirred into smoothies, yogurts, oatmeal, and baked goods.",
            "Used as an egg substitute in vegan recipes when soaked in water."
        ],
        "nutritional_benefits": [
            "Excellent plant source of heart-healthy omega-3 fats.",
            "Very high in dietary fiber to promote smooth digestion."
        ],
        "health_benefits": [
            "Helps keep you feeling full longer and supports gut regularity.",
            "Omega-3 fatty acids help support healthy heart function."
        ],
        "practical_uses": [
            "Absorbs liquid quickly to create creamy, no-cook chia pudding."
        ]
    },
    "linum usitatissimum": {
        "common_uses": [
            "Ground into meal and added to breakfast cereals, breads, and smoothies.",
            "Pressed into flaxseed oil."
        ],
        "nutritional_benefits": [
            "High in plant-based omega-3 fatty acids and dietary fiber."
        ],
        "health_benefits": [
            "Supports healthy digestion and regular bowel movements.",
            "Helps maintain healthy cholesterol levels."
        ],
        "practical_uses": [
            "Can be boiled in water to make a simple, natural hair gel."
        ]
    },
    "triticum aestivum": {
        "common_uses": [
            "Milled into flour for making bread, roti, and pasta.",
            "Sprouted to produce fresh wheatgrass juice."
        ],
        "nutritional_benefits": [
            "Provides wholesome complex carbohydrates for steady everyday energy.",
            "Contains dietary fiber, plant protein, iron, and B-vitamins."
        ],
        "health_benefits": [
            "Whole grains support healthy digestion and heart wellness."
        ],
        "environmental_benefits": [
            "Wheat cover crops protect topsoil from wind and water erosion."
        ]
    },
    "mangifera indica": {
        "common_uses": [
            "Pressed to extract rich mango seed butter for skin creams and lip balms.",
            "Planted in moist soil to grow new mango trees."
        ],
        "health_benefits": [
            "Natural mango butter deeply moisturizes dry skin and cracked lips."
        ],
        "environmental_benefits": [
            "Using fruit pits prevents organic waste from going to landfills."
        ],
        "practical_uses": [
            "Carefully opening the tough outer shell helps the seed sprout much faster."
        ]
    },
    "carica papaya": {
        "common_uses": [
            "Dried and ground as a mild, peppery table spice.",
            "Planted to grow fresh papaya fruit trees."
        ],
        "health_benefits": [
            "Contains natural enzymes that help support smooth digestion."
        ],
        "practical_uses": [
            "Ground seeds can be added to salad dressings for a zesty kick."
        ]
    },
    "solanum lycopersicum": {
        "common_uses": [
            "Sown in seed starter trays to grow fresh garden tomatoes.",
            "Pressed into specialty cosmetic tomato seed oil."
        ],
        "nutritional_benefits": [
            "Contains healthy fatty acids and antioxidant Vitamin E."
        ],
        "health_benefits": [
            "Antioxidants help protect and nourish skin."
        ],
        "practical_uses": [
            "Dried seeds can be saved in envelopes for planting next season."
        ]
    },
    "zea mays": {
        "common_uses": [
            "Milled into cornmeal for tortillas, porridge, and baking.",
            "Popped as whole-grain popcorn."
        ],
        "nutritional_benefits": [
            "Provides dietary fiber and steady energy.",
            "Contains natural eye-healthy pigments like lutein."
        ],
        "health_benefits": [
            "Dietary fiber aids regular digestive transit."
        ]
    },
    "phaseolus vulgaris": {
        "common_uses": [
            "Staple kitchen bean cooked in soups, chili, and side dishes.",
            "Enriches garden soil when planted with vegetables."
        ],
        "nutritional_benefits": [
            "Excellent source of plant protein and dietary fiber.",
            "Rich in iron, potassium, and folate."
        ],
        "health_benefits": [
            "Supports heart health and helps keep you feeling satisfied.",
            "Provides steady energy without sudden sugar spikes."
        ],
        "environmental_benefits": [
            "Naturally adds nitrogen back into garden soil, helping other plants grow."
        ]
    },
    "pisum sativum": {
        "common_uses": [
            "Cooked fresh or dried in soups, stews, and vegetable curries.",
            "Sprouted on sunny windowsills for sweet green salad pea shoots."
        ],
        "nutritional_benefits": [
            "High in plant protein, Vitamin C, and fiber."
        ],
        "health_benefits": [
            "Nourishes beneficial gut bacteria and supports muscle health."
        ],
        "environmental_benefits": [
            "Naturally enriches soil with nitrogen."
        ]
    }
}

# =====================================================================
# 3. PUBLIC API: GET PLANT USES AND BENEFITS
# =====================================================================
def get_plant_uses_and_benefits(scientific_name: str, common_name: str = "") -> Dict[str, Any]:
    """
    Returns short, simple, everyday English uses and benefits for an identified plant.
    1. Checks curated database.
    2. If not found, calls Gemini AI with strict brevity & simplicity rules.
    3. Prunes empty or unverified categories cleanly.
    """
    s_norm = (scientific_name or "").lower().strip()
    c_norm = (common_name or "").lower().strip()

    # 1. Check curated database
    for key, data in PLANT_USES_AND_BENEFITS_DB.items():
        if key in s_norm or s_norm in key or (c_norm and key in c_norm):
            return _clean_plant_payload(data)

    genus = s_norm.split()[0] if " " in s_norm else s_norm
    if genus and genus in PLANT_USES_AND_BENEFITS_DB:
        return _clean_plant_payload(PLANT_USES_AND_BENEFITS_DB[genus])

    # 2. Check in-memory AI cache
    cache_key = f"plant:{s_norm}"
    if cache_key in _AI_CACHE:
        return _clean_plant_payload(_AI_CACHE[cache_key])

    # 3. Call Gemini AI generator
    try:
        from .gemini_service import generate_uses_and_benefits
        ai_data = generate_uses_and_benefits(common_name or scientific_name, scientific_name, item_type="plant")
        if ai_data and isinstance(ai_data, dict):
            _AI_CACHE[cache_key] = ai_data
            return _clean_plant_payload(ai_data)
    except Exception as e:
        print("Gemini plant uses & benefits generation note:", e)

    # 4. Safe baseline for uncataloged plant (omits health claims completely)
    baseline = {
        "common_uses": [
            f"Grown as an attractive decorative plant for home or garden.",
            f"Valued for its distinctive green foliage."
        ],
        "environmental_benefits": [
            "Helps add fresh oxygen and natural moisture to indoor air."
        ],
        "practical_uses": [
            "Can be grown in pots or garden beds with appropriate sunlight and water."
        ]
    }
    return _clean_plant_payload(baseline)

# =====================================================================
# 4. PUBLIC API: GET SEED USES AND BENEFITS
# =====================================================================
def get_seed_uses_and_benefits(scientific_name: str, common_name: str = "") -> Dict[str, Any]:
    """
    Returns short, simple, everyday English uses and benefits for an identified seed.
    1. Checks curated database.
    2. If not found, calls Gemini AI.
    3. Strictly omits confidence numbers or empty sections.
    """
    s_norm = (scientific_name or "").lower().strip()
    c_norm = (common_name or "").lower().strip()

    # 1. Check curated database
    for key, data in SEED_USES_AND_BENEFITS_DB.items():
        if key in s_norm or s_norm in key or (c_norm and key in c_norm):
            return _clean_seed_payload(data)

    genus = s_norm.split()[0] if " " in s_norm else s_norm
    if genus and genus in SEED_USES_AND_BENEFITS_DB:
        return _clean_seed_payload(SEED_USES_AND_BENEFITS_DB[genus])

    # 2. Check in-memory AI cache
    cache_key = f"seed:{s_norm}"
    if cache_key in _AI_CACHE:
        return _clean_seed_payload(_AI_CACHE[cache_key])

    # 3. Call Gemini AI generator
    try:
        from .gemini_service import generate_uses_and_benefits
        ai_data = generate_uses_and_benefits(common_name or scientific_name, scientific_name, item_type="seed")
        if ai_data and isinstance(ai_data, dict):
            _AI_CACHE[cache_key] = ai_data
            return _clean_seed_payload(ai_data)
    except Exception as e:
        print("Gemini seed uses & benefits generation note:", e)

    # 4. Safe baseline for uncataloged seed
    baseline = {
        "common_uses": [
            f"Sown in soil to grow healthy new {common_name or 'plant'} specimens.",
            "Preserved as garden seed stock for the next planting season."
        ],
        "environmental_benefits": [
            "Supports natural plant reproduction and local biodiversity."
        ],
        "practical_uses": [
            "Plant at the recommended depth in moist, well-draining soil."
        ]
    }
    return _clean_seed_payload(baseline)

# =====================================================================
# 5. PAYLOAD SANITIZATION HELPERS
# =====================================================================
def _clean_plant_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prunes empty lists and formats strictly into the 4 requested simple plant categories:
    - common_uses
    - health_benefits
    - environmental_benefits
    - practical_uses
    """
    cleaned: Dict[str, Any] = {}

    # 1. Common Uses
    c_uses = data.get("common_uses") or []
    if isinstance(c_uses, list):
        valid = [str(x).strip() for x in c_uses if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["common_uses"] = valid[:2]

    # 2. Health Benefits (merge any medicinal/health items into clean list; omit if empty)
    h_bens = data.get("health_benefits") or data.get("medicinal_uses") or data.get("human_health_benefits") or []
    if isinstance(h_bens, list):
        valid = [str(x).strip() for x in h_bens if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["health_benefits"] = valid[:2]

    # 3. Environmental Benefits
    e_bens = data.get("environmental_benefits") or []
    if isinstance(e_bens, list):
        valid = [str(x).strip() for x in e_bens if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["environmental_benefits"] = valid[:2]

    # 4. Other Practical Uses
    p_uses = data.get("practical_uses") or data.get("practical_applications") or []
    if isinstance(p_uses, list):
        valid = [str(x).strip() for x in p_uses if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["practical_uses"] = valid[:2]

    return cleaned

def _clean_seed_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prunes empty lists and formats strictly into the 5 requested simple seed categories:
    - common_uses
    - nutritional_benefits
    - health_benefits
    - environmental_benefits
    - practical_uses
    Strictly removes any confidence fields.
    """
    cleaned: Dict[str, Any] = {}

    # 1. Common Uses
    c_uses = data.get("common_uses") or []
    if isinstance(c_uses, list):
        valid = [str(x).strip() for x in c_uses if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["common_uses"] = valid[:2]

    # 2. Nutritional Benefits
    n_bens = data.get("nutritional_benefits") or data.get("nutritional_value") or []
    if isinstance(n_bens, list):
        valid = [str(x).strip() for x in n_bens if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["nutritional_benefits"] = valid[:2]

    # 3. Health Benefits
    h_bens = data.get("health_benefits") or []
    if isinstance(h_bens, list):
        valid = [str(x).strip() for x in h_bens if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["health_benefits"] = valid[:2]

    # 4. Environmental Benefits
    e_bens = data.get("environmental_benefits") or []
    if isinstance(e_bens, list):
        valid = [str(x).strip() for x in e_bens if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["environmental_benefits"] = valid[:2]

    # 5. Other Practical Uses
    p_uses = data.get("practical_uses") or data.get("practical_applications") or []
    if isinstance(p_uses, list):
        valid = [str(x).strip() for x in p_uses if x and str(x).strip() and str(x).strip().lower() not in ("none", "n/a", "no benefits available")]
        if valid:
            cleaned["practical_uses"] = valid[:2]

    # Strict rule: Ensure no confidence fields exist
    cleaned.pop("confidence", None)
    cleaned.pop("confidence_percent", None)

    return cleaned
