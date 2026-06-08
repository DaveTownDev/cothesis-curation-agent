"""
Source verification — does the URL/DOI actually resolve to a real resource?

Audit 2026-06-06 found the pipeline confidently enriched dead and fabricated
sources (e.g. a non-existent JAMA DOI). This guards the front of the pipeline.

Key nuance from the URL-liveness analysis: academic publishers frequently return
403/429 to bots — that is NOT a dead link. Only 404/410, DNS failure, or an
unresolvable DOI count as 'dead'. 403/429 -> 'blocked' (treated as live).
"""
from __future__ import annotations

import logging

import httpx

from agents.shared.url_safety import _MAX_REDIRECTS, is_safe_outbound_url, normalise_doi

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CoThesis-curation/1.0)"}
_DEAD_CODES = {404, 410}


def verify_source(url: str | None, doi: str | None = None, timeout: int = 12) -> dict:
    """
    Returns {status, code, final_url, resolved}.
      status: 'live' (reachable) | 'blocked' (403/429 — treat as live) |
              'dead' (404/410/DNS-fail/unresolvable DOI) | 'unknown' (no url+doi)
    A 'dead' result should stop confident enrichment and route to human review.
    """
    # Prefer the DOI (authoritative); fall back to the URL.
    target: str | None = None
    if doi:
        clean = normalise_doi(doi)
        if not clean:
            return {"status": "dead", "code": None, "final_url": None, "resolved": False, "err": "invalid doi"}
        target = f"https://doi.org/{clean}"
    elif url:
        if not is_safe_outbound_url(url):
            logger.warning("verify_source blocked unsafe URL: %s", url[:80])
            return {"status": "dead", "code": None, "final_url": None, "resolved": False, "err": "blocked url"}
        target = url
    if not target:
        return {"status": "unknown", "code": None, "final_url": None, "resolved": False}

    try:
        with httpx.Client(
            follow_redirects=True, max_redirects=_MAX_REDIRECTS, timeout=timeout, headers=_HEADERS,
        ) as c:
            r = c.get(target)
            code = r.status_code
            if code in _DEAD_CODES:
                return {"status": "dead", "code": code, "final_url": str(r.url), "resolved": False}
            if code in (403, 429):
                return {"status": "blocked", "code": code, "final_url": str(r.url), "resolved": True}
            if code >= 500:
                # Server error — inconclusive, don't condemn the source
                return {"status": "blocked", "code": code, "final_url": str(r.url), "resolved": True}
            return {"status": "live", "code": code, "final_url": str(r.url), "resolved": True}
    except httpx.HTTPError as exc:
        # DNS failure / connection refused / timeout — if we used a DOI and it
        # didn't resolve, that's dead; a bare-URL network blip is inconclusive.
        msg = str(exc).lower()
        if doi or "name or service not known" in msg or "no address" in msg or "nodename" in msg:
            return {"status": "dead", "code": None, "final_url": None, "resolved": False, "err": str(exc)[:100]}
        logger.warning("verify_source inconclusive for %s: %s", target, exc)
        return {"status": "blocked", "code": None, "final_url": None, "resolved": False, "err": str(exc)[:100]}
