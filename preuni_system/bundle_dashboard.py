"""
Bundles all verified JSON datasets into dashboard/data.js for standalone GitHub Pages hosting.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DASHBOARD_DIR = BASE_DIR / "dashboard"

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
  timezone: "Africa/Lagos"
}};

window.PREUNI_DATA = {json.dumps(data, indent=2)};
"""
    out_file = DASHBOARD_DIR / "data.js"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print(f"✅ Successfully bundled all datasets into {out_file}")

if __name__ == "__main__":
    bundle()
