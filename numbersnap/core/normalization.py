from __future__ import annotations

import re

_CONFUSABLES = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1"})
_ALLOWED_AFTER_NORMALIZATION = re.compile(r"^[\d.,%$€¥+\-]+$")
_NUMERIC_CONTEXT = re.compile(r"[\d.,%$€¥+\-]")


def normalize_numeric_context(text: str) -> str:
    """Apply conservative OCR fixes only to otherwise numeric-looking text.

    Pure words such as ``OIL`` are deliberately left unchanged. Whitespace around
    or inside an OCR token is removed because OCR commonly separates a currency
    sign or minus sign from its value.
    """

    stripped = text.strip()
    compact = "".join(stripped.split())
    if not compact or not _NUMERIC_CONTEXT.search(compact):
        return stripped

    candidate = compact.translate(_CONFUSABLES)
    if _ALLOWED_AFTER_NORMALIZATION.fullmatch(candidate):
        return candidate
    return stripped
