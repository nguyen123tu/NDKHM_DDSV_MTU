"""
Core Image Validator Module
Xác thực, kiểm tra dung lượng, định dạng ảnh tải lên và xóa EXIF metadata
đảm bảo an toàn trước khi lưu trữ hoặc xử lý sinh trắc học.
"""

import os
import io
import logging
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Giới hạn dung lượng tải lên mặc định 5 MB
DEFAULT_MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}
ALLOWED_MIMES = {"image/png", "image/jpeg", "image/webp", "image/bmp"}


class ImageValidationError(Exception):
    """Lỗi xác thực ảnh tải lên"""

    pass


def allowed_file(filename: str) -> bool:
    """Kiểm tra phần mở rộng của file ảnh có hợp lệ không"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_and_strip_exif(
    file_stream, max_size: int = DEFAULT_MAX_IMAGE_SIZE
) -> bytes:
    """
    Xác thực file ảnh từ luồng dữ liệu (FileStorage hoặc BytesIO/bytes):
    1. Kiểm tra kích thước file (tối đa max_size bytes).
    2. Kiểm tra tính hợp lệ cấu trúc ảnh bằng PIL Image.verify().
    3. Loại bỏ toàn bộ EXIF metadata và chuẩn hóa chiều ảnh (EXIF transpose).
    4. Trả về bytes của ảnh sạch đã được strip metadata.
    """
    try:
        # Lấy nội dung raw bytes
        if hasattr(file_stream, "read"):
            raw_bytes = file_stream.read()
            if hasattr(file_stream, "seek"):
                file_stream.seek(0)
        elif isinstance(file_stream, bytes):
            raw_bytes = file_stream
        else:
            raise ImageValidationError("Định dạng input stream không hợp lệ")

        if len(raw_bytes) > max_size:
            size_mb = max_size / (1024 * 1024)
            raise ImageValidationError(
                f"Dung lượng ảnh vượt quá giới hạn cho phép ({size_mb:.1f} MB)"
            )

        if len(raw_bytes) == 0:
            raise ImageValidationError("File ảnh rỗng")

        # Verify cấu trúc ảnh (ngăn chặn file giả mạo hoặc shell code ngụy trang)
        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                img.verify()
        except Exception as e:
            logger.warning("PIL verify failed: %s", e)
            raise ImageValidationError(
                "File tải lên không phải là hình ảnh hợp lệ hoặc bị hỏng"
            )

        # Mở lại để chuẩn hóa và xóa EXIF metadata
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # Tự động xoay ảnh theo EXIF Orientation trước khi xóa EXIF
            img = ImageOps.exif_transpose(img)

            # Chuyển đổi sang mode RGB nếu cần thiết (loại bỏ alpha/palette lạ nếu lưu JPEG)
            if img.mode in ("RGBA", "P", "LA") and img.format in ("JPEG", "JPG"):
                img = img.convert("RGB")

            output = io.BytesIO()
            save_format = (
                img.format if img.format in ("JPEG", "PNG", "WEBP", "BMP") else "JPEG"
            )

            # Khi lưu không truyền exif/info -> toàn bộ EXIF metadata bị loại bỏ
            img.save(output, format=save_format, quality=95)
            return output.getvalue()

    except ImageValidationError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during image validation: %s", e)
        raise ImageValidationError(f"Lỗi xử lý ảnh: {str(e)}")


def save_validated_image(
    file_stream, destination_path: str, max_size: int = DEFAULT_MAX_IMAGE_SIZE
) -> str:
    """
    Xác thực, làm sạch metadata EXIF và lưu ảnh một cách an toàn vào ổ cứng.
    """
    cleaned_bytes = validate_and_strip_exif(file_stream, max_size=max_size)

    # Đảm bảo thư mục cha tồn tại
    parent_dir = os.path.dirname(destination_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(destination_path, "wb") as f:
        f.write(cleaned_bytes)

    return destination_path
