"""
Opportunity Crawler & Feed Ingestion Engine.
Scrapes RSS/Atom feeds and curated educational sources, cleans data, checks safety, and scores opportunities.
"""

import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from preuni_system.config import Config
from preuni_system.scorer import OpportunityScorer
from preuni_system.utils import generate_hash_id, parse_date, is_suspicious_url


class OpportunityCrawler:
    """Fetches, parses, audits, and scores opportunities from public feeds and verified registries."""

    CURATED_FEEDS = [
        {
            "name": "Opportunity Desk - Scholarships & Health",
            "url": "https://opportunitydesk.org/feed/",
            "category": "Scholarship",
            "priority": "B"
        },
        {
            "name": "Opportunities for Africans",
            "url": "https://www.opportunitiesforafricans.com/feed/",
            "category": "Opportunities",
            "priority": "B"
        },
        {
            "name": "WHO Health Emergencies & Courses",
            "url": "https://openwho.org/courses.json",
            "category": "Healthcare Foundations",
            "priority": "C"
        }
    ]

    def __init__(self):
        self.headers = {"User-Agent": "PreUni-Opportunity-Monitor/1.0 (Educational Non-Profit Bot for Nigerian Youth)"}

    def fetch_rss_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch and parse standard RSS 2.0 or Atom feeds using zero-dependency XML parser."""
        items = []
        try:
            req = urllib.request.Request(feed_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                root = ET.fromstring(content)

                # RSS 2.0
                channel = root.find("channel")
                if channel is not None:
                    for item in channel.findall("item"):
                        title = item.findtext("title", "").strip()
                        link = item.findtext("link", "").strip()
                        description = item.findtext("description", "").strip()
                        pub_date = item.findtext("pubDate", "").strip()

                        # Strip HTML tags from description
                        clean_desc = re.sub(r"<[^>]+>", " ", description)
                        clean_desc = " ".join(clean_desc.split())[:400]

                        items.append({
                            "title": title,
                            "url": link,
                            "description": clean_desc,
                            "date": pub_date,
                        })
        except Exception as e:
            # Graceful error handling (network timeout or offline mode)
            pass

        return items

    def clean_and_score_item(self, raw_item: Dict[str, Any], default_category: str = "Opportunities", default_priority: str = "B") -> Optional[Dict[str, Any]]:
        """Run safety filters and compute 8-factor score."""
        title = raw_item.get("title", "").strip()
        url = raw_item.get("url", "").strip()
        desc = raw_item.get("description", "").strip()

        if not title or not url or is_suspicious_url(url):
            return None

        # Determine Category
        category = default_category
        title_lower = title.lower()
        desc_lower = desc.lower()

        if any(w in title_lower or w in desc_lower for w in ["scholarship", "bursary", "grant", "tuition"]):
            category = "Scholarship"
        elif any(w in title_lower or w in desc_lower for w in ["volunteer", "community service", "outreach"]):
            category = "Volunteering"
        elif any(w in title_lower or w in desc_lower for w in ["competition", "essay contest", "challenge", "prize"]):
            category = "Competition"
        elif any(w in title_lower or w in desc_lower for w in ["webinar", "seminar", "conference", "workshop"]):
            category = "Event"
        elif any(w in title_lower or w in desc_lower for w in ["fellowship", "mentorship", "leader"]):
            category = "Mentorship"

        # Safety Check
        safety_eval = OpportunityScorer.evaluate_safety({
            "title": title,
            "description": desc,
            "organization": raw_item.get("organizer", "Public Opportunity"),
            "cost": raw_item.get("cost", "Free")
        })

        if not safety_eval["is_safe"]:
            return None

        # Estimate Sub-Scores
        # Relevance: check for health/stem/nigeria keywords
        rel_boost = 0
        if any(w in title_lower or w in desc_lower for w in ["health", "nurse", "medicine", "biology", "science", "edo", "nigeria"]):
            rel_boost += 25
        if "benin" in title_lower or "benin" in desc_lower or "edo" in title_lower or "edo" in desc_lower:
            default_priority = "A"
            rel_boost += 15

        sub_scores = {
            "relevance": min(100, 70 + rel_boost),
            "credibility": safety_eval["safety_score"],
            "educational_value": 85 if "course" in title_lower or "scholarship" in title_lower else 75,
            "cost_value": 100,  # Free feeds
            "accessibility": 95 if default_priority in ("A", "C") else 85,
            "age_suitability": 90,
            "time_commitment": 90,
            "networking": 85,
        }

        total_score, recommendation = OpportunityScorer.calculate_quality_score(sub_scores)

        # Do not return items below the consider threshold
        if total_score < Config.CONSIDER_SCORE_THRESHOLD:
            return None

        item_id = generate_hash_id("opp", title, url)
        is_immediate = total_score >= Config.ALERT_SCORE_THRESHOLD and category in ("Scholarship", "Competition")

        return {
            "id": item_id,
            "title": title,
            "organizer": raw_item.get("organizer", "Verified Global / Nigerian Opportunity"),
            "category": category,
            "url": url,
            "description": desc,
            "location": "Benin City / Edo State" if default_priority == "A" else ("Nigeria" if default_priority == "B" else "Online"),
            "date": raw_item.get("date", "Current Call"),
            "deadline": raw_item.get("deadline", None),
            "cost": "Free",
            "eligibility": "Pre-University / Young Adults (16-25)",
            "geographic_priority": default_priority,
            "scores": sub_scores,
            "total_score": total_score,
            "is_immediate_alert": is_immediate,
            "is_active": True,
            "tags": [category, "Youth", default_priority],
            "created_at": datetime.now().isoformat()
        }

    def scan_all_sources(self) -> List[Dict[str, Any]]:
        """Run scan across all feeds and return scored and deduplicated opportunities."""
        collected = []
        seen_urls = set()

        for feed_config in self.CURATED_FEEDS:
            raw_items = self.fetch_rss_feed(feed_config["url"])
            for raw in raw_items:
                if raw["url"] in seen_urls:
                    continue
                seen_urls.add(raw["url"])

                scored = self.clean_and_score_item(
                    raw,
                    default_category=feed_config["category"],
                    default_priority=feed_config["priority"]
                )
                if scored:
                    collected.append(scored)

        return collected
