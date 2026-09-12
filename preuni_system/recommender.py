"""
Personalized Learning Opportunity Recommender Engine.
Ranks and categorizes newly discovered educational opportunities and courses into:
1. "Learn Now" (Immediate match for current week's topics & objectives)
2. "Good Long-Term Match" (Strategic alignment with future modules & UNIBEN degree requirements)
"""

import re
from datetime import datetime, date
from typing import Dict, List, Set, Optional, Any, Tuple
from preuni_system.config import Config
from preuni_system.models import DailyLearningFocus, OpportunityAlertMatch
from preuni_system.utils import normalize_url, compute_keyword_overlap


class PersonalizedLearningRecommender:
    """Evaluates candidates against current learning calendar and long-term milestones."""

    WEIGHTS = Config.DAILY_RELEVANCE_WEIGHTS

    def __init__(self, config: Config = Config):
        self.config = config

    def evaluate_resource(
        self,
        item: Dict[str, Any],
        learning_focus: DailyLearningFocus,
        upcoming_keywords: List[str],
        already_alerted_urls: Set[str],
        completed_urls: Set[str],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate a single learning opportunity across all relevance factors.
        Returns evaluation metrics and candidate classification.
        """
        raw_url = item.get("url", "")
        norm_url = normalize_url(raw_url)
        title = item.get("title", "")
        category = item.get("category", "")
        desc = item.get("description", "") or item.get("practical_task", "")
        combined_text = f"{title} {category} {desc}".lower()

        # 1. Duplication & Consumption Check
        is_completed = norm_url in completed_urls
        is_already_alerted = norm_url in already_alerted_urls

        if not force and (is_completed or is_already_alerted):
            return {
                "item": item,
                "is_eligible": False,
                "rejection_reason": "Already completed" if is_completed else "Already alerted",
                "learn_now_score": 0,
                "long_term_score": 0,
                "overall_score": 0,
            }

        # 2. Topic Match Score (Current Week)
        topic_text = f"{learning_focus.topic} {learning_focus.subject}".lower()
        topic_words = [w for w in re.split(r"\W+", topic_text) if len(w) > 3]

        # Check keyword matches
        kw_matches = 0
        for w in topic_words:
            if w in combined_text:
                kw_matches += 1
        kw_ratio = (kw_matches / max(1, len(topic_words))) if topic_words else 0.0

        # Check subject category match
        subject_first = learning_focus.subject.lower().split()[0]
        has_subject_in_cat = subject_first in category.lower()
        has_subject_in_title = subject_first in title.lower()
        subject_match = has_subject_in_cat or has_subject_in_title

        # Check core objectives
        obj_matches = 0
        for obj in learning_focus.weekly_objectives:
            obj_words = [w for w in re.split(r"\W+", obj.lower()) if len(w) > 4]
            if any(w in combined_text for w in obj_words):
                obj_matches += 1
        obj_ratio = (obj_matches / max(1, len(learning_focus.weekly_objectives))) if learning_focus.weekly_objectives else 0.0

        # Compute balanced topic match score
        topic_score_calc = 0.0
        if kw_matches > 0:
            topic_score_calc += min(60.0, kw_matches * 25.0)
        if subject_match:
            topic_score_calc += 35.0
        if obj_ratio > 0:
            topic_score_calc += (obj_ratio * 25.0)

        # Bonus for exact key phrase in title
        for phrase in [learning_focus.topic.lower(), learning_focus.subject.lower()]:
            if phrase in combined_text:
                topic_score_calc += 20.0

        topic_match_score = min(100.0, max(0.0, topic_score_calc))

        # 3. Module & Phase Match Score
        recommended_m = item.get("recommended_month", 1)
        if recommended_m == learning_focus.month:
            module_match_score = 95.0
        elif abs(recommended_m - learning_focus.month) == 1:
            module_match_score = 80.0
        elif recommended_m > learning_focus.month:
            module_match_score = max(50.0, 85.0 - (abs(recommended_m - learning_focus.month) * 5.0))
        else:
            module_match_score = max(40.0, 75.0 - (abs(recommended_m - learning_focus.month) * 8.0))

        # 4. Field & Target University Match Score
        field_score = 70.0
        healthcare_kws = ["health", "biology", "chemistry", "physics", "medicine", "nursing", "anatomy", "physiology", "public health", "pharmacy", "biochemistry", "medical", "science"]
        if any(k in combined_text for k in healthcare_kws):
            field_score += 20.0
        if "uniben" in combined_text or "edo" in combined_text or "nigeria" in combined_text:
            field_score += 10.0
        field_match_score = min(100.0, field_score)

        # 5. Long-Term Roadmap Fit Score
        # Matches future modules or general pre-med requirements
        long_term_score_calc = 50.0
        if recommended_m > learning_focus.month:
            long_term_score_calc += min(35.0, (recommended_m - learning_focus.month) * 8.0)

        future_kws = ["pathology", "pharmacology", "immunology", "research", "cbt", "post-utme", "genetics", "biomolecules", "microbiology", "biochemistry", "scholarship"]
        if any(k in combined_text for k in future_kws):
            long_term_score_calc += 20.0

        if upcoming_keywords:
            up_match = 0
            for ukw in upcoming_keywords:
                if ukw.lower() in combined_text:
                    up_match += 1
            if up_match > 0:
                long_term_score_calc += min(20.0, up_match * 5.0)

        long_term_score = min(100.0, long_term_score_calc)

        # 6. Quality & Credibility Score
        quality_score = float(item.get("total_score", 80))

        # 7. Recency Score
        recency_score = 85.0
        created_at = item.get("created_at")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", ""))
                age_days = (datetime.now() - dt).days
                if age_days <= 7:
                    recency_score = 100.0
                elif age_days <= 30:
                    recency_score = 90.0
            except Exception:
                pass

        # Compute Total Weighted Score
        w = self.WEIGHTS
        overall_score = int(round(
            (topic_match_score * w["topic_match"]) +
            (module_match_score * w["module_match"]) +
            (field_match_score * w["field_match"]) +
            (long_term_score * w["long_term_fit"]) +
            (quality_score * w["quality"]) +
            (recency_score * w["recency"])
        ))

        # Build Dynamic Explanations
        why_matches = f"Covers {learning_focus.subject} concepts aligned with this week's focus on {learning_focus.topic}."
        if topic_match_score >= 70:
            why_matches = f"Directly addresses this week's core focus on '{learning_focus.topic}' with practical modules."
        elif subject_match:
            why_matches = f"Strengthens foundational {learning_focus.subject} mastery for this month's curriculum milestone."

        where_fits = f"Provides strategic preparation for future modules in {learning_focus.phase.split(':')[0]} and UNIBEN degree coursework."
        if recommended_m > learning_focus.month:
            where_fits = f"Prepares for Month {recommended_m} curriculum milestones and UNIBEN {self.config.TARGET_FIELD} requirements."

        return {
            "item": item,
            "is_eligible": True,
            "topic_match_score": int(topic_match_score),
            "module_match_score": int(module_match_score),
            "field_match_score": int(field_match_score),
            "long_term_score": int(long_term_score),
            "quality_score": int(quality_score),
            "overall_score": overall_score,
            "why_matches": why_matches,
            "where_fits": where_fits,
        }

    def rank_and_select_recommendations(
        self,
        candidates: List[Dict[str, Any]],
        learning_focus: DailyLearningFocus,
        upcoming_keywords: List[str],
        already_alerted_urls: Set[str],
        completed_urls: Set[str],
        max_learn_now: int = 2,
        max_long_term: int = 1,
        min_relevance_score: int = 65,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Rank all candidate resources and select top Learn Now and Long-Term opportunities.
        """
        evaluated = []
        for cand in candidates:
            res = self.evaluate_resource(
                cand,
                learning_focus,
                upcoming_keywords,
                already_alerted_urls,
                completed_urls,
                force=force
            )
            if res["is_eligible"]:
                evaluated.append(res)

        # 1. Select "Learn Now" items (Strong match with current week's topic)
        # Filter for candidates with good topic match score and overall score
        learn_now_candidates = [
            e for e in evaluated
            if (e["topic_match_score"] >= 45 or e["module_match_score"] >= 75) and e["overall_score"] >= min_relevance_score
        ]
        learn_now_candidates.sort(
            key=lambda x: (x["topic_match_score"] * 1.5 + x["overall_score"]),
            reverse=True
        )

        learn_now_selected: List[OpportunityAlertMatch] = []
        selected_urls = set()

        for ev in learn_now_candidates[:max_learn_now]:
            item = ev["item"]
            norm_u = normalize_url(item["url"])
            selected_urls.add(norm_u)
            learn_now_selected.append(OpportunityAlertMatch(
                opportunity_id=item["id"],
                title=item["title"],
                provider=item.get("provider", "Verified Academy"),
                url=item["url"],
                category=item.get("category", "Course"),
                match_type="learn_now",
                relevance_score=ev["overall_score"],
                why_it_matches=ev["why_matches"],
                where_it_fits=ev["where_fits"],
                difficulty_level=item.get("difficulty", "Beginner / Pre-University"),
                estimated_time=item.get("duration", "45-60 mins"),
                cost=item.get("cost", "Free"),
                practical_task=item.get("practical_task") or item.get("description", "")
            ))

        # 2. Select "Long-Term Match" items (Strategic future fit, not in Learn Now)
        long_term_candidates = [
            e for e in evaluated
            if normalize_url(e["item"]["url"]) not in selected_urls and (e["long_term_score"] >= 45 or e["overall_score"] >= min_relevance_score)
        ]
        long_term_candidates.sort(
            key=lambda x: (x["long_term_score"] * 1.3 + x["quality_score"]),
            reverse=True
        )

        long_term_selected: List[OpportunityAlertMatch] = []
        for ev in long_term_candidates[:max_long_term]:
            item = ev["item"]
            norm_u = normalize_url(item["url"])
            selected_urls.add(norm_u)
            fit_score = int(round((ev["long_term_score"] * 0.45) + (ev["quality_score"] * 0.35) + (ev["field_match_score"] * 0.20)))
            long_term_selected.append(OpportunityAlertMatch(
                opportunity_id=item["id"],
                title=item["title"],
                provider=item.get("provider", "Verified Academy"),
                url=item["url"],
                category=item.get("category", "Course"),
                match_type="long_term",
                relevance_score=fit_score,
                why_it_matches=ev["why_matches"],
                where_it_fits=ev["where_fits"],
                difficulty_level=item.get("difficulty", "Beginner to Intermediate"),
                estimated_time=item.get("duration", "4-6 weeks"),
                cost=item.get("cost", "Free"),
                practical_task=item.get("practical_task") or item.get("description", "")
            ))

        has_new = len(learn_now_selected) > 0 or len(long_term_selected) > 0

        return {
            "learn_now": learn_now_selected,
            "long_term": long_term_selected,
            "has_new_recommendations": has_new,
            "total_evaluated": len(evaluated),
        }
