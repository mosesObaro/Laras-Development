"""
Command Line Interface (CLI) for Pre-University Development & Opportunity System.
Provides easy terminal commands for seeding, scanning, digests, alerts, reports, and local dashboard hosting.
"""

import argparse
import json
import sys
import http.server
import socketserver
import os
from pathlib import Path
from preuni_system.config import Config, DASHBOARD_DIR, EMAIL_OUTPUT_DIR
from preuni_system.db import Database
from preuni_system.monitor import OpportunityMonitor
from preuni_system.emailer import EmailService
from preuni_system.scorer import OpportunityScorer
from preuni_system.calendar import LearningCalendarEngine
from preuni_system.recommender import PersonalizedLearningRecommender
from preuni_system.utils import format_naira, generate_hash_id, normalize_url


def cmd_seed(args):
    """Seed SQLite database from JSON files."""
    db = Database()
    stats = db.seed_from_json()
    print("==================================================")
    print("✅ DATABASE SEEDED SUCCESSFULLY")
    print("==================================================")
    for k, v in stats.items():
        print(f"  • {k.capitalize()}: {v} records loaded")
    print("==================================================")


def cmd_scan(args):
    """Scan feeds for new opportunities, deduplicate, and score."""
    print("🔍 Scanning live educational feeds and registries...")
    monitor = OpportunityMonitor()
    results = monitor.run_pipeline()
    print("==================================================")
    print("📊 OPPORTUNITY SCAN COMPLETE")
    print("==================================================")
    print(f"  • Items Scanned: {results['scanned']}")
    print(f"  • New Inserted: {results['new_inserted']}")
    print(f"  • Expired Deactivated: {results['expired_deactivated']}")
    print(f"  • Immediate Alerts (Score >= 85): {len(results['immediate_alerts'])}")
    print("==================================================")
    for alert in results["immediate_alerts"]:
        print(f"🚨 [ALERT {alert['total_score']}/100] {alert['title']} ({alert['category']})")
        print(f"   Deadline: {alert.get('deadline') or 'N/A'} | URL: {alert['url']}")


def cmd_digest(args):
    """Generate and preview/send the weekly digest."""
    db = Database()
    emailer = EmailService()
    month = args.month or 1
    week = args.week or 1

    opps = db.get_top_opportunities(limit=8, min_score=70)
    courses = db.get_courses(month=month)
    reading_items = db.get_reading_items(month=month)
    reading = reading_items[0] if reading_items else None

    subject, html_body, text_body = emailer.build_weekly_digest(month, week, opps, courses, reading)
    res = emailer.dispatch_email(
        subject,
        html_body,
        text_body,
        dry_run=args.preview or not args.send,
        file_tag=f"weekly_digest_m{month}_w{week}"
    )

    print("==================================================")
    print(f"📬 WEEKLY DIGEST GENERATED: Month {month}, Week {week}")
    print("==================================================")
    print(f"  • Subject: {subject}")
    print(f"  • Mode: {res.get('mode', 'Sent via ' + ('Resend' if Config.RESEND_API_KEY else 'SMTP'))}")
    if res.get("preview_html"):
        print(f"  • Preview HTML: {res['preview_html']}")
    if res.get("preview_txt"):
        print(f"  • Preview Plaintext: {res['preview_txt']}")
    if res.get("resend_id"):
        print(f"  • Resend Message ID: {res['resend_id']}")
    print("==================================================")


def cmd_alert(args):
    """Generate immediate high-priority alert for an opportunity."""
    db = Database()
    emailer = EmailService()
    opp_id = args.id

    opp = None
    with db.get_connection() as conn:
        cursor = conn.cursor()
        if opp_id:
            cursor.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,))
        else:
            cursor.execute("SELECT * FROM opportunities WHERE total_score >= 85 ORDER BY total_score DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            opp = dict(row)

    if not opp:
        print("❌ No qualifying high-priority opportunity found.")
        return

    subject, html_body, text_body = emailer.build_immediate_alert(opp)
    res = emailer.dispatch_email(
        subject,
        html_body,
        text_body,
        dry_run=args.preview or not args.send,
        file_tag=f"alert_{opp['id']}"
    )

    print("==================================================")
    print(f"🚨 IMMEDIATE ALERT PROCESSED: {opp['title']}")
    print("==================================================")
    print(f"  • Score: {opp.get('total_score')}/100")
    print(f"  • Subject: {subject}")
    if res.get("preview_html"):
        print(f"  • Preview HTML: {res['preview_html']}")
    if res.get("resend_id"):
        print(f"  • Resend ID: {res['resend_id']}")
    print("==================================================")


def cmd_daily_alert(args):
    """Generate and preview/send personalized daily learning-opportunity alert driven by calendar."""
    calendar = LearningCalendarEngine()
    db = Database()
    recommender = PersonalizedLearningRecommender()
    emailer = EmailService()

    # 1. Determine Learning Focus from calendar
    focus = calendar.get_learning_focus(
        target_date=args.date,
        month=args.month,
        week=args.week
    )

    # 2. Gather candidates and history
    candidates = db.get_all_candidate_learning_resources()
    upcoming_keywords = calendar.get_upcoming_keywords(focus.global_week, lookahead_weeks=8)
    already_alerted_urls = {row["url_normalized"] for row in db.get_alert_history()}
    completed_urls = db.get_completed_course_urls()

    # 3. Rank & Categorize Recommendations
    recs = recommender.rank_and_select_recommendations(
        candidates=candidates,
        learning_focus=focus,
        upcoming_keywords=upcoming_keywords,
        already_alerted_urls=already_alerted_urls,
        completed_urls=completed_urls,
        max_learn_now=Config.MAX_LEARN_NOW_RECOMMENDATIONS,
        max_long_term=Config.MAX_LONG_TERM_RECOMMENDATIONS,
        min_relevance_score=Config.MIN_DAILY_ALERT_RELEVANCE_SCORE,
        force=args.force
    )

    learn_now = recs["learn_now"]
    long_term = recs["long_term"]

    # 4. Build and Dispatch Email
    subject, html_body, text_body = emailer.build_daily_alert(focus, learn_now, long_term)
    is_dry_run = args.preview or not args.send
    file_tag = f"daily_alert_m{focus.month}_w{focus.week_in_month}_{focus.date_str.replace('-', '')}"

    res = emailer.dispatch_email(
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        dry_run=is_dry_run,
        file_tag=file_tag
    )

    # 5. Persist Alert History if sent/dispatched (and not forced preview)
    if args.send and not args.preview:
        for item in learn_now:
            db.record_alert_history(
                opportunity_id=item.opportunity_id,
                url=item.url,
                title=item.title,
                alert_type="learn_now",
                week_number=focus.global_week,
                relevance_score=item.relevance_score,
                date_alerted=focus.date_str
            )
        for item in long_term:
            db.record_alert_history(
                opportunity_id=item.opportunity_id,
                url=item.url,
                title=item.title,
                alert_type="long_term",
                week_number=focus.global_week,
                relevance_score=item.relevance_score,
                date_alerted=focus.date_str
            )

    # 6. Terminal Summary Output
    print("==================================================")
    print(f"📚 DAILY LEARNING & OPPORTUNITY ALERT")
    print(f"   Date: {focus.date_str} • Month {focus.month}, Week {focus.week_in_month} (Week {focus.global_week}/78)")
    print(f"   Phase: {focus.phase}")
    print("==================================================")
    print(f"  • Subject: {focus.subject}")
    print(f"  • Topic: {focus.topic}")
    print(f"  • Today's Focus: {focus.daily_focus}")
    print("--------------------------------------------------")
    print(f"  🆕 LEARN NOW RECOMMENDATIONS ({len(learn_now)}):")
    if learn_now:
        for op in learn_now:
            print(f"    - [{op.relevance_score}/100] {op.title} ({op.provider})")
            print(f"      Why: {op.why_it_matches}")
            print(f"      Link: {op.url}")
    else:
        print("    - (No new external courses required today. Core focus on active recall.)")

    print("--------------------------------------------------")
    print(f"  🎯 LONG-TERM MATCH ({len(long_term)}):")
    if long_term:
        for op in long_term:
            print(f"    - [{op.relevance_score}/100] {op.title} ({op.provider})")
            print(f"      Why: {op.why_it_matches}")
            print(f"      Where: {op.where_it_fits}")
            print(f"      Link: {op.url}")
    else:
        print(f"    - ({focus.long_term_connection})")

    print("--------------------------------------------------")
    print(f"  • Mode: {res.get('mode', 'Sent via Resend' if Config.RESEND_API_KEY else 'Sent via SMTP')}")
    if res.get("preview_html"):
        print(f"  • Preview HTML: {res['preview_html']}")
    if res.get("preview_txt"):
        print(f"  • Preview Plaintext: {res['preview_txt']}")
    if res.get("resend_id"):
        print(f"  • Resend Message ID: {res['resend_id']}")
    print("==================================================")


def cmd_stats(args):
    """Display student progress and database stats."""
    db = Database()
    stats = db.get_summary_stats()
    print("==================================================")
    print(f"📊 {Config.STUDENT_NAME.upper()}'S PRE-UNIVERSITY SYSTEM OVERVIEW")
    print(f"   Target: {Config.UNIVERSITY} ({Config.TARGET_FIELD})")
    print(f"   Apprenticeship: {Config.CURRENT_APPRENTICESHIP}")
    print("==================================================")
    print(f"  • Verified Courses Database: {stats['courses_total']} total")
    print(f"    - Completed: {stats['courses_completed']} | In Progress: {stats['courses_in_progress']}")
    print(f"  • Volunteering Organizations: {stats['volunteering_orgs']} (Edo Priority)")
    print(f"    - Volunteer Hours Logged: {stats['volunteering_hours']} hrs")
    print(f"  • Healthcare Careers Explored: {stats['careers_explored']}")
    print(f"  • Active Scored Opportunities: {stats['active_opportunities']}")
    print(f"  • Tailoring Projects Completed: {stats['tailoring_projects_completed']}")
    print(f"    - Net Tailoring Profit: {format_naira(stats['tailoring_net_profit_ngn'])}")
    print("==================================================")


def cmd_serve(args):
    """Serve the static web dashboard locally."""
    port = args.port or 8000
    web_dir = DASHBOARD_DIR

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(web_dir), **kw)

    print(f"🚀 Starting Pre-University Dashboard at: http://localhost:{port}")
    print(f"📁 Serving static files from: {web_dir}")
    print("Press Ctrl+C to stop the server.")

    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Pre-University Development & Opportunity System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # seed
    subparsers.add_parser("seed", help="Seed database from verified JSON data")

    # scan
    subparsers.add_parser("scan", help="Scan feeds for new opportunities and purge expired")

    # digest
    digest_p = subparsers.add_parser("digest", help="Generate and send weekly development digest")
    digest_p.add_argument("--month", type=int, default=1, help="Curriculum Month (1-18)")
    digest_p.add_argument("--week", type=int, default=1, help="Curriculum Week (1-4)")
    digest_p.add_argument("--preview", action="store_true", help="Generate local preview files without sending")
    digest_p.add_argument("--send", action="store_true", help="Send email via Resend API / SMTP")

    # daily-alert
    daily_p = subparsers.add_parser("daily-alert", help="Generate calendar-driven personalized daily learning-opportunity alert")
    daily_p.add_argument("--date", type=str, help="Target date (YYYY-MM-DD) to calculate calendar focus")
    daily_p.add_argument("--month", type=int, help="Override curriculum month (1-18)")
    daily_p.add_argument("--week", type=int, help="Override curriculum week (1-4)")
    daily_p.add_argument("--force", action="store_true", help="Force recommendations even if already alerted")
    daily_p.add_argument("--preview", action="store_true", help="Generate local preview files without sending")
    daily_p.add_argument("--send", action="store_true", help="Send email via Resend API / SMTP")

    # alert
    alert_p = subparsers.add_parser("alert", help="Generate immediate high-priority alert")
    alert_p.add_argument("--id", type=str, help="Opportunity ID")
    alert_p.add_argument("--preview", action="store_true", help="Generate preview only")
    alert_p.add_argument("--send", action="store_true", help="Send email via Resend API / SMTP")

    # stats
    subparsers.add_parser("stats", help="Display student progress overview")

    # serve
    serve_p = subparsers.add_parser("serve", help="Start local web server for dashboard")
    serve_p.add_argument("--port", type=int, default=8000, help="Port to listen on")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "seed": cmd_seed,
        "scan": cmd_scan,
        "digest": cmd_digest,
        "daily-alert": cmd_daily_alert,
        "alert": cmd_alert,
        "stats": cmd_stats,
        "serve": cmd_serve,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)


if __name__ == "__main__":
    main()
