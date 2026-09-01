"""
Opportunity Quality & Safety Scoring Engine.
Implements the 8-factor mathematical scoring model, safety risk filters, and soft-skill rubrics.
"""

from typing import Dict, Any, Tuple
from preuni_system.config import Config


class OpportunityScorer:
    """Calculates multidimensional quality scores and performs safety checks."""

    WEIGHTS = Config.SCORING_WEIGHTS

    @classmethod
    def calculate_quality_score(cls, sub_scores: Dict[str, int]) -> Tuple[int, str]:
        """
        Calculate weighted score (0-100) and return (score, recommendation_tier).
        Sub-scores dictionary:
          - relevance: 0-100 (25%)
          - credibility: 0-100 (20%)
          - educational_value: 0-100 (20%)
          - cost_value: 0-100 (10%)
          - accessibility: 0-100 (10%)
          - age_suitability: 0-100 (5%)
          - time_commitment: 0-100 (5%)
          - networking: 0-100 (5%)
        """
        total = 0.0
        for key, weight in cls.WEIGHTS.items():
            val = float(sub_scores.get(key, 70))
            # Clamp value between 0 and 100
            val = max(0.0, min(100.0, val))
            total += val * weight

        final_score = int(round(total))

        if final_score >= Config.ALERT_SCORE_THRESHOLD:
            recommendation = "STRONGLY RECOMMENDED"
        elif final_score >= Config.CONSIDER_SCORE_THRESHOLD:
            recommendation = "CONSIDER"
        else:
            recommendation = "SUPPRESSED"

        return final_score, recommendation

    @classmethod
    def evaluate_safety(cls, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform safety and legitimacy audit for teenager opportunities.
        Returns safety assessment dictionary.
        """
        title = opportunity_data.get("title", "").lower()
        desc = opportunity_data.get("description", "").lower()
        org = opportunity_data.get("organization", opportunity_data.get("organizer", "")).lower()
        cost = opportunity_data.get("cost", "").lower()

        red_flags = []
        is_safe = True

        # Clinical procedure safety check: Teenager must NOT perform invasive procedures
        clinical_keywords = ["inject", "surgery", "draw blood", "prescribe", "cannula", "administer drugs", "clinical diagnosis"]
        if any(w in desc or w in title for w in clinical_keywords):
            red_flags.append("Involves potential unsupervised clinical or invasive medical procedures inappropriate for pre-university student.")
            is_safe = False

        # Financial scam / upfront payment check
        if "pay fee to volunteer" in desc or "registration fee for interview" in desc or "crypto" in desc or "forex" in desc:
            red_flags.append("Requests suspicious payment for volunteering or employment.")
            is_safe = False

        # Unverified contact / meeting check
        if "private meetup" in desc or "hotel room" in desc or "direct whatsapp only" in desc:
            red_flags.append("Unverified or private 1-on-1 meeting location.")
            is_safe = False

        # Known credible organizers boost safety
        credible_orgs = [
            "world health organization", "who", "unicef", "un", "khan academy", "coursera",
            "edx", "openlearn", "alison", "nigerian red cross", "ubth", "uniben",
            "girls power initiative", "gpi", "jci", "rotaract", "british council",
            "mtn foundation", "nnpc", "seplat", "edo state"
        ]
        is_known_credible = any(c in org for c in credible_orgs)

        safety_score = 100
        if red_flags:
            safety_score = max(0, 100 - (len(red_flags) * 40))
        elif is_known_credible:
            safety_score = 98

        return {
            "is_safe": is_safe,
            "safety_score": safety_score,
            "red_flags": red_flags,
            "parental_consent_recommended": True,
            "is_known_credible": is_known_credible,
        }

    @classmethod
    def score_course(cls, relevance: int, quality: int, practical: int, accessibility: int, career: int) -> Dict[str, Any]:
        """Compute structured multi-factor score for a course."""
        total = int(round((relevance * 0.25) + (quality * 0.25) + (practical * 0.25) + (accessibility * 0.15) + (career * 0.10)))
        return {
            "relevance": relevance,
            "quality": quality,
            "practical_value": practical,
            "accessibility": accessibility,
            "career_value": career,
            "total_score": total,
            "recommendation": "STRONGLY RECOMMENDED" if total >= 85 else ("CONSIDER" if total >= 70 else "SUPPRESSED"),
        }
