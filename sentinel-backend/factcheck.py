from __future__ import annotations

import os
from typing import Optional

import requests


FACTCHECK_API = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def get_veracity_score(claim: str, api_key: Optional[str] = None, timeout_s: float = 6.0) -> float:
    """Return a simple veracity score in [0,1] using Google Fact Check Tools.

    Heuristic mapping:
      - textualRating contains "true" => 1.0
      - textualRating contains "false" => 0.0
      - otherwise => 0.5

    Falls back to 0.5 on errors or when no claims are found.
    """
    if not claim or not claim.strip():
        return 0.5

    # Read from function arg or environment variable GOOGLE_FACTCHECK_API_KEY
    key = api_key or os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not key or key == "your_api_key_here":
        print("Warning: Google Factcheck API key not configured")
        return 0.5

    try:
        params = {"query": claim, "key": key}
        resp = requests.get(FACTCHECK_API, params=params, timeout=timeout_s)
        if resp.status_code != 200:
            return 0.5
        data = resp.json() or {}
        claims = data.get("claims") or []
        if not claims:
            return 0.5
        # Take the first review of the top claim
        reviews = claims[0].get("claimReview") or []
        if not reviews:
            return 0.5
        rating = str(reviews[0].get("textualRating", "")).lower()
        if "true" in rating:
            return 1.0
        if "false" in rating:
            return 0.0
        return 0.5
    except Exception:
        return 0.5


