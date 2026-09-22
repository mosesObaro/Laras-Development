"""
Bundles all verified JSON datasets into dashboard/data.js for standalone GitHub Pages hosting,
and renders this week's emails into dashboard/emails/ for the dashboard's Emails tab.
"""

import json
import tempfile
from datetime import date
from pathlib import Path

from preuni_system.calendar import LearningCalendarEngine
from preuni_system.config import Config
from preuni_system.db import Database
from preuni_system.emailer import EmailService
from preuni_system.monitor import select_immediate_alert, split_digest_opportunities
from preuni_system.recommender import recommend_for_focus

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DASHBOARD_DIR = BASE_DIR / "dashboard"
EMAIL_PREVIEW_DIR = DASHBOARD_DIR / "emails"


def render_email_previews(out_dir: Path = EMAIL_PREVIEW_DIR) -> None:
    """Render this week's daily alert, weekly digest and immediate alert with the real email templates."""
    out_dir.mkdir(parents=True, exist_ok=True)
    emailer = EmailService()
    calendar = LearningCalendarEngine()
    focus = calendar.get_learning_focus()

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(db_path=Path(tmp) / "preview.sqlite3")
        db.seed_from_json()

        recs = recommend_for_focus(db, calendar, focus, already_alerted_urls=set())
        _, daily_html, _ = emailer.build_daily_alert(focus, recs["learn_now"], recs["long_term"])

        open_now, plan_ahead, deadlines = split_digest_opportunities(db)
        reading_items = db.get_reading_items(month=focus.month)
        _, digest_html, _ = emailer.build_weekly_digest(
            focus.month, focus.week_in_month, open_now, db.get_courses(month=focus.month),
            reading_items[0] if reading_items else None,
            focus=focus, plan_ahead=plan_ahead[:3], deadlines=deadlines[:3]
        )

        opp = select_immediate_alert(db)
        if opp:
            _, alert_html, _ = emailer.build_immediate_alert(opp)
        else:
            alert_html = ('<p style="padding:20px;font-family:sans-serif;">No immediate alert this week: '
                          "no high-scoring opportunity is open to the student's current study level.</p>")

    for name, html in (("daily_alert", daily_html), ("weekly_digest", digest_html), ("immediate_alert", alert_html)):
        (out_dir / f"{name}.html").write_text(html, encoding="utf-8")


def bundle():
    data = {}
    for json_file in DATA_DIR.glob("*.json"):
        key = json_file.stem
        with open(json_file, "r", encoding="utf-8") as f:
            data[key] = json.load(f)

    js_content = f"""/**
 * Pre-University Development & Opportunity System
 * Bundled Dataset for GitHub Pages & Offline Web Application
 * Auto-generated from data/ directory
 */

window.PREUNI_CONFIG = {{
  student_name: "Lara",
  student_email: "lara@example.com",
  parent_email: "parent@example.com",
  country: "Nigeria",
  state: "Edo State",
  city: "Benin City",
  university: "University of Benin (UNIBEN)",
  target_field: "Healthcare / Medical Sciences",
  primary_career: "Nursing Science",
  apprenticeship: "Tailoring & Fashion Design",
  target_date: "October 2027",
  timezone: "Africa/Lagos",
  student_level: {json.dumps(Config.STUDENT_LEVEL)},
  previews_generated: {json.dumps(date.today().isoformat())}
}};

window.PREUNI_DATA = {json.dumps(data, indent=2)};
"""
    out_file = DASHBOARD_DIR / "data.js"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"✅ Successfully bundled all datasets into {out_file}")

    render_email_previews()
    print(f"✅ Rendered this week's email previews into {EMAIL_PREVIEW_DIR}")


if __name__ == "__main__":
    bundle()
