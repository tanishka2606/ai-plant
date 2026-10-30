import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from .image_validator import validate_and_preprocess_image, validate_botanical_image
from .gemini_service import identify_plant as gemini_identify_plant
from .uses_and_benefits import get_plant_uses_and_benefits

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH, override=True)

PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
KINDWISE_API_KEY = os.getenv("KINDWISE_API_KEY")
CONFIDENCE_THRESHOLD = float(os.getenv("IDENTIFICATION_CONFIDENCE_THRESHOLD", "0.50"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))

# Curated, reliable botanical characteristics by species/genus in simple, everyday English
BOTANICAL_TRAITS_DB: Dict[str, List[str]] = {
    "catharanthus roseus": [
        "Flowers have five flat petals with a small colored eye in the center.",
        "Leaves are smooth, shiny green with rounded tips.",
        "A visible pale line runs through the middle of each leaf."
    ],
    "vinca": [
        "Flowers have five flat petals with a small colored eye in the center.",
        "Leaves are smooth, shiny green with rounded tips.",
        "A visible pale line runs through the middle of each leaf."
    ],
    "opuntia microdasys": [
        "Flat, rounded green pads shaped like rabbit ears.",
        "Covered with dense clusters of tiny golden bristles.",
        "Thick succulent pads that store water."
    ],
    "cactaceae": [
        "Thick, fleshy green stems that store water.",
        "Sharp protective spines instead of normal flat leaves.",
        "Waxy outer surface to prevent water loss."
    ],
    "epipremnum aureum": [
        "Heart-shaped leaves with pointed tips.",
        "Shiny green leaves splashed with yellow or cream patches.",
        "Long, flexible trailing vine that easily climbs or hangs."
    ],
    "dracaena trifasciata": [
        "Tall, upright sword-shaped leaves that stand stiff.",
        "Dark green leaves patterned with light wavy bands.",
        "Bright yellow borders often run along the outer edges."
    ],
    "sansevieria trifasciata": [
        "Tall, upright sword-shaped leaves that stand stiff.",
        "Dark green leaves patterned with light wavy bands.",
        "Bright yellow borders often run along the outer edges."
    ],
    "monstera deliciosa": [
        "Large, glossy green leaves with natural splits and holes.",
        "Thick stems that grow long brown climbing air roots."
    ],
    "spathiphyllum": [
        "Dark green, glossy leaves with noticeable indented veins.",
        "Erect white flower with a single curved petal-like hood.",
        "Cream-colored textured spike standing in the center of the bloom."
    ],
    "chlorophytum comosum": [
        "Long, slender arching leaves with green and cream stripes.",
        "Produces thin stems carrying miniature baby plants."
    ],
    "ficus elastica": [
        "Large, thick leathery leaves with a deep glossy shine.",
        "A prominent main line runs straight down the middle of each leaf.",
        "New leaves unfold from a reddish pointed sheath."
    ],
    "ficus lyrata": [
        "Large leaves shaped like a violin or fiddle with wavy edges.",
        "Thick, leathery leaf surface with bold pale veins."
    ],
    "ficus benjamina": [
        "Small, glossy pointed oval leaves.",
        "Graceful drooping branches forming a leafy indoor tree."
    ],
    "aloe vera": [
        "Thick, fleshy green leaves growing in a tight rosette.",
        "Small, soft teeth line the outer edges of the leaves.",
        "Leaves are plump and filled with clear cooling gel."
    ],
    "zamioculcas zamiifolia": [
        "Upright stems lined with thick, shiny oval leaflets.",
        "Very glossy dark green leaves that look naturally polished.",
        "Swollen bulb-like stem bases that store water."
    ],
    "crassula ovata": [
        "Plump, smooth oval green leaves resembling smooth jade stones.",
        "Thick woody stems that branch like a miniature tree."
    ],
    "ocimum tenuiflorum": [
        "Small oval leaves with a strong, pleasant herbal scent.",
        "Four-sided square stems with leaves growing opposite each other.",
        "Tiny purple or white flowers on upright tips."
    ],
    "ocimum sanctum": [
        "Small oval leaves with a strong, pleasant herbal scent.",
        "Four-sided square stems with leaves growing opposite each other.",
        "Tiny purple or white flowers on upright tips."
    ],
    "ocimum basilicum": [
        "Bright green, gently cupped leaves with a sweet peppery fragrance.",
        "Square stems with paired leaves."
    ],
    "hibiscus rosa-sinensis": [
        "Glossy dark green leaves with saw-tooth edges.",
        "Large bell-shaped flowers with a long column in the middle."
    ],
    "rosa": [
        "Leaves made of 3 to 7 small toothed leaflets.",
        "Stems armed with sharp protective thorns.",
        "Showy, multi-petaled fragrant blossoms."
    ],
    "helianthus annuus": [
        "Large rough heart-shaped leaves on a thick hairy stalk.",
        "Bright yellow outer petals surrounding a dark brown seed center."
    ],
    "carica papaya": [
        "Very large leaves deeply divided into 5 to 7 finger-like lobes.",
        "Single straight trunk with distinct round leaf scars."
    ],
    "mangifera indica": [
        "Long, narrow leathery leaves with slightly wavy edges.",
        "New leaves start reddish-bronze before maturing deep green."
    ],
    "calathea": [
        "Oval leaves with striking dark and light green patterns.",
        "Rich purple or reddish-maroon color on the underside of leaves."
    ],
    "peperomia": [
        "Small, thick spoon-shaped leaves with a waxy texture.",
        "Slender tail-like flower spikes."
    ],
    "philodendron": [
        "Glossy heart-shaped leaves with pointed tips.",
        "Trailing vine with small climbing roots at leaf joints."
    ],
    "dieffenbachia": [
        "Broad oval leaves decorated with creamy white and yellow spots.",
        "Thick, fleshy cane-like stems."
    ],
    "aglaonema": [
        "Broad lance-shaped leaves with silver, light green, or pink patterns.",
        "Compact bushy growth habit."
    ],
    "syngonium podophyllum": [
        "Distinct arrow-shaped leaves with pointed lobes.",
        "Climbing or trailing green stems."
    ]
}

# Reliable family-level botanical characteristics
BOTANICAL_FAMILY_TRAITS: Dict[str, List[str]] = {
    "araceae": [
        "Leaf structure: Typically features glossy, heart-shaped or lobed blades with prominent venation",
        "Inflorescence: Characterized by a leaf-like spathe wrapping around a fleshy spadix spike",
        "Growth habit: Predominantly climbing, trailing, or rhizomatous evergreen perennials"
    ],
    "lamiaceae": [
        "Stem structure: Characteristic four-angled square stems",
        "Leaf arrangement: Simple leaves arranged in opposite pairs along the stems",
        "Aroma: Foliage contains specialized glandular hairs releasing aromatic essential oils"
    ],
    "rosaceae": [
        "Leaf structure: Alternate leaves with stipules at the base, often serrated or pinnately compound",
        "Flower structure: Regular flowers typically with five distinct petals and numerous stamens",
        "Stem features: Often woody stems, frequently bearing protective prickles or thorns"
    ],
    "fabaceae": [
        "Leaf structure: Pinnately or palmately compound leaves with distinct basal stipules",
        "Flower structure: Irregular, butterfly-like (papilionaceous) blossoms or brush-like clusters",
        "Root features: Roots form symbiotic nodules that fix atmospheric nitrogen"
    ],
    "asteraceae": [
        "Flower structure: Composite flower heads made of numerous tiny florets on a common receptacle",
        "Petal arrangement: Often bordered by strap-like ray florets resembling single petals",
        "Leaf structure: Alternate or opposite leaves, frequently toothed or lobed"
    ],
    "asparagaceae": [
        "Leaf structure: Slender, strap-like, or fleshy leaves with parallel venation",
        "Growth form: Often evergreen perennials growing from rhizomes, bulbs, or tuberous roots",
        "Flower structure: Small 6-parted flowers arranged in racemes, spikes, or panicles"
    ],
    "solanaceae": [
        "Leaf structure: Alternate, simple or pinnately lobed leaves with characteristic scent",
        "Flower structure: Radial 5-lobed star- or trumpet-shaped flowers with prominent central anthers",
        "Fruit type: Typically produces fleshy berries or capsules"
    ],
    "cactaceae": [
        "Stem features: Fleshy, thickened photosynthetic green stems adapted for water storage",
        "Leaf modification: Leaves reduced to protective spines arising from specialized areoles",
        "Surface: Thick waxy cuticle preventing moisture loss in arid environments"
    ],
    "orchidaceae": [
        "Flower structure: Highly specialized zygomorphic (bilaterally symmetrical) flowers with a modified lip (labellum)",
        "Growth habit: Frequently epiphytic with thick aerial roots coated in moisture-absorbing velamen",
        "Stem features: Often possess swollen pseudobulbs that store water and nutrients"
    ],
    "arecaceae": [
        "Trunk structure: Single unbranched columnar woody trunk with ring-like leaf scar markings",
        "Frond structure: Large, evergreen compound fronds either pinnate (feather-like) or palmate (fan-like)",
        "Growth habit: Foliage clustered at the crown of the trunk"
    ]
}

def _get_botanical_characteristics(scientific_name: str, genus: str = "", family: str = "") -> List[str]:
    """
    Returns verified botanical characteristics (leaf shape, color, arrangement, stem/flower features)
    based on reliable botanical data. Returns an empty list if data is not available.
    """
    s_clean = (scientific_name or "").lower().strip()
    g_clean = (genus or "").lower().strip()
    f_clean = (family or "").lower().strip()

    # 1. Check exact species or key in BOTANICAL_TRAITS_DB
    for key, traits in BOTANICAL_TRAITS_DB.items():
        if key in s_clean or s_clean in key:
            return list(traits)

    # 2. Check genus
    if not g_clean and " " in s_clean:
        g_clean = s_clean.split()[0]
    if g_clean:
        for key, traits in BOTANICAL_TRAITS_DB.items():
            if key == g_clean:
                return list(traits)

    # 3. Check botanical family
    if f_clean:
        for f_key, traits in BOTANICAL_FAMILY_TRAITS.items():
            if f_key in f_clean or f_clean in f_key:
                return list(traits)

    return []

def identify_plant(image_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
    """
    Accuracy-first plant identification pipeline:
    1. Validation & Preprocessing (orientation, lighting, resolution)
    2. Primary Identification via Pl@ntNet API
    3. Secondary / Complement via Kindwise API
    4. Google Gemini Vision for taxonomic verification and visible morphological features
    5. Strict confidence evaluation against threshold
    """
    # 1. Validation & Preprocessing (Physical integrity + Subject & Fake/Invalid Detection)
    is_valid, processed_bytes, val_error, val_meta = validate_botanical_image(
        image_bytes, filename, content_type, expected_subject="plant", max_size=MAX_UPLOAD_SIZE
    )
    if not is_valid:
        return {
            "success": False,
            "status": "validation_error",
            "message": val_error or "This image does not appear to contain a valid plant. Please upload a clear plant photograph.",
            "data": None
        }

    quality_warning = val_meta.get("quality_warning") if val_meta else None

    best_match = None
    candidates: List[Dict[str, Any]] = []
    identifying_features: List[str] = []
    uncertainty_note = ""

    # 2. Try Pl@ntNet API first (Preserving PlantNet integration)
    if PLANTNET_API_KEY:
        try:
            plantnet_url = "https://my-api.plantnet.org/v2/identify/all"
            response = requests.post(
                plantnet_url,
                params={
                    "api-key": PLANTNET_API_KEY,
                    "lang": "en",
                    "nb-results": 5
                },
                files={
                    "images": ("plant.jpg", processed_bytes, "image/jpeg")
                },
                data={
                    "organs": ["auto"]
                },
                timeout=20
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                for res in results:
                    species_info = res.get("species", {})
                    sci_name = species_info.get("scientificNameWithoutAuthor") or species_info.get("scientificName", "Unknown")
                    common_names = species_info.get("commonNames", [])
                    c_name = common_names[0] if common_names else sci_name
                    score = float(res.get("score", 0.0))
                    genus_info = species_info.get("genus", {}).get("scientificNameWithoutAuthor", "")
                    family_info = species_info.get("family", {}).get("scientificNameWithoutAuthor", "")

                    item = {
                        "scientific_name": sci_name,
                        "common_name": c_name,
                        "genus": genus_info,
                        "family": family_info,
                        "confidence": score,
                        "confidence_percent": round(score * 100, 2)
                    }
                    candidates.append(item)

                if candidates:
                    best_match = candidates[0]
        except Exception as e:
            print("Pl@ntNet API Request failed:", e)

    # 3. Fallback / Complement with Kindwise Plant.id if needed
    if (not best_match or best_match["confidence"] < CONFIDENCE_THRESHOLD) and KINDWISE_API_KEY:
        try:
            kindwise_response = requests.post(
                "https://plant.id/api/v3/identification",
                headers={"Api-Key": KINDWISE_API_KEY},
                files={"images": ("plant.jpg", processed_bytes, "image/jpeg")},
                timeout=20
            )
            if kindwise_response.status_code in (200, 201):
                kw_data = kindwise_response.json()
                kw_suggestions = kw_data.get("result", {}).get("classification", {}).get("suggestions", [])
                kw_candidates = []
                for sug in kw_suggestions[:5]:
                    name = sug.get("name", "Unknown")
                    details = sug.get("details", {}) or {}
                    c_names = details.get("commonNames") or []
                    c_name = c_names[0] if c_names else name
                    prob = float(sug.get("probability", 0.0))
                    kw_candidates.append({
                        "scientific_name": name,
                        "common_name": c_name,
                        "genus": name.split()[0] if " " in name else name,
                        "family": "",
                        "confidence": prob,
                        "confidence_percent": round(prob * 100, 2)
                    })

                if kw_candidates and (not best_match or kw_candidates[0]["confidence"] > best_match["confidence"]):
                    best_match = kw_candidates[0]
                    candidates = kw_candidates
        except Exception as e:
            print("Kindwise API Request failed:", e)

    # 4. Integrate Google Gemini AI Vision (Feature 2 requirement)
    try:
        gemini_result = gemini_identify_plant(processed_bytes, mime_type="image/jpeg")
        if gemini_result:
            identifying_features = gemini_result.get("identifying_features", [])
            uncertainty_note = gemini_result.get("uncertainty_note", "")

            # If Pl@ntNet/Kindwise had no match or very low confidence, use Gemini's botanical taxon
            if not best_match or best_match["confidence"] < CONFIDENCE_THRESHOLD:
                g_sci = gemini_result.get("scientific_name")
                g_com = gemini_result.get("common_name")
                if g_sci:
                    best_match = {
                        "scientific_name": g_sci,
                        "common_name": g_com or g_sci,
                        "genus": gemini_result.get("genus") or (g_sci.split()[0] if " " in g_sci else g_sci),
                        "family": gemini_result.get("family", ""),
                        "confidence": 0.85 if not gemini_result.get("is_uncertain") else 0.45,
                        "confidence_percent": 85.0 if not gemini_result.get("is_uncertain") else 45.0
                    }
                    candidates = [best_match]
    except Exception as e:
        print("Gemini plant identification non-blocking note:", e)

    # 5. Check if any matches were returned
    if not best_match:
        return {
            "success": False,
            "status": "error",
            "message": "Plant identification service is temporarily unavailable. Please try again later.",
            "data": None
        }

    # 6. Attach reliable botanical characteristics to each candidate
    for cand in candidates:
        c_sci = cand.get("scientific_name", "")
        c_gen = cand.get("genus", "")
        c_fam = cand.get("family", "")
        cand["characteristics"] = _get_botanical_characteristics(c_sci, c_gen, c_fam)

    # If Gemini did not provide image-specific identifying features, fall back to verified botanical characteristics
    if not identifying_features:
        identifying_features = _get_botanical_characteristics(
            best_match["scientific_name"],
            best_match.get("genus", ""),
            best_match.get("family", "")
        )

    # 7. Evaluate Confidence against Threshold
    confidence = best_match["confidence"]
    confidence_pct = best_match["confidence_percent"]

    # 8. Fetch evidence-based Uses and Benefits
    uses_and_benefits = get_plant_uses_and_benefits(
        best_match["scientific_name"],
        best_match.get("common_name", "")
    )

    result_data = {
        "plant_name": best_match["scientific_name"],
        "common_name": best_match["common_name"],
        "scientific_name": best_match["scientific_name"],
        "species": best_match["scientific_name"],
        "genus": best_match.get("genus", ""),
        "family": best_match.get("family", ""),
        "confidence": confidence,
        "confidence_percent": confidence_pct,
        "identifying_features": identifying_features,
        "characteristics": identifying_features,
        "uncertainty_note": uncertainty_note,
        "candidates": candidates,
        "uses_and_benefits": uses_and_benefits,
        "image_quality": quality_warning or "Good"
    }

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "success": False,
            "status": "low_confidence",
            "message": uncertainty_note or "Unable to confidently identify this image. Please upload a clear image showing the complete plant or important identifying features.",
            "data": result_data,
            "uses_and_benefits": uses_and_benefits
        }

    return {
        "success": True,
        "status": "identified",
        "message": f"Identified as {best_match['common_name']} ({best_match['scientific_name']})",
        "data": result_data,
        "uses_and_benefits": uses_and_benefits
    }
