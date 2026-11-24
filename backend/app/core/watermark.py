"""Watermark vô hình: mã hoá id phiên đọc bằng ký tự zero-width.

Cấu trúc 1 dấu ẩn (42 ký tự, không nhìn thấy):
    ZWJ + 40 bit + ZWJ
    40 bit = 32 bit session_id + 8 bit checksum (CRC32 rút gọn)
    bit 0 = U+200B (zero width space), bit 1 = U+200C (zero width non-joiner)
"""
import re
import zlib

ZERO = "​"
ONE = "‌"
BOUNDARY = "‍"
PAYLOAD_BITS = 32
CHECK_BITS = 8
TOTAL_BITS = PAYLOAD_BITS + CHECK_BITS

_MARK_PATTERN = re.compile(f"{BOUNDARY}([{ZERO}{ONE}]{{{TOTAL_BITS}}}){BOUNDARY}")
_INVISIBLE_PATTERN = re.compile(f"[{ZERO}{ONE}{BOUNDARY}]")


def _checksum(session_id: int) -> int:
    return zlib.crc32(session_id.to_bytes(4, "big")) & 0xFF


def encode_mark(session_id: int) -> str:
    if not 0 <= session_id < 2**PAYLOAD_BITS:
        raise ValueError("session_id vượt quá 32 bit")
    value = (session_id << CHECK_BITS) | _checksum(session_id)
    bits = format(value, f"0{TOTAL_BITS}b")
    return BOUNDARY + "".join(ONE if b == "1" else ZERO for b in bits) + BOUNDARY


def embed(text: str, session_id: int, every: int = 8) -> str:
    """Gắn dấu ẩn sau từ đầu tiên, rồi cứ mỗi `every` từ (mặc định 8) lại gắn thêm 1 lần."""
    mark = encode_mark(session_id)
    words = text.split(" ")
    return " ".join(w + mark if i % every == 0 else w for i, w in enumerate(words))


def strip_marks(text: str) -> str:
    return _INVISIBLE_PATTERN.sub("", text)


def extract_session_ids(text: str) -> tuple[int, list[int]]:
    """Trả về (số dấu ẩn tìm thấy, danh sách session_id hợp lệ, không trùng, giữ thứ tự)."""
    marks = _MARK_PATTERN.findall(text)
    session_ids: list[int] = []
    for bits in marks:
        value = int("".join("1" if c == ONE else "0" for c in bits), 2)
        session_id = value >> CHECK_BITS
        if value & 0xFF == _checksum(session_id) and session_id not in session_ids:
            session_ids.append(session_id)
    return len(marks), session_ids
