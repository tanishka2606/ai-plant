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
