import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from .image_validator import validate_and_preprocess_image
from .gemini_service import identify_plant as gemini_identify_plant

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(DOTENV_PATH, override=True)

PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY")
KINDWISE_API_KEY = os.getenv("KINDWISE_API_KEY")
CONFIDENCE_THRESHOLD = float(os.getenv("IDENTIFICATION_CONFIDENCE_THRESHOLD", "0.50"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))

# Curated, reliable botanical characteristics by species/genus
BOTANICAL_TRAITS_DB: Dict[str, List[str]] = {
    # Species-level documented traits
    "epipremnum aureum": [
        "Leaf shape: Heart-shaped (cordate) leaves with pointed tips and smooth margins",
        "Leaf color: Glossy bright green, frequently marbled with creamy-gold or light green variegation",
        "Growth habit: Flexible trailing or climbing vine with aerial rootlets at leaf nodes"
    ],
    "dracaena trifasciata": [
        "Leaf shape: Stiff, upright sword-like fleshy leaves tapering to a sharp point",
        "Leaf color: Deep green marked with gray-green horizontal zig-zag bands, often bordered with yellow margins",
        "Growth habit: Upright clumping rosette growing directly from underground rhizomes"
    ],
    "sansevieria trifasciata": [
        "Leaf shape: Stiff, upright sword-like fleshy leaves tapering to a sharp point",
        "Leaf color: Deep green marked with gray-green horizontal zig-zag bands, often bordered with yellow margins",
        "Growth habit: Upright clumping rosette growing directly from underground rhizomes"
    ],
    "monstera deliciosa": [
        "Leaf shape: Large, glossy heart-shaped to ovate leaves that develop natural holes (fenestrations) and deep edge splits",
        "Leaf color: Deep, lustrous forest green surface with prominent pale veins",
        "Stem features: Thick, sturdy climbing stems supported by cord-like aerial adventitious roots"
    ],
    "spathiphyllum": [
        "Leaf shape: Glossy, deep green lanceolate to elliptical leaves with prominent indented veins",
        "Flower structure: Showy white hood-like spathe sheltering an erect central creamy-white spadix spike",
        "Growth habit: Stemless evergreen perennial foliage rising directly from the root crown"
    ],
    "chlorophytum comosum": [
        "Leaf shape: Long, slender, arching ribbon-like leaves tapering to fine pointed tips",
        "Leaf color: Bright green foliage, typically featuring a broad central creamy-white stripe",
        "Growth habit: Fountain-like clumping rosette producing long wiry stolons that bear miniature plantlets"
    ],
    "ficus elastica": [
        "Leaf shape: Broadly elliptical, thick, leathery leaves with a prominent central midrib",
        "Leaf color: Glossy dark green or burgundy, with newly emerging leaves enclosed in a red-tinted sheath",
        "Stem features: Robust woody trunk and branches that secrete milky latex sap when cut"
    ],
    "ficus lyrata": [
        "Leaf shape: Large, dramatic fiddle- or lyre-shaped leaves with wavy margins and sunken veins",
        "Leaf texture: Thick, rigid, leathery surface with a bold sculptural vein pattern",
        "Growth habit: Upright woody tree with broad, architectural foliage"
    ],
    "ficus benjamina": [
        "Leaf shape: Small, pointed oval leaves with a distinct slender drip tip",
        "Growth habit: Graceful drooping or weeping branches forming a dense evergreen canopy",
        "Bark features: Smooth light-gray bark with fine slender branching twigs"
    ],
    "aloe vera": [
        "Leaf shape: Thick, fleshy, sword-shaped succulent leaves with soft whitish teeth along the margins",
        "Leaf color: Gray-green to pea-green arranged in a tight stemless rosette",
        "Leaf interior: Packed with clear, soothing mucilaginous water-storing gel"
    ],
    "zamioculcas zamiifolia": [
        "Leaf structure: Pinnately compound upright stems lined with thick, shiny, oval leaflets",
        "Leaf texture: Smooth, waxy, highly polished dark green finish",
        "Stem features: Swollen, bulbous petiole bases adapted to store water against drought"
    ],
    "crassula ovata": [
        "Leaf shape: Smooth, fleshy, oval jade-green leaves, frequently with red-tinged margins in bright sunlight",
        "Growth habit: Compact succulent shrub with thick, woody branching stems resembling a miniature tree"
    ],
    "ocimum tenuiflorum": [
        "Leaf shape: Ovate, slightly serrated green or purplish leaves with aromatic glandular hairs",
        "Stem features: Square-angled stems with opposite paired leaf arrangement",
        "Flower structure: Small tubular purple or white flowers clustered along erect terminal spikes"
    ],
    "ocimum basilicum": [
        "Leaf shape: Broadly oval, bright green leaves with cupped or smooth surfaces",
        "Stem features: Four-sided square stems with opposite leaf arrangement",
        "Aroma: Distinct sweet, peppery fragrance produced by microscopic surface oil glands"
    ],
    "hibiscus rosa-sinensis": [
        "Leaf shape: Glossy, dark green ovate leaves with coarsely serrated edges",
        "Flower structure: Large, 5-petaled flared blossoms with a long, prominent protruding staminal column"
    ],
    "rosa": [
        "Leaf shape: Odd-pinnately compound leaves typically composed of 3 to 7 serrated oval leaflets",
        "Stem features: Tough woody stems armed with sharp prickles or thorns",
        "Flower structure: Showy multi-petaled fragrant flowers with distinct basal sepals"
    ],
    "helianthus annuus": [
        "Leaf shape: Broad, heart-shaped to ovate leaves with coarse, rough hairy surfaces and serrated edges",
        "Flower structure: Large composite head with outer golden-yellow ray petals and a dark central disc",
        "Stem features: Thick, erect, rough-textured fibrous stalk"
    ],
    "carica papaya": [
        "Leaf shape: Very large, deeply palmately lobed leaves (5 to 7 lobes) with prominent whitish veins",
        "Stem features: Single straight hollow trunk with prominent leaf scar marks and a crown of leaves"
    ],
    "mangifera indica": [
        "Leaf shape: Long, narrow lanceolate leathery leaves with wavy margins, emerging reddish-bronze before maturing deep green",
        "Growth habit: Dense evergreen dome canopy with alternate, spirally clustered foliage"
    ],
    "calathea": [
        "Leaf shape: Broadly elliptical leaves with intricate feather-like patterns on the upper surface",
        "Leaf color: Deep green patterns with rich burgundy or purple undersides",
        "Leaf behavior: Leaves fold upward at night following natural circadian rhythms"
    ],
    "peperomia": [
        "Leaf shape: Compact, thick, semi-succulent leaves often rounded or spoon-shaped",
        "Flower structure: Slender, greenish-white tail-like flower spikes lacking showy petals"
    ],
    "philodendron": [
        "Leaf shape: Glossy cordate or deeply lobed foliage with distinct drip tips",
        "Growth habit: Climbing or trailing vine with aerial rootlets at nodes"
    ],
    "dieffenbachia": [
        "Leaf shape: Large, broad, oblong-ovate leaves with pointed tips",
        "Leaf color: Variegated with prominent cream, white, or pale yellow speckles and green borders",
        "Stem features: Thick, cane-like fleshy stems"
    ],
    "aglaonema": [
        "Leaf shape: Broad, lance-shaped leaves with elegant tapering tips",
        "Leaf color: Distinct silvery, gray-green, or pink marbling along the veins",
        "Growth habit: Low-growing compact clumping foliage"
    ],
    "syngonium podophyllum": [
        "Leaf shape: Distinct arrow-shaped (sagittate) juvenile leaves that become multi-lobed as the plant matures",
        "Growth habit: Trailing or climbing vine with adventitious aerial roots"
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
    # 1. Validation & Preprocessing
    is_valid, processed_bytes, val_error, quality_warning = validate_and_preprocess_image(
        image_bytes, filename, content_type, max_size=MAX_UPLOAD_SIZE
    )
    if not is_valid:
        return {
            "success": False,
            "status": "validation_error",
            "message": val_error or "Invalid image file.",
            "data": None
        }

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
        "image_quality": quality_warning or "Good"
    }

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "success": False,
            "status": "low_confidence",
            "message": uncertainty_note or "Unable to confidently identify this image. Please upload a clear image showing the complete plant or important identifying features.",
            "data": result_data
        }

    return {
        "success": True,
        "status": "identified",
        "message": f"Identified as {best_match['common_name']} ({best_match['scientific_name']})",
        "data": result_data
    }
