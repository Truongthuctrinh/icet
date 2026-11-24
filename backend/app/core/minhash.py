"""MinHash + LSH banding, tự cài đặt bằng numpy.

- Shingle: cụm 5 âm tiết liền nhau sau khi chuẩn hoá (thường hoá, bỏ dấu câu, bỏ watermark).
- MinHash: 128 hàm băm dạng (a*x + b) mod p; chữ ký = giá trị nhỏ nhất của mỗi hàm trên tập shingle.
  Xác suất 2 chữ ký trùng nhau ở 1 vị trí = độ tương đồng Jaccard của 2 tập shingle.
- LSH banding: chia chữ ký thành 32 dải x 4 giá trị. 2 đoạn có ít nhất 1 dải trùng -> ứng viên.
  Ngưỡng xấp xỉ (1/32)^(1/4) ≈ 0.42: đoạn giống nhau >= 50% bị bắt với xác suất ~87%, >= 60% ~99%.
"""
import hashlib
import re
import unicodedata

import numpy as np

from app.core.watermark import strip_marks

SHINGLE_SIZE = 5
NUM_PERM = 128
BANDS = 32
ROWS = NUM_PERM // BANDS  # 4
MIN_SHINGLES = 5  # đoạn quá ngắn (dưới ~9 âm tiết, vd. lời thoại "Ừ.") không đưa vào chỉ mục

_MERSENNE_PRIME = np.uint64((1 << 61) - 1)
_MAX_HASH = np.uint64((1 << 32) - 1)
_rng = np.random.RandomState(20261124)  # hạt giống cố định: chữ ký phải ổn định giữa các lần chạy
_A = _rng.randint(1, (1 << 61) - 1, size=NUM_PERM, dtype=np.uint64)
_B = _rng.randint(0, (1 << 61) - 1, size=NUM_PERM, dtype=np.uint64)

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = strip_marks(text)
    text = unicodedata.normalize("NFC", text).lower()
    text = _PUNCT.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def shingles(text: str) -> set[str]:
    words = normalize(text).split()
    if len(words) < SHINGLE_SIZE:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + SHINGLE_SIZE]) for i in range(len(words) - SHINGLE_SIZE + 1)}


def _hash32(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=4).digest(), "little")


def signature(shingle_set: set[str]) -> np.ndarray:
    hv = np.array([_hash32(s) for s in shingle_set], dtype=np.uint64)[:, None]
    with np.errstate(over="ignore"):  # tràn số uint64 là có chủ đích (giống thư viện datasketch)
        phv = np.bitwise_and((_A * hv + _B) % _MERSENNE_PRIME, _MAX_HASH)
    return phv.min(axis=0)


def band_buckets(sig: np.ndarray) -> list[tuple[int, int]]:
    """[(dải, mã xô)] — mã xô là băm 64 bit của 4 giá trị trong dải."""
    result = []
    for band in range(BANDS):
        chunk = sig[band * ROWS : (band + 1) * ROWS].tobytes()
        bucket = int.from_bytes(hashlib.blake2b(chunk, digest_size=8).digest(), "big", signed=True)
        result.append((band, bucket))
    return result


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
