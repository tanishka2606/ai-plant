import io
import math
from typing import Tuple, Optional
from PIL import Image, ImageOps, ImageStat

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/octet-stream"
}

def validate_and_preprocess_image(
    image_bytes: bytes,
    filename: str = "image.jpg",
    content_type: Optional[str] = None,
    max_size: int = 10 * 1024 * 1024
) -> Tuple[bool, Optional[bytes], Optional[str], Optional[str]]:
    """
    Validates image file existence, size, MIME type, decodability,
    analyzes lighting and quality, corrects orientation, and converts safely to clean RGB JPEG bytes.
    
    Returns:
        (is_valid, processed_bytes, error_message, quality_warning)
    """
    if not image_bytes or len(image_bytes) == 0:
        return False, None, "The uploaded image file is empty.", None

    if len(image_bytes) > max_size:
        max_mb = max_size // (1024 * 1024)
        return False, None, f"Image file size exceeds the {max_mb}MB limit.", None

    # Check extension
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext and ext not in SUPPORTED_EXTENSIONS and (content_type and content_type not in SUPPORTED_MIME_TYPES):
        return False, None, f"Unsupported image format ({ext}). Supported formats: JPG, JPEG, PNG, WEBP.", None

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        # Re-open for operations after verify
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as err:
        return False, None, "Corrupted or unreadable image file. Please upload a valid image.", None

    width, height = image.size
    if width < 80 or height < 80:
        return False, None, "Image resolution is too low for reliable identification. Minimum resolution is 80x80 pixels.", None

    # EXIF orientation fix
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # Convert safely to RGB
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        alpha = image.split()[-1]
        background.paste(image, mask=alpha)
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Quality, contrast, and edge definition checks
    grayscale = image.convert("L")
    stat = ImageStat.Stat(grayscale)
    avg_brightness = stat.mean[0]
    std_dev = stat.stddev[0]

    quality_warning = None

    if avg_brightness < 18:
        return False, None, "The uploaded image is too dark to identify features clearly. Please upload a photo with adequate lighting.", None

    if avg_brightness > 248:
        return False, None, "The uploaded image is overexposed / washed out. Please upload a photo with balanced lighting.", None

    if std_dev < 6:
        return False, None, "Image lacks sufficient visual detail or contrast. Please upload a clear photo of the plant or leaf.", None

    # Safe blur check evaluated on real leaf varieties:
    # Naturally smooth leaves (tulip, cactus, rubber plant) have edge_mean >= 9.0.
    # Out-of-focus or motion-blurred foliage (edge_mean < 3.0) is rejected.
    try:
        from PIL import ImageFilter
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        edge_mean = ImageStat.Stat(edges).mean[0]
        if edge_mean < 3.0:
            return False, None, "The image is too blurry or out-of-focus to distinguish foliar features. Please upload a sharper photo.", None
        elif edge_mean < 6.0:
            quality_warning = "Slight soft focus detected. For best accuracy, capture close-up details in clear focus."
    except Exception:
        pass



    # Save to high quality JPEG
    output_buffer = io.BytesIO()
    # Limit max dimension to 2048 to prevent memory exhaustion while retaining botanical detail
    max_dim = 2048
    if max(width, height) > max_dim:
        image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    image.save(output_buffer, format="JPEG", quality=95, optimize=True)
    processed_bytes = output_buffer.getvalue()

    return True, processed_bytes, None, quality_warning


def validate_botanical_image(
    image_bytes: bytes,
    filename: str = "image.jpg",
    content_type: Optional[str] = None,
    expected_subject: str = "plant",
    max_size: int = 10 * 1024 * 1024
) -> Tuple[bool, Optional[bytes], Optional[str], Optional[dict]]:
    """
    Comprehensive two-stage botanical image validator:
    Stage 1: Structural & physical validation (size, MIME, decodability, resolution, lighting, sharpness).
    Stage 2: Semantic, authenticity, and fake/invalid image detection via Google Gemini AI vision:
             - Rejects unrelated subjects (people, animals, cars, buildings, electronics, food, objects).
             - Rejects wrong botanical category (e.g. whole plant uploaded to seed identifier).
             - Rejects AI-generated images, digital art, drawings, cartoons, sketches, screenshots.
             - Treats borderline authenticity cautiously without declaring genuine photos fake.
             - Provides clear, user-friendly rejection messages.

    Returns:
        (is_valid, processed_bytes, error_message, validation_metadata)
    """
    # 1. Structural physical validation
    is_valid, processed_bytes, val_error, quality_warning = validate_and_preprocess_image(
        image_bytes, filename, content_type, max_size=max_size
    )
    if not is_valid:
        return False, None, val_error, None

    # 2. Semantic & authenticity validation via Gemini AI
    validation_meta = None
    try:
        from .gemini_service import validate_image_authenticity_and_subject
        gemini_val = validate_image_authenticity_and_subject(processed_bytes, expected_subject=expected_subject)
        if gemini_val and isinstance(gemini_val, dict):
            validation_meta = gemini_val
            # If the subject is invalid or artificial / AI-generated / drawing
            if gemini_val.get("is_valid") is False:
                rejection = gemini_val.get("rejection_reason")
                if not rejection:
                    auth = gemini_val.get("authenticity", "")
                    if auth in ("likely_ai_generated", "digital_art_or_drawing"):
                        rejection = "This image may be digitally generated, illustrated, or manipulated. Please upload an original photograph."
                    elif gemini_val.get("is_blurry"):
                        rejection = "The image is too blurry or out-of-focus to distinguish botanical features. Please upload a sharper photo."
                    elif expected_subject == "seed":
                        rejection = "This image does not appear to contain a seed. Please upload a clear seed photograph."
                    else:
                        rejection = "This image does not appear to contain a valid plant. Please upload a clear plant photograph."

                return False, None, rejection, validation_meta
    except Exception as e:
        print("Semantic image validation note:", e)

    # Valid image
    return True, processed_bytes, None, validation_meta

