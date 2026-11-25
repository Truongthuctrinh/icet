"""Kiểm tra và chuẩn hoá ảnh người dùng tải lên.

Không tin vào đuôi file hay Content-Type người dùng gửi: mở ảnh bằng Pillow để biết định dạng thật.
Mọi ảnh được vẽ lại thành WebP mới:
  - file giả dạng ảnh (chèn mã độc, HTML...) không sống sót qua bước này
  - dữ liệu EXIF (toạ độ GPS, loại máy chụp...) bị bỏ -> bảo vệ quyền riêng tư người dùng
  - kích thước cố định, dung lượng nhỏ -> trang tải nhanh
"""
import io
import warnings

from PIL import Image, ImageOps

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_PIXELS = 40_000_000  # chặn "bom giải nén": file vài KB nhưng giải ra hàng tỉ điểm ảnh
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

# Loại ảnh -> (rộng, cao). Bìa truyện tỉ lệ 2:3 như bìa sách, ảnh đại diện hình vuông
SIZES = {
    "cover": (600, 900),
    "avatar": (256, 256),
}


class ImageError(ValueError):
    pass


def process_image(raw: bytes, kind: str) -> bytes:
    """Trả về ảnh WebP đã cắt đúng tỉ lệ. Ảnh không hợp lệ -> ImageError (thông báo tiếng Việt)."""
    size = SIZES[kind]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(raw))
            fmt = probe.format
            probe.verify()  # kiểm tra file không bị hỏng / cắt cụt
            img = Image.open(io.BytesIO(raw))
            img.load()
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageError("Ảnh quá lớn (quá nhiều điểm ảnh)")
    except Exception:
        raise ImageError("File không phải ảnh hợp lệ")

    if fmt not in ALLOWED_FORMATS:
        raise ImageError("Chỉ nhận ảnh JPG, PNG hoặc WebP")
    if getattr(img, "is_animated", False):
        raise ImageError("Không nhận ảnh động")

    img = ImageOps.exif_transpose(img)  # ảnh chụp điện thoại: xoay đúng chiều trước khi bỏ EXIF
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    img = img.convert("RGBA" if has_alpha else "RGB")
    img = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)  # cắt giữa cho đúng tỉ lệ

    out = io.BytesIO()
    img.save(out, format="WEBP", quality=82, method=4)  # không truyền exif -> ảnh mới sạch metadata
    return out.getvalue()
