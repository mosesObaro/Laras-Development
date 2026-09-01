"""
Pipeline Monitor & Opportunity Coordinator.
Coordinates scanning, deduplication, deadline expiration, and alert triggers.
"""

import json
from datetime import datetime, date
from typing import Dict, List, Any
from preuni_system.config import Config
from preuni_system.crawler import OpportunityCrawler
from preuni_system.db import Database
from preuni_system.utils import is_expired


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
                    total_score, is_immediate_alert, is_active, tags_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp["id"], opp["title"], opp["organizer"], opp["category"],
                    opp["url"], opp.get("description", ""), opp.get("location", ""),
                    opp.get("date", ""), opp.get("deadline"), opp.get("cost", "Free"),
                    opp.get("eligibility", ""), opp.get("geographic_priority", "A"),
                    json.dumps(opp.get("scores", {})), opp.get("total_score", 80),
                    1 if opp.get("is_immediate_alert") else 0,
                    1 if opp.get("is_active", True) else 0,
                    json.dumps(opp.get("tags", [])), opp.get("created_at", "")
                ))
                stats["new_inserted"] += 1

                if opp.get("is_immediate_alert"):
                    stats["immediate_alerts"].append(opp)

            conn.commit()

        return stats
