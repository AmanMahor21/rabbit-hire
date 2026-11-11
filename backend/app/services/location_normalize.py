# backend/app/services/location_normalize.py
"""
Production location resolver for talent search.

Design (FAANG-style):
  1. Canonicalize at WRITE time (ingest) → store location_canonical in payload
  2. Resolve at QUERY time with the same function → expand aliases before filter
  3. Alias table is data (dict + optional fuzzy), not scattered if/else
  4. Substring / token fallback so residual free-text still matches

Do NOT treat a static alias dict as the whole system — it is one layer
of a shared resolver used by ingest, hybrid_search, and chat tools.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Optional, Sequence, Set

# ---------------------------------------------------------------------------
# Canonical city keys (stable, lowercase, no spaces where possible)
# Display names are title-cased for UI.
# ---------------------------------------------------------------------------
CANONICAL_DISPLAY: dict[str, str] = {
    "bengaluru": "Bengaluru",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "noida": "Noida",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "pune": "Pune",
    "kolkata": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "chandigarh": "Chandigarh",
    "kochi": "Kochi",
    "indore": "Indore",
    "remote": "Remote",
}

# Alias / synonym / common misspelling → canonical key
# Keep this table versioned (or move to YAML/Redis later). Product can extend.
_ALIAS_TO_CANONICAL: dict[str, str] = {
    # Bengaluru
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "bangaluru": "bengaluru",
    "banaglore": "bengaluru",
    "bengalooru": "bengaluru",
    "blr": "bengaluru",
    "bangalore urban": "bengaluru",
    "bengaluru urban": "bengaluru",
    "whitefield": "bengaluru",
    "koramangala": "bengaluru",
    "electronic city": "bengaluru",
    "indiranagar": "bengaluru",
    # Mumbai
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "navi mumbai": "mumbai",
    "thane": "mumbai",
    # Delhi NCR
    "delhi": "delhi",
    "new delhi": "delhi",
    "delhi ncr": "delhi",
    "ncr": "delhi",
    "delhi-ncr": "delhi",
    "noida": "noida",
    "greater noida": "noida",
    "gurgaon": "gurugram",
    "gurugram": "gurugram",
    "gurgoan": "gurugram",
    "faridabad": "delhi",
    "ghaziabad": "delhi",
    # Others
    "hyderabad": "hyderabad",
    "hyd": "hyderabad",
    "secunderabad": "hyderabad",
    "chennai": "chennai",
    "madras": "chennai",
    "pune": "pune",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "ahmedabad": "ahmedabad",
    "amdavad": "ahmedabad",
    "jaipur": "jaipur",
    "chandigarh": "chandigarh",
    "kochi": "kochi",
    "cochin": "kochi",
    "indore": "indore",
    "remote": "remote",
    "wfh": "remote",
    "work from home": "remote",
}

_WORD_RE = re.compile(r"[a-z0-9]+(?:\s+[a-z0-9]+)*")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


@lru_cache(maxsize=4096)
def resolve_one(raw: str) -> Optional[str]:
    """
    Resolve a single free-text location fragment to a canonical key.
    Returns None if nothing confident can be derived.
    """
    text = _clean(raw)
    if not text or len(text) < 2:
        return None

    # Exact alias
    if text in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[text]

    # Multi-word: try longest alias match as substring
    # Prefer longer keys so "delhi ncr" beats "delhi"
    for alias in sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True):
        if len(alias) >= 3 and alias in text:
            return _ALIAS_TO_CANONICAL[alias]

    # Token-level: any single token that is a known city
    for token in text.replace(",", " ").replace("/", " ").split():
        t = token.strip()
        if t in _ALIAS_TO_CANONICAL:
            return _ALIAS_TO_CANONICAL[t]

    # Light fuzzy for common 1-char typos on known cities (optional, cheap)
    try:
        from rapidfuzz import process, fuzz

        choices = list(_ALIAS_TO_CANONICAL.keys())
        match = process.extractOne(
            text, choices, scorer=fuzz.ratio, score_cutoff=88
        )
        if match:
            return _ALIAS_TO_CANONICAL[match[0]]
    except ImportError:
        pass

    return None


def normalize_locations(raw_locations: Optional[Sequence[str]]) -> List[str]:
    """
    Query-time / filter-time helper.
    Returns list of canonical keys (lowercase). Empty if nothing resolved.
    """
    if not raw_locations:
        return []
    seen: Set[str] = set()
    out: List[str] = []
    for item in raw_locations:
        if not item or not str(item).strip():
            continue
        # One string may contain multiple places ("Delhi / Noida")
        parts = re.split(r"[,;/|&]+", str(item))
        for part in parts:
            key = resolve_one(part)
            if key and key not in seen:
                seen.add(key)
                out.append(key)
    return out


def to_display(canonical_keys: Iterable[str]) -> List[str]:
    """Canonical keys → human display names for UI."""
    return [CANONICAL_DISPLAY.get(k, k.title()) for k in canonical_keys]


def expand_for_filter(user_locations: Optional[Sequence[str]]) -> List[str]:
    """
    Expand user-typed locations into all strings that should match in Qdrant:
    - canonical key
    - display name
    - every known alias that maps to that canonical
    Used when payload still has mixed raw strings (migration period).
    """
    keys = normalize_locations(user_locations)
    if not keys:
        # fallback: keep original cleaned strings so filter is not empty
        return [str(x).strip() for x in (user_locations or []) if str(x).strip()]

    expanded: Set[str] = set()
    for key in keys:
        expanded.add(key)
        expanded.add(CANONICAL_DISPLAY.get(key, key.title()))
        for alias, canon in _ALIAS_TO_CANONICAL.items():
            if canon == key:
                expanded.add(alias)
                expanded.add(alias.title())
    return sorted(expanded)


def canonicalize_payload_locations(raw_list: Optional[Sequence[str]]) -> dict:
    """
    Ingest-time helper. Call from process_file / upsert path.

    Returns:
      {
        "location": [...display names...],           # for UI / cards
        "location_canonical": [...canonical keys...], # for filters
      }
    """
    if not raw_list:
        return {"location": [], "location_canonical": []}

    keys = normalize_locations(list(raw_list))
    # If resolver found nothing, keep cleaned originals as display only
    if not keys:
        cleaned = [str(x).strip() for x in raw_list if str(x).strip()]
        return {"location": cleaned[:5], "location_canonical": []}

    displays = to_display(keys)
    return {
        "location": displays,
        "location_canonical": keys,
    }


def locations_match(
    payload_locations: Sequence[str] | None,
    payload_canonical: Sequence[str] | None,
    required_user_locations: Sequence[str] | None,
) -> bool:
    """
    Hard location constraint used by Python post-filter.
    Prefer canonical IDs; fall back to expanded alias substring on raw text.
    """
    required = normalize_locations(required_user_locations)
    if not required:
        return True

    # Fast path: canonical intersection
    payload_keys = set(payload_canonical or [])
    if not payload_keys and payload_locations:
        payload_keys = set(normalize_locations(payload_locations))
    if payload_keys & set(required):
        return True

    # Fallback: expanded aliases against joined raw text
    haystack = " ".join(str(x) for x in (payload_locations or [])).lower()
    for key in required:
        for term in expand_for_filter([key]):
            if term.lower() in haystack:
                return True
    return False
