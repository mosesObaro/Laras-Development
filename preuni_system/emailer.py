"""
Email Notification & Delivery Engine.
Sends responsive HTML/plaintext emails via Resend API or SMTP, and writes local preview files.
"""

import json
import smtplib
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from preuni_system.config import Config, EMAIL_OUTPUT_DIR, TEMPLATES_DIR
from preuni_system.models import DailyLearningFocus, OpportunityAlertMatch


class EmailService:
    """Handles email generation and dispatch via Resend REST API or SMTP."""

    def __init__(self, config: Config = Config):
        self.config = config
        self.resend_api_key = config.RESEND_API_KEY
        self.resend_api_url = config.RESEND_API_URL
        self.from_email = config.RESEND_FROM_EMAIL

    def send_via_resend(self, to_emails: List[str], subject: str, html_body: str, text_body: str) -> Dict[str, Any]:
        """Send email via Resend REST API (https://api.resend.com/emails)."""
        if not self.resend_api_key:
            return {"success": False, "error": "RESEND_API_KEY is not set"}

        payload = {
            "from": self.from_email,
            "to": to_emails,
            "subject": subject,
            "html": html_body,
            "text": text_body,
        }

        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PreUni-Development-System/1.0",
        }

        try:
            req = urllib.request.Request(
                self.resend_api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                return {"success": True, "resend_id": res_data.get("id"), "data": res_data}
        except urllib.error.HTTPError as e:
            error_msg = e.read().decode("utf-8")
            return {"success": False, "error": f"HTTP {e.code}: {error_msg}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_via_smtp(self, to_emails: List[str], subject: str, html_body: str, text_body: str) -> Dict[str, Any]:
        """Fallback SMTP delivery."""
        if not self.config.SMTP_PASSWORD:
            return {"success": False, "error": "SMTP_PASSWORD is not configured"}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.SMTP_FROM_EMAIL
        msg["To"] = ", ".join(to_emails)

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT, timeout=15) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                server.sendmail(self.config.SMTP_FROM_EMAIL, to_emails, msg.as_string())
            return {"success": True, "method": "smtp"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def dispatch_email(self, subject: str, html_body: str, text_body: str, to_emails: Optional[List[str]] = None, dry_run: bool = False, file_tag: str = "email") -> Dict[str, Any]:
        """
        Dispatches email using Resend API (or SMTP fallback), and always saves a local HTML copy.
        """
        recipients = to_emails or [self.config.PARENT_EMAIL, self.config.STUDENT_EMAIL]

        # 1. Save local preview file
        safe_tag = file_tag.replace(" ", "_").lower()
        html_file = EMAIL_OUTPUT_DIR / f"{safe_tag}.html"
        txt_file = EMAIL_OUTPUT_DIR / f"{safe_tag}.txt"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_body)
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text_body)

        if dry_run or (not self.resend_api_key and not self.config.SMTP_PASSWORD):
            return {
                "success": True,
                "mode": "dry_run / preview",
                "preview_html": str(html_file),
                "preview_txt": str(txt_file),
                "recipients": recipients,
                "subject": subject,
            }

        # Try Resend first
        if self.resend_api_key:
            res = self.send_via_resend(recipients, subject, html_body, text_body)
            res["preview_file"] = str(html_file)
            return res

        # Try SMTP fallback
        return self.send_via_smtp(recipients, subject, html_body, text_body)

    # --- EMAIL BUILDERS ---

    def build_immediate_alert(self, opp: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generates (Subject, HTML, Plaintext) for an Immediate High-Priority Alert (Score >= 85).
        """
        score = opp.get("total_score", 85)
        title = opp.get("title", "High-Priority Opportunity")
        organizer = opp.get("organizer", "Verified Organization")
        category = opp.get("category", "Opportunity")
        deadline = opp.get("deadline") or "Not yet announced"
        location = opp.get("location", "Benin City / Nigeria")
        cost = opp.get("cost", "Free")
        eligibility = opp.get("eligibility", "Pre-University / Teenagers")
        url = opp.get("url", "#")
        desc = opp.get("description", "")

        subject = f"[PRE-UNIVERSITY ALERT] {title[:45]} — {score}/100"

        text_body = f"""=======================================================
PRE-UNIVERSITY OPPORTUNITY ALERT: {score}/100
=======================================================
STUDENT: {self.config.STUDENT_NAME} ({self.config.CITY}, {self.config.STATE})
TARGET: {self.config.UNIVERSITY} ({self.config.TARGET_FIELD})

OPPORTUNITY: {title}
ORGANIZER:   {organizer}
CATEGORY:    {category}
DEADLINE:    {deadline}
LOCATION:    {location}
COST:        {cost}
ELIGIBILITY: {eligibility}

WHY IT MATTERS:
This high-scoring opportunity directly reinforces your pre-university development goals for healthcare, academic rigor, and leadership.

DESCRIPTION:
{desc}

SAFETY & SUPERVISION:
• Parent/Guardian verification is recommended.
• No clinical invasive procedures required.

OFFICIAL REGISTRATION LINK:
{url}

-------------------------------------------------------
Pre-University Development, Career & Opportunity System
Powered by Resend Email Delivery Engine
"""

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
  .header {{ background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; padding: 24px; text-align: left; }}
  .badge {{ display: inline-block; background: #38bdf8; color: #082f49; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; margin-bottom: 8px; }}
  .score-badge {{ background: #22c55e; color: #ffffff; font-weight: 800; font-size: 14px; padding: 4px 12px; border-radius: 9999px; float: right; }}
  .content {{ padding: 24px; }}
  .meta-grid {{ background: #f1f5f9; border-radius: 8px; padding: 16px; margin: 16px 0; }}
  .meta-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
  .meta-row:last-child {{ border-bottom: none; }}
  .meta-label {{ color: #64748b; font-weight: 600; }}
  .meta-val {{ color: #0f172a; font-weight: 700; text-align: right; }}
  .btn {{ display: block; background: #0284c7; color: #ffffff !important; text-decoration: none; text-align: center; font-weight: 700; font-size: 16px; padding: 14px 20px; border-radius: 8px; margin: 24px 0 16px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="badge">Immediate High-Priority Alert</span>
    <span class="score-badge">{score}/100</span>
    <h2 style="margin: 8px 0 0; font-size: 20px; line-height: 1.3;">{title}</h2>
  </div>
  <div class="content">
    <p style="font-size: 15px; line-height: 1.6; color: #334155;">
      A verified high-quality opportunity scoring <strong>{score}/100</strong> has been identified for <strong>{self.config.STUDENT_NAME}</strong> in preparation for <strong>{self.config.UNIVERSITY}</strong> ({self.config.TARGET_FIELD}).
    </p>

    <div class="meta-grid">
      <div class="meta-row"><span class="meta-label">Organizer:</span><span class="meta-val">{organizer}</span></div>
      <div class="meta-row"><span class="meta-label">Category:</span><span class="meta-val">{category}</span></div>
      <div class="meta-row"><span class="meta-label">Deadline:</span><span class="meta-val" style="color: #dc2626;">{deadline}</span></div>
      <div class="meta-row"><span class="meta-label">Location:</span><span class="meta-val">{location}</span></div>
      <div class="meta-row"><span class="meta-label">Cost:</span><span class="meta-val" style="color: #16a34a;">{cost}</span></div>
      <div class="meta-row"><span class="meta-label">Eligibility:</span><span class="meta-val">{eligibility}</span></div>
    </div>

    <h3 style="font-size: 16px; color: #0f172a; margin-top: 20px;">Why It Matters:</h3>
    <p style="font-size: 14px; line-height: 1.6; color: #475569;">
      {desc}
    </p>

    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; font-size: 13px; color: #92400e; margin: 16px 0;">
      <strong>Safety Notice:</strong> Always confirm application details with a parent/guardian. This opportunity involves zero unsupervised clinical procedures.
    </div>

    <a href="{url}" class="btn" target="_blank">Access Official Application & Registration &rarr;</a>
  </div>
  <div class="footer">
    Pre-University Development & Opportunity System • {self.config.CITY}, {self.config.STATE}, {self.config.COUNTRY}<br>
    Delivered via Resend Email Infrastructure
  </div>
</div>
</body>
</html>
"""
        return subject, html_body, text_body

    def build_weekly_digest(
        self,
        month: int,
        week: int,
        opps: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
        reading: Optional[Dict[str, Any]] = None,
        focus: Optional[DailyLearningFocus] = None,
        plan_ahead: Optional[List[Dict[str, Any]]] = None,
        deadlines: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, str, str]:
        """
        Generates (Subject, HTML, Plaintext) for the 8-section Weekly Development Digest.
        `opps` are open to the student now, `plan_ahead` open later (e.g. once at university),
        `focus` is this week's calendar focus and `deadlines` are opportunities with known dates.
        """
        subject = f"[THIS WEEK'S DEVELOPMENT DIGEST] Month {month}, Week {week} — UNIBEN Pre-University Track"
        plan_ahead = plan_ahead or []
        deadlines = deadlines or []

        # This week's focus and challenge come from the learning calendar when available
        if focus:
            focus_title = focus.topic
            focus_points = focus.weekly_objectives[:3] or [focus.daily_focus]
            challenge = focus.recommended_assignment or focus.daily_focus
        else:
            focus_title = "Active Listening & Professional Email Communication"
            focus_points = ["Draft an inquiry email without filler words and ask 2 clarifying questions in every conversation."]
            challenge = "Annotate the blood flow pathway through the 4 heart chambers and valves."

        # Safe defaults
        reading_title = reading.get("title", "Atomic Habits") if reading else "Atomic Habits by James Clear"
        reading_author = reading.get("author", "James Clear") if reading else "James Clear"
        reading_exercise = reading.get("practical_exercise", "Apply 2-minute habit stacking rule.") if reading else "Apply 2-minute habit stacking rule."

        # Plaintext
        text_body = f"""=======================================================
THIS WEEK'S PRE-UNIVERSITY DEVELOPMENT DIGEST
Month {month} • Week {week}
=======================================================
STUDENT: {self.config.STUDENT_NAME} | TARGET: {self.config.UNIVERSITY} ({self.config.TARGET_FIELD})
APPRENTICESHIP: {self.config.CURRENT_APPRENTICESHIP}

1. 🌟 OPPORTUNITIES OPEN TO YOU NOW:
"""
        for i, op in enumerate(opps[:5], start=1):
            text_body += f"   {i}. {op.get('title')} ({op.get('organizer')}) — Score: {op.get('total_score')}/100\n      Deadline: {(op.get('deadline') or 'Not yet announced')} | Link: {op.get('url')}\n"
        if not opps:
            text_body += "   • None this week - see Plan Ahead below.\n"
        if plan_ahead:
            text_body += "\n   🗓️ PLAN AHEAD (opens once you are at university):\n"
            for op in plan_ahead:
                text_body += f"   • {op.get('title')} — {op.get('eligibility', '')}\n     Link: {op.get('url')}\n"

        text_body += f"""
2. 📚 ACTIVE COURSE FOCUS (Max 2 simultaneous):
"""
        for c in courses[:2]:
            text_body += f"   • {c.get('name')} ({c.get('provider')}) — {c.get('duration')}\n     Assignment: {c.get('practical_assignment')}\n"

        text_body += f"""
3. 🎯 THIS WEEK'S FOCUS: {focus_title}
"""
        for point in focus_points:
            text_body += f"   • {point}\n"

        text_body += f"""
4. ⚡ THIS WEEK'S PRACTICAL CHALLENGE:
   • {challenge}

5. ✂️ TAILORING APPRENTICESHIP GOAL:
   • Milestone: Calculate full unit costing (Fabric + Labor + Overhead + Margin) for your current garment project.

6. 📖 READING ASSIGNMENT:
   • Reading: {reading_title} ({reading_author})
   • Exercise: {reading_exercise}

7. 🤝 VOLUNTEERING SPOTLIGHT (Benin City / Edo Priority):
   • Nigerian Red Cross Society (Edo State Branch) / Girls' Power Initiative (Benin City).

8. 📅 UPCOMING DEADLINES:
"""
        for op in deadlines:
            text_body += f"   • {op.get('title')} — {op.get('deadline')}\n"
        if not deadlines:
            text_body += "   • No confirmed deadlines yet - check the Plan Ahead links for each scheme's next round.\n"

        text_body += """
=======================================================
Pre-University Development & Opportunity System
"""

        # HTML
        html_opps = ""
        for op in opps[:5]:
            html_opps += f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <span style="font-weight: 700; color: #0f172a; font-size: 15px;">{op.get('title')}</span>
                <span style="background: #e0f2fe; color: #0369a1; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 4px;">{op.get('total_score')}/100</span>
              </div>
              <p style="font-size: 13px; color: #64748b; margin: 4px 0 8px;">{op.get('organizer')} • <span style="color: #dc2626; font-weight: 600;">Deadline: {(op.get('deadline') or 'Not yet announced')}</span></p>
              <p style="font-size: 13px; color: #334155; margin: 0 0 8px;">{op.get('description', '')[:160]}...</p>
              <a href="{op.get('url')}" style="color: #0284c7; font-size: 13px; font-weight: 600; text-decoration: none;" target="_blank">View Details & Apply &rarr;</a>
            </div>
            """
        if not opps:
            html_opps = """
            <div class="card"><p style="margin: 0; font-size: 13px; color: #475569;">No opportunities are open to you this week - see Plan Ahead below.</p></div>
            """
        if plan_ahead:
            html_opps += """<h4 style="margin: 14px 0 8px; color: #0f172a; font-size: 14px;">🗓️ Plan Ahead (opens once you're at university)</h4>"""
            for op in plan_ahead:
                html_opps += f"""
            <div class="card">
              <strong style="font-size: 13px; color: #0f172a;">{op.get('title')}</strong>
              <p style="font-size: 12px; color: #475569; margin: 4px 0 6px;">{op.get('eligibility', '')}</p>
              <a href="{op.get('url')}" style="color: #0284c7; font-size: 12px; font-weight: 600; text-decoration: none;" target="_blank">Official page &rarr;</a>
            </div>
            """

        html_courses = ""
        for c in courses[:2]:
            html_courses += f"""
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
              <span style="font-weight: 700; color: #166534; font-size: 15px;">{c.get('name')}</span>
              <p style="font-size: 13px; color: #15803d; margin: 4px 0 6px;">Provider: <strong>{c.get('provider')}</strong> | Duration: {c.get('duration')}</p>
              <p style="font-size: 13px; color: #334155; margin: 0 0 8px;"><strong>Practical Task:</strong> {c.get('practical_assignment')}</p>
              <a href="{c.get('url')}" style="color: #16a34a; font-size: 13px; font-weight: 600; text-decoration: none;" target="_blank">Open Course &rarr;</a>
            </div>
            """

        html_focus_points = "".join(f"<li>{point}</li>" for point in focus_points)
        html_deadlines = "".join(
            f"<li><strong>{op.get('title')}</strong> — {op.get('deadline')}</li>" for op in deadlines
        ) or "<li>No confirmed deadlines yet - check the Plan Ahead links for each scheme's next round.</li>"

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 20px; }}
  .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
  .header {{ background: #0f172a; color: #ffffff; padding: 24px; }}
  .section {{ padding: 20px 24px; border-bottom: 1px solid #f1f5f9; }}
  .section-title {{ font-size: 16px; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 12px; display: flex; align-items: center; gap: 8px; }}
  .card {{ background: #f8fafc; border-radius: 8px; padding: 14px; margin-bottom: 12px; border: 1px solid #e2e8f0; }}
  .footer {{ background: #f8fafc; padding: 20px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span style="background: #0284c7; color: #ffffff; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">Weekly Development Digest</span>
    <h1 style="margin: 8px 0 4px; font-size: 22px;">Month {month} • Week {week}</h1>
    <p style="margin: 0; font-size: 14px; color: #94a3b8;">Student: {self.config.STUDENT_NAME} • Target: {self.config.UNIVERSITY}</p>
  </div>

  <div class="section">
    <div class="section-title">🌟 Opportunities Open to You Now</div>
    {html_opps}
  </div>

  <div class="section">
    <div class="section-title">📚 Active Course Load (Max 2)</div>
    {html_courses}
  </div>

  <div class="section">
    <div class="section-title">🎯 This Week's Focus & Challenge</div>
    <div class="card">
      <h4 style="margin: 0 0 6px; color: #0284c7; font-size: 14px;">{focus_title}</h4>
      <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.5;">{html_focus_points}</ul>
    </div>
    <div class="card" style="background: #fffbeb; border-color: #fde68a;">
      <h4 style="margin: 0 0 6px; color: #b45309; font-size: 14px;">⚡ Weekly Practical Challenge</h4>
      <p style="margin: 0; font-size: 13px; color: #78350f; line-height: 1.5;">{challenge}</p>
    </div>
  </div>

  <div class="section">
    <div class="section-title">✂️ Tailoring & Reading Growth</div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
      <div class="card">
        <strong style="font-size: 13px; color: #0f172a;">✂️ Tailoring Goal</strong>
        <p style="font-size: 12px; color: #475569; margin: 6px 0 0;">Calculate full cost breakdown (Material + Labor + Overhead + Margin) for your current garment.</p>
      </div>
      <div class="card">
        <strong style="font-size: 13px; color: #0f172a;">📖 Reading</strong>
        <p style="font-size: 12px; color: #475569; margin: 6px 0 0;">{reading_title} ({reading_author})</p>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">📅 Upcoming Deadlines</div>
    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155; line-height: 1.6;">{html_deadlines}</ul>
  </div>

  <div class="footer">
    Pre-University Development, Career & Opportunity System<br>
    Benin City, Edo State, Nigeria • Sent via Resend
  </div>
</div>
</body>
</html>
"""
        return subject, html_body, text_body

    def build_daily_alert(
        self,
        focus: DailyLearningFocus,
        learn_now_opps: List[OpportunityAlertMatch],
        long_term_opps: List[OpportunityAlertMatch],
        custom_note: str = ""
    ) -> Tuple[str, str, str]:
        """
        Generates (Subject, HTML, Plaintext) for the calendar-driven Daily Learning & Opportunity Alert.
        Answers:
        1. What should I focus on learning now?
        2. What newly available course/resource/opportunity is a good match for my long-term learning path?
        """
        subject = f"[DAILY LEARNING GUIDE] {focus.subject} • Month {focus.month}, Week {focus.week_in_month}"

        # --- PLAINTEXT VERSION ---
        text_body = f"""=======================================================
📚 TODAY'S PRE-UNIVERSITY LEARNING GUIDE
Date: {focus.date_str} • Month {focus.month}, Week {focus.week_in_month} (Global Week {focus.global_week}/78)
Phase: {focus.phase}
=======================================================
STUDENT: {self.config.STUDENT_NAME} ({self.config.CITY}, {self.config.STATE})
TARGET:  {self.config.UNIVERSITY} ({self.config.TARGET_FIELD})
APPRENTICESHIP: {self.config.CURRENT_APPRENTICESHIP}

-------------------------------------------------------
1. 🎯 WHAT TO FOCUS ON LEARNING NOW:
-------------------------------------------------------
• Subject: {focus.subject}
• Topic:   {focus.topic}
• TODAY'S RECOMMENDED FOCUS:
  👉 {focus.daily_focus}

• WEEKLY OBJECTIVES:
"""
        for obj in focus.weekly_objectives:
            text_body += f"  - {obj}\n"

        if focus.recommended_assignment:
            text_body += f"\n• CORE TASK: {focus.recommended_assignment}\n"

        # Learn Now Section
        text_body += """
-------------------------------------------------------
2. 🆕 LEARN NOW (Resources directly matching this week):
-------------------------------------------------------
"""
        if learn_now_opps:
            for i, op in enumerate(learn_now_opps, start=1):
                text_body += f"""{i}. {op.title}
   Provider: {op.provider} | Level: {op.difficulty_level} | Est. Time: {op.estimated_time} | Cost: {op.cost}
   Score: {op.relevance_score}/100
   Why it matches: {op.why_it_matches}
   Direct Link: {op.url}

"""
        else:
            text_body += "   ✨ You are right on track! No urgent supplementary resources required today.\n   Focus on your core active recall flashcards and daily study assignment.\n\n"

        # Long-Term Match Section
        text_body += """-------------------------------------------------------
3. 🎯 GOOD LONG-TERM MATCH (Strategic future alignment):
-------------------------------------------------------
"""
        if long_term_opps:
            for i, op in enumerate(long_term_opps, start=1):
                text_body += f"""{i}. {op.title}
   Provider: {op.provider} | Level: {op.difficulty_level} | Duration: {op.estimated_time}
   Score: {op.relevance_score}/100
   Why it matters: {op.why_it_matches}
   Where it fits:  {op.where_it_fits}
   Direct Link:    {op.url}

"""
        else:
            text_body += f"   🌟 Roadmap alignment: {focus.long_term_connection}\n\n"

        text_body += f"""-------------------------------------------------------
💡 SUGGESTED DAILY ACTION:
Spend 60–90 minutes mastering today's focus on '{focus.topic}'
before exploring supplementary courses. Maintain your Anki recall streak!
=======================================================
Pre-University Development, Career & Opportunity System
Benin City, Edo State, Nigeria • Delivered via Resend
"""

        # --- HTML VERSION ---
        html_learn_now = ""
        if learn_now_opps:
            for op in learn_now_opps:
                html_learn_now += f"""
                <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                    <span style="font-weight: 800; color: #166534; font-size: 15px;">{op.title}</span>
                    <span style="background: #dcfce7; color: #15803d; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; white-space: nowrap;">Score: {op.relevance_score}/100</span>
                  </div>
                  <p style="font-size: 12px; color: #15803d; margin: 4px 0 8px;">Provider: <strong>{op.provider}</strong> • Level: <strong>{op.difficulty_level}</strong> • Est. Time: <strong>{op.estimated_time}</strong> • Cost: <strong>{op.cost}</strong></p>
                  <div style="background: #ffffff; border-radius: 6px; padding: 10px; border-left: 3px solid #22c55e; margin-bottom: 10px; font-size: 13px; color: #1e293b;">
                    <strong>Why it matches today's focus:</strong> {op.why_it_matches}
                  </div>
                  <a href="{op.url}" style="display: inline-block; background: #16a34a; color: #ffffff !important; text-decoration: none; font-size: 12px; font-weight: 700; padding: 6px 12px; border-radius: 6px;" target="_blank">Access Course &rarr;</a>
                </div>
                """
        else:
            html_learn_now = """
            <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; text-align: center; color: #64748b; font-size: 13px;">
              ✨ <strong>Right on track!</strong> No new external resources needed today. Focus on your active recall flashcards and textbook exercises.
            </div>
            """

        html_long_term = ""
        if long_term_opps:
            for op in long_term_opps:
                html_long_term += f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                    <span style="font-weight: 800; color: #0369a1; font-size: 15px;">{op.title}</span>
                    <span style="background: #e0f2fe; color: #0284c7; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; white-space: nowrap;">Score: {op.relevance_score}/100</span>
                  </div>
                  <p style="font-size: 12px; color: #0284c7; margin: 4px 0 8px;">Provider: <strong>{op.provider}</strong> • Level: <strong>{op.difficulty_level}</strong> • Est. Duration: <strong>{op.estimated_time}</strong></p>
                  <div style="background: #ffffff; border-radius: 6px; padding: 10px; border-left: 3px solid #0284c7; margin-bottom: 6px; font-size: 13px; color: #1e293b;">
                    <strong>Why it matters:</strong> {op.why_it_matches}
                  </div>
                  <p style="font-size: 12px; color: #64748b; margin: 0 0 10px;"><strong>Where it fits:</strong> {op.where_it_fits}</p>
                  <a href="{op.url}" style="display: inline-block; background: #0284c7; color: #ffffff !important; text-decoration: none; font-size: 12px; font-weight: 700; padding: 6px 12px; border-radius: 6px;" target="_blank">Explore Long-Term Course &rarr;</a>
                </div>
                """
        else:
            html_long_term = f"""
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; font-size: 13px; color: #475569;">
              🌟 <strong>Roadmap Connection:</strong> {focus.long_term_connection}
            </div>
            """

        html_objectives = "".join(f"<li style='margin-bottom: 4px;'>{obj}</li>" for obj in focus.weekly_objectives)

        html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{subject}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 20px; }}
  .container {{ max-width: 640px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
  .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: #ffffff; padding: 24px; }}
  .badge {{ display: inline-block; background: #0284c7; color: #ffffff; font-weight: 800; font-size: 11px; padding: 4px 10px; border-radius: 9999px; text-transform: uppercase; margin-bottom: 8px; }}
  .section {{ padding: 20px 24px; border-bottom: 1px solid #f1f5f9; }}
  .section-title {{ font-size: 15px; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 12px; display: flex; align-items: center; gap: 8px; }}
  .focus-box {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
  .footer {{ background: #f8fafc; padding: 18px 24px; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="badge">Personalized Daily Learning Guide</span>
    <h1 style="margin: 6px 0 4px; font-size: 21px; line-height: 1.3;">{focus.subject}: {focus.topic}</h1>
    <p style="margin: 0; font-size: 13px; color: #94a3b8;">Month {focus.month}, Week {focus.week_in_month} (Week {focus.global_week}/78) • {self.config.STUDENT_NAME} • {self.config.UNIVERSITY}</p>
  </div>

  <div class="section">
    <div class="section-title">🎯 What to Focus on Learning Today</div>
    <div class="focus-box">
      <div style="font-size: 12px; font-weight: 700; color: #1d4ed8; text-transform: uppercase; margin-bottom: 4px;">Today's Recommended Focus:</div>
      <div style="font-size: 14px; font-weight: 700; color: #1e3a8a; line-height: 1.4;">{focus.daily_focus}</div>
    </div>
    <div style="font-size: 13px; color: #334155; line-height: 1.5;">
      <strong>Weekly Learning Objectives:</strong>
      <ul style="margin: 6px 0 0; padding-left: 20px;">
        {html_objectives}
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">🆕 Learn Now (Matched to Current Topic)</div>
    {html_learn_now}
  </div>

  <div class="section">
    <div class="section-title">🎯 Good Long-Term Match (Future Roadmap Alignment)</div>
    {html_long_term}
  </div>

  <div class="section" style="background: #fffbeb;">
    <div style="font-size: 13px; color: #92400e; line-height: 1.5;">
      <strong>💡 Suggested Action:</strong> Spend 60–90 minutes on today's focus on <em>{focus.topic}</em> before exploring long-term materials. Keep up your Anki flashcard streak!
    </div>
  </div>

  <div class="footer">
    Pre-University Development, Career & Opportunity System<br>
    Benin City, Edo State, Nigeria • Sent via Resend API
  </div>
</div>
</body>
</html>
"""
        return subject, html_body, text_body
