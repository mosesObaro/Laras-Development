"""
Utility functions for hashing, date manipulation, deduplication, sanitization, and CGPA math.
"""

import hashlib
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any


def normalize_text(text: str) -> str:
    """Normalize text for comparison, removing extra spaces and lowercasing."""
    if not text:
        return ""
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.lower().split())


def generate_hash_id(prefix: str, *components: str) -> str:
    """Generate a stable short hash ID from string components."""
    combined = "||".join(str(c).strip().lower() for c in components)
    hash_digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{hash_digest}"


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Safely parse date strings in common formats (YYYY-MM-DD, DD/MM/YYYY, etc.)."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%d %b %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def is_expired(deadline_str: Optional[str], ref_date: Optional[date] = None) -> bool:
    """Check if a given deadline date is expired relative to today or ref_date."""
    if not deadline_str:
        return False
    parsed = parse_date(deadline_str)
    if not parsed:
        return False
    today = ref_date or date.today()
    return parsed < today


def format_naira(amount: float) -> str:
    """Format numerical value to Nigerian Naira currency display."""
    return f"₦{amount:,.2f}"


def calculate_uniben_cgpa(grade_list: List[Tuple[str, int, int]]) -> Dict[str, Any]:
    """
    Calculate UNIBEN 5.0 CGPA Scale.
    Input: List of (course_code, credit_units, score_or_grade_point)
    UNIBEN Grade Points:
      70-100: A = 5
      60-69:  B = 4
      50-59:  C = 3
      45-49:  D = 2
      40-44:  E = 1
      0-39:   F = 0
    """
    total_units = 0
    total_points = 0
    course_details = []

    for item in grade_list:
        course_code = item[0]
        units = int(item[1])
        score_val = item[2]

        if isinstance(score_val, int) or isinstance(score_val, float):
            if score_val >= 70:
                grade, gp = "A", 5
            elif score_val >= 60:
                grade, gp = "B", 4
            elif score_val >= 50:
                grade, gp = "C", 3
            elif score_val >= 45:
                grade, gp = "D", 2
            elif score_val >= 40:
                grade, gp = "E", 1
            else:
                grade, gp = "F", 0
        else:
            grade = str(score_val).upper()
            gp_map = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
            gp = gp_map.get(grade, 0)

        weighted_gp = units * gp
        total_units += units
        total_points += weighted_gp
        course_details.append({
            "course_code": course_code,
            "units": units,
            "grade": grade,
            "grade_point": gp,
            "weighted_points": weighted_gp,
        })

    cgpa = round(total_points / total_units, 2) if total_units > 0 else 0.0

    # Classification
    if cgpa >= 4.50:
        classification = "First Class Honours"
    elif cgpa >= 3.50:
        classification = "Second Class Honours (Upper Division)"
    elif cgpa >= 2.40:
        classification = "Second Class Honours (Lower Division)"
    elif cgpa >= 1.50:
        classification = "Third Class Honours"
    elif cgpa >= 1.00:
        classification = "Pass"
    else:
        classification = "Probation / Fail"

    return {
        "total_units": total_units,
        "total_weighted_points": total_points,
        "cgpa": cgpa,
        "classification": classification,
        "courses": course_details,
    }


def is_suspicious_url(url: str) -> bool:
    """Flag common scam/phishing/unverified patterns."""
    if not url:
        return True
    suspicious_patterns = [
        r"bit\.ly",
        r"tinyurl\.com",
        r"t\.me",
        r"wa\.me",
        r"chat\.whatsapp\.com",
        r"free-money",
        r"crypto-gift",
        r"mlm-matrix",
        r"fast-cash",
    ]
    for pattern in suspicious_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False
