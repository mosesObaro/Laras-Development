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
from preuni_system.monitor import OpportunityMonitor, select_immediate_alert, split_digest_opportunities
from preuni_system.emailer import EmailService
from preuni_system.scorer import OpportunityScorer
from preuni_system.calendar import LearningCalendarEngine
from preuni_system.recommender import recommend_for_focus
from preuni_system.utils import format_naira, generate_hash_id, normalize_url


def _was_sent(res: dict) -> bool:
    """True only when an email actually left the system (not a preview or dry run)."""
    return bool(res.get("success")) and not res.get("mode")


def _report_dispatch(res: dict) -> None:
    """Print how an email was handled; exit non-zero if sending failed so scheduled runs show as failed."""
    if res.get("mode"):
        print(f"  • Mode: {res['mode']}")
    elif res.get("success"):
        print(f"  • Mode: Sent via {'Resend' if res.get('resend_id') else 'SMTP'}")
    if res.get("preview_html"):
        print(f"  • Preview HTML: {res['preview_html']}")
    if res.get("preview_txt"):
        print(f"  • Preview Plaintext: {res['preview_txt']}")
    if res.get("resend_id"):
        print(f"  • Resend Message ID: {res['resend_id']}")
    print("==================================================")
    if not res.get("success"):
        print(f"❌ EMAIL NOT SENT: {res.get('error', 'unknown error')}")
        sys.exit(1)


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
    """Generate and preview/send the weekly digest for the current calendar week (or --month/--week)."""
    db = Database()
    emailer = EmailService()
    focus = LearningCalendarEngine().get_learning_focus(month=args.month, week=args.week)
    month, week = focus.month, focus.week_in_month

    open_now, plan_ahead, deadlines = split_digest_opportunities(db)
    courses = db.get_courses(month=month)
    reading_items = db.get_reading_items(month=month)
    reading = reading_items[0] if reading_items else None

    subject, html_body, text_body = emailer.build_weekly_digest(
        month, week, open_now, courses, reading,
        focus=focus, plan_ahead=plan_ahead[:3], deadlines=deadlines[:3]
    )
    res = emailer.dispatch_email(
        subject,
        html_body,
        text_body,
        dry_run=args.preview or not args.send,
        file_tag=f"weekly_digest_m{month}_w{week}"
    )

    print("==================================================")
    print(f"📬 WEEKLY DIGEST GENERATED: Month {month}, Week {week} (Week {focus.global_week}/78)")
    print("==================================================")
    print(f"  • Subject: {subject}")
    print(f"  • Opportunities open now: {len(open_now)} | Plan ahead: {len(plan_ahead)}")
    _report_dispatch(res)


def cmd_alert(args):
    """Send one immediate alert for the best new opportunity the student can apply to now (never repeats)."""
    db = Database()
    emailer = EmailService()

    opp = db.get_opportunity(args.id) if args.id else select_immediate_alert(db)
    if not opp:
        print("✅ No new eligible high-priority opportunity to alert. Nothing sent.")
        return

    subject, html_body, text_body = emailer.build_immediate_alert(opp)
    res = emailer.dispatch_email(
        subject,
        html_body,
        text_body,
        dry_run=args.preview or not args.send,
        file_tag=f"alert_{opp['id']}"
    )

    # Record the alert only once it has really been sent, so it is never sent again
    if _was_sent(res):
        db.record_alert_history(
            opportunity_id=opp["id"],
            url=opp["url"],
            title=opp["title"],
            alert_type="immediate",
            week_number=LearningCalendarEngine().calculate_week_number(),
            relevance_score=opp.get("total_score") or 0
        )

    print("==================================================")
    print(f"🚨 IMMEDIATE ALERT PROCESSED: {opp['title']}")
    print("==================================================")
    print(f"  • Score: {opp.get('total_score')}/100")
    print(f"  • Subject: {subject}")
    _report_dispatch(res)


def cmd_daily_alert(args):
    """Generate and preview/send personalized daily learning-opportunity alert driven by calendar."""
    if args.send and not args.preview and not Config.DAILY_ALERT_ENABLED:
        print("⏸️  Daily alert is disabled (DAILY_ALERT_ENABLED=false). Nothing sent.")
        return

    calendar = LearningCalendarEngine()
    db = Database()
    emailer = EmailService()

    # 1. Determine Learning Focus from calendar
    focus = calendar.get_learning_focus(
        target_date=args.date,
        month=args.month,
        week=args.week
    )

    # 2-3. Rank & categorize this week's candidates, skipping anything already alerted
    already_alerted_urls, _ = db.get_alerted_keys()
    recs = recommend_for_focus(db, calendar, focus, already_alerted_urls, force=args.force)

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

    # 5. Persist Alert History only once the email has really been sent
    if _was_sent(res):
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
    _report_dispatch(res)


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
    digest_p.add_argument("--month", type=int, help="Override curriculum month (1-18); default is the current calendar week")
    digest_p.add_argument("--week", type=int, help="Override curriculum week (1-4)")
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
    alert_p = subparsers.add_parser("alert", help="Send one alert for the best new opportunity open to the student now")
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
