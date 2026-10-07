import re
import unicodedata
from urllib.parse import quote

# Letters that NFKD normalization doesn't reduce to ASCII on its own (ı has no base letter).
_TURKISH_TO_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def _ascii_part(text: str) -> str:
    """'Koç Holding' -> 'Koc_Holding': transliterate, then keep only filename-safe characters."""
    text = text.translate(_TURKISH_TO_ASCII)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9-]+", "_", text).strip("_")


def _unicode_part(text: str) -> str:
    """Keep letters like ç and ş, but replace whitespace and characters invalid in filenames."""
    return re.sub(r'[\s\\/:*?"<>|]+', "_", text).strip("_")


def cv_filename(company: str, role: str, suffix: str = "") -> str:
    """ASCII-only CV filename, safe for HTTP headers and as a path component."""
    parts = ["CV", _ascii_part(company), _ascii_part(role), suffix]
    return "_".join(part for part in parts if part) + ".pdf"


def content_disposition(company: str, role: str) -> str:
    """Content-Disposition header that keeps Turkish letters in browsers that support it.

    HTTP headers are Latin-1, so the UTF-8 name goes in filename* (RFC 6266 / RFC 5987)
    and an ASCII-transliterated name in filename= for older clients.
    """
    unicode_name = "_".join(p for p in ["CV", _unicode_part(company), _unicode_part(role)] if p)
    return (
        f'inline; filename="{cv_filename(company, role)}"; '
        f"filename*=UTF-8''{quote(unicode_name + '.pdf')}"
    )
