"""
Pipeline Monitor & Opportunity Coordinator.
Coordinates scanning, deduplication, deadline expiration, and alert triggers.
"""

import json
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from preuni_system.config import Config
from preuni_system.crawler import OpportunityCrawler
from preuni_system.db import Database
from preuni_system.utils import is_expired, is_level_eligible, normalize_url, parse_date


def select_immediate_alert(db: Database, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """
    Pick the best opportunity for an immediate alert: active, not expired, flagged for immediate
    alerts, scoring at least ALERT_SCORE_THRESHOLD, open to the student's current study level,
    and never alerted before. Returns None when nothing qualifies.
    """
    alerted_urls, alerted_ids = db.get_alerted_keys()
    candidates = [
        opp for opp in db.get_active_opportunities()
        if opp.get("is_immediate_alert")
        and (opp.get("total_score") or 0) >= Config.ALERT_SCORE_THRESHOLD
        and not is_expired(opp.get("deadline"), today)
        and is_level_eligible(opp.get("min_level"), opp.get("max_level"))
        and opp["id"] not in alerted_ids
        and normalize_url(opp["url"]) not in alerted_urls
    ]
    # Highest score first; among equal scores, the soonest known deadline first
    candidates.sort(key=lambda opp: (-(opp.get("total_score") or 0), parse_date(opp.get("deadline")) or date.max))
    return candidates[0] if candidates else None


class OpportunityMonitor:
    """Monitors live opportunities, purges expired records, and identifies immediate alerts."""

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.crawler = OpportunityCrawler()

    def run_pipeline(self) -> Dict[str, Any]:
        """
        Execute full monitoring workflow:
        1. Scan live sources and registries
        2. Deduplicate against database
        3. Insert new validated opportunities
        4. Purge or deactivate expired deadlines
        5. Identify immediate alerts
        """
        stats = {
            "scanned": 0,
            "new_inserted": 0,
            "expired_deactivated": 0,
            "immediate_alerts": [],
            "timestamp": datetime.now().isoformat(),
        }

        # 1. Purge / Deactivate Expired Items
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, deadline FROM opportunities WHERE is_active = 1 AND deadline IS NOT NULL")
            active_items = cursor.fetchall()
            for item in active_items:
                if is_expired(item["deadline"]):
                    cursor.execute("UPDATE opportunities SET is_active = 0 WHERE id = ?", (item["id"],))
                    stats["expired_deactivated"] += 1
            conn.commit()

        # 2. Ingest New Opportunities
        new_items = self.crawler.scan_all_sources()
        stats["scanned"] = len(new_items)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            for opp in new_items:
                # Check if already exists
                cursor.execute("SELECT id FROM opportunities WHERE id = ? OR url = ?", (opp["id"], opp["url"]))
                existing = cursor.fetchone()
                if existing:
                    continue

                cursor.execute("""
                INSERT INTO opportunities (
                    id, title, organizer, category, url, description, location,
                    date, deadline, cost, eligibility, geographic_priority, scores_json,
                    total_score, is_immediate_alert, is_active, tags_json, created_at,
                    min_level, max_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp["id"], opp["title"], opp["organizer"], opp["category"],
                    opp["url"], opp.get("description", ""), opp.get("location", ""),
                    opp.get("date", ""), opp.get("deadline"), opp.get("cost", "Free"),
                    opp.get("eligibility", ""), opp.get("geographic_priority", "A"),
                    json.dumps(opp.get("scores", {})), opp.get("total_score", 80),
                    1 if opp.get("is_immediate_alert") else 0,
                    1 if opp.get("is_active", True) else 0,
                    json.dumps(opp.get("tags", [])), opp.get("created_at", ""),
                    opp.get("min_level", "unknown"), opp.get("max_level")
                ))
                stats["new_inserted"] += 1

                if opp.get("is_immediate_alert"):
                    stats["immediate_alerts"].append(opp)

            conn.commit()

        return stats
