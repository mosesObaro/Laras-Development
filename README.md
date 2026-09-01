# 18-Month Pre-University Development, Career & Opportunity System
## University of Benin (UNIBEN) / Healthcare Preparation & Apprenticeship Integration Year

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Email Engine](https://img.shields.io/badge/Email-Resend%20API-black.svg)](https://resend.com/)
[![Hosting](https://img.shields.io/badge/Hosting-GitHub%20Pages-2ea44f.svg)](https://pages.github.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Executive Summary & Core Philosophy

This system is an end-to-end, production-ready personal development, healthcare career-exploration, and opportunity-monitoring platform designed for a Nigerian teenager in Edo State (Benin City) who has completed WAEC, is undertaking a **tailoring apprenticeship**, and is preparing for entry into the **University of Benin (UNIBEN)** for a healthcare degree (e.g., Nursing Science, Medicine, Pharmacy, Medical Laboratory Science, Physiotherapy, etc.).

### The Core Development Philosophy:
$$\mathbf{SKILLS} + \mathbf{EXPERIENCE} + \mathbf{CHARACTER} + \mathbf{KNOWLEDGE} + \mathbf{EXPOSURE} + \mathbf{SERVICE} \gg \mathbf{CERTIFICATES}$$

### The 70 / 20 / 10 Development Mix:
* **70% Practical Application**: Daytime tailoring apprenticeship, hands-on projects, Edo State community volunteering, presentations, financial budgeting, and life skills.
* **20% Exposure & Mentorship**: Webinars, healthcare professional interviews, books, university open events, and scientific inquiry.
* **10% Formal Learning**: Curated, high-quality, free online courses (strictly capped at **maximum 2 simultaneous courses**).

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│               PRE-UNIVERSITY SYSTEM ARCHITECTURAL LAYOUT               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       ▼                           ▼                           ▼
┌──────────────┐          ┌────────────────┐          ┌────────────────┐
│ CLI & Engine │          │ SQLite3 Engine │          │ Web Dashboard  │
│ (Python 3)   │ ◄──────► │ (Local/Cached) │ ◄──────► │ (GitHub Pages) │
└──────┬───────┘          └────────────────┘          └────────────────┘
       │
       ├───────────────────────────────────────────────────────┐
       ▼                                                       ▼
┌───────────────────────────────┐              ┌───────────────────────────────┐
│ Opportunity Monitor & Crawler │              │ Resend Email Delivery Engine  │
│ • RSS / Atom & Custom Ingest  │              │ • Immediate Alerts (85+)      │
│ • 8-Factor Quality Scorer     │              │ • Weekly Development Digest   │
│ • Teenager Safety Risk Filter │              │ • Monthly Progress Report     │
└───────────────────────────────┘              └───────────────────────────────┘
```

---

## 3. Directory & Folder Structure

```
lara_development_system/
├── preuni_system/                     # Core Python Automation & Monitoring Package
│   ├── __init__.py                    # Package initialization
│   ├── config.py                      # Profile, thresholds, and Resend settings
│   ├── models.py                      # Dataclasses & schemas (Course, Org, Opp, Progress)
│   ├── utils.py                       # Hashing, dates, URL safety, and UNIBEN 5.0 CGPA math
│   ├── db.py                          # SQLite database interface & migrations
│   ├── scorer.py                      # 8-factor Opportunity Quality Scorer & Safety Filter
│   ├── crawler.py                     # Multi-source RSS/Atom parser & feed ingestor
│   ├── monitor.py                     # Pipeline coordinator & expiration manager
│   ├── emailer.py                     # Resend REST API client & SMTP fallback dispatcher
│   ├── cli.py                         # Unified Command Line Interface
│   ├── seed_generator.py              # Course dataset population utility
│   └── bundle_dashboard.py            # Bundles JSON data into dashboard/data.js
│
├── data/                              # Verified Databases (Seed Datasets)
│   ├── courses.json                   # 127 verified courses with direct links & practical tasks
│   ├── volunteering.json              # 15 verified volunteering orgs (Benin City / Edo Priority A)
│   ├── healthcare_careers.json        # 14 healthcare career comparative profiles (UNIBEN requirements)
│   ├── scholarships_competitions.json # 10 verified scholarships & competitions for Nigerians
│   ├── soft_skills.json               # 15 quarterly soft-skills rubric evaluation standards
│   ├── reading_list.json              # 12-month curated reading curriculum with writing prompts
│   └── uniben_data.json               # Official UNIBEN faculties, 100L courses, and First 30 Days guide
│
├── curriculum/                        # Comprehensive 18-Month Curriculum Documents
│   ├── 01_18_month_master_curriculum.md # Month-by-month roadmap across all 30 pillars
│   ├── 02_academic_foundations.md       # Biology, Chemistry, Physics, Math (Healthcare-focused)
│   ├── 03_healthcare_foundations.md     # Anatomy, physiology, ethics, clinical safety boundaries
│   ├── 04_uniben_readiness_guide.md     # Official UNIBEN admission, UTME, CGPA, faculty guide
│   ├── 05_first_30_days_at_uniben.md    # Actionable 30-day handbook for campus, safety, academics
│   ├── 06_tailoring_integration_guide.md# Apprenticeship milestones, pricing, costing, business plan
│   ├── 07_12_month_reading_program.md   # Curated books, chapters, reflection prompts & exercises
│   ├── 08_soft_skills_rubrics.md        # 1-5 Quarterly evidence-based soft-skills assessment
│   └── 09_weekly_reflection_journal.md  # Structured weekly & daily reflection frameworks
│
├── dashboard/                         # Standalone Interactive Web Dashboard (GitHub Pages Ready)
│   ├── index.html                     # Single-Page Application (Navigation, Charts, Modals)
│   ├── app.js                         # State management, reactive filters, CGPA simulator
│   ├── styles.css                     # Custom animations, card hover effects, badge themes
│   └── data.js                        # Bundled datasets for offline/static deployment
│
├── .github/workflows/                 # GitHub Actions CI/CD Automations
│   ├── weekly_digest.yml              # Scheduled weekly run (Mondays 07:00 WAT) via Resend
│   ├── opportunity_crawler.yml        # Daily crawler & immediate alert scan
│   └── deploy_dashboard.yml           # Auto-deploy dashboard to GitHub Pages
│
├── tests/                             # Automated Test Suite (19 unit tests)
│   ├── test_models.py
│   ├── test_scorer.py
│   ├── test_db.py
│   ├── test_crawler.py
│   ├── test_emailer.py
│   └── test_cli.py
│
├── .env.example                       # Environment template
├── requirements.txt                   # Optional dependencies
├── setup.py                           # Package setup script
├── Makefile                           # Developer commands
└── README.md                          # Complete technical and operational manual
```

---

## 4. Technologies Selected & Rationale

1. **Python 3 Standard Library Core (`sqlite3`, `urllib`, `smtplib`, `json`, `dataclasses`, `unittest`)**:
   * *Rationale*: Ensures zero external dependency failure modes, running reliably on any system, server, or GitHub Actions runner out of the box.
2. **Resend REST API (`https://api.resend.com/emails`)**:
   * *Rationale*: High-deliverability transactional email service with generous free tier (3,000 emails/month, 100/day). Sends verified HTML alerts without deliverability headaches.
3. **SQLite3 Embedded Database**:
   * *Rationale*: Serverless, lightweight, ACID-compliant local database storing all courses, hours logged, tailoring finances, and opportunities.
4. **HTML5 + TailwindCSS (CDN) + Lucide Icons + Chart.js**:
   * *Rationale*: Zero build steps needed (no heavy node_modules). Runs instantly in any web browser and deploys to GitHub Pages in seconds.

---

## 5. Quick Start & Setup Instructions

### A. Clone Repository & Configure Environment
```bash
# 1. Clone your GitHub repository
git clone https://github.com/your-username/lara-preuni-system.git
cd lara-preuni-system

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your details
# Set your RESEND_API_KEY from https://resend.com
```

### B. Seed the Database
```bash
python3 -m preuni_system.cli seed
```

### C. Run Automated Tests
```bash
python3 -m unittest discover -s tests
# or using Makefile:
make test
```

### D. Launch the Interactive Dashboard Locally
```bash
python3 -m preuni_system.cli serve --port 8000
# or using Makefile:
make serve
```
Open your browser and navigate to: **`http://localhost:8000`**

---

## 6. CLI Usage Guide

The unified CLI provides command-line control:

| Command | Description | Example |
| :--- | :--- | :--- |
| `seed` | Populates SQLite database from JSON seed files | `python3 -m preuni_system.cli seed` |
| `scan` | Scans RSS/Atom feeds, deduplicates, and scores | `python3 -m preuni_system.cli scan` |
| `digest` | Generates and previews/sends the weekly digest | `python3 -m preuni_system.cli digest --preview` |
| `alert` | Generates and previews/sends top high-priority alert | `python3 -m preuni_system.cli alert --preview` |
| `stats` | Displays student progress and summary metrics | `python3 -m preuni_system.cli stats` |
| `serve` | Launches local dashboard web server | `python3 -m preuni_system.cli serve --port 8000` |

---

## 7. Hosting on GitHub Pages & GitHub Actions Setup

### Step 1: Push Repository to GitHub
```bash
git add .
git commit -m "Initial commit of Pre-University Development System"
git push origin main
```

### Step 2: Configure GitHub Repository Secrets
Go to your GitHub Repository $\rightarrow$ **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** $\rightarrow$ **New repository secret**:
* `RESEND_API_KEY`: Your API key from [Resend](https://resend.com).
* `RESEND_FROM_EMAIL`: `Pre-University System <onboarding@resend.dev>` (or your custom domain).
* `STUDENT_EMAIL`: Student's email address.
* `PARENT_EMAIL`: Parent/Guardian's email address.

### Step 3: Enable GitHub Pages
1. In your GitHub repository, go to **Settings** $\rightarrow$ **Pages**.
2. Under **Build and deployment** $\rightarrow$ **Source**, select **GitHub Actions**.
3. The `.github/workflows/deploy_dashboard.yml` workflow will automatically build and publish your dashboard to `https://<your-username>.github.io/<repo-name>/`.

---

## 8. Opportunity Quality & Safety Scoring Methodology

### A. Mathematical Scoring Formula (0 – 100):
$$\text{Total Score} = (R \times 0.25) + (C \times 0.20) + (E \times 0.20) + (V \times 0.10) + (A \times 0.10) + (G \times 0.05) + (T \times 0.05) + (N \times 0.05)$$

* **Relevance ($R$, 25%)**: Alignment with UNIBEN healthcare, sciences, tailoring, or character.
* **Credibility ($C$, 20%)**: Accredited universities, WHO, UNICEF, Government bodies, registered NGOs.
* **Educational Value ($E$, 20%)**: Hands-on practical tasks vs passive video consumption.
* **Cost / Value ($V$, 10%)**: 100 for verified free opportunities; heavily penalized for paid.
* **Accessibility ($A$, 10%)**: Bandwidth feasibility and physical accessibility in Benin City / Edo State.
* **Age Suitability ($G$, 5%)**: Appropriate for 16–19 year olds.
* **Time Commitment ($T$, 5%)**: Fits within the daily 60–90 min study limit.
* **Networking & Mentorship ($N$, 5%)**: Direct interaction with credible health mentors.

### B. Decision Thresholds:
* **$\mathbf{\ge 85}$ (STRONGLY RECOMMENDED)**: Triggers immediate email alert if deadline is approaching.
* **$\mathbf{70 - 84}$ (CONSIDER)**: Curated in the weekly digest.
* **$\mathbf{< 70}$ (SUPPRESSED)**: Omitted from email communications.

### C. Non-Clinical Safety Mandate:
* Any opportunity involving invasive clinical procedures (injections, blood drawing, prescribing, surgery) performed by an unqualified teenager is **automatically rejected**.
* Strict verification of physical addresses in Benin City (e.g., Nigerian Red Cross Edo Branch on Ikpokpan Rd, Girls' Power Initiative on Upper Ekewan Rd).

---

## 9. Tailoring Apprenticeship Costing Formula

Never guess prices. The system embeds the scientific unit costing model:

$$\text{Final Price} = \text{Material Cost} + (\text{Labor Hours} \times \text{Hourly Rate}) + \text{Overhead (10--15\%)} + \text{Profit Margin (25--35\%)}$$

*Example*:
* Material (Fabric, lining, zip, stay): $\text{₦3,200}$
* Labor ($3.5\text{ hrs} \times \text{₦1,200/hr}$): $\text{₦4,200}$
* Overhead (Power, transport): $\text{₦800}$
* Base Cost = $\text{₦8,200}$ $\rightarrow$ $30\%$ Margin ($\text{₦2,460}$) $\rightarrow$ **Customer Price: $\mathbf{₦10,660}$**.

---

## 10. UNIBEN 5.0 CGPA Scale

$$\text{GPA} = \frac{\sum (\text{Course Credit Units} \times \text{Grade Point})}{\text{Total Credit Units}}$$

* **70 – 100% (A = 5.0)**: Excellent
* **60 – 69% (B = 4.0)**: Very Good
* **50 – 59% (C = 3.0)**: Good
* **45 – 49% (D = 2.0)**: Fair
* **40 – 44% (E = 1.0)**: Pass
* **0 – 39% (F = 0.0)**: Fail
* **$\ge 4.50$**: **First Class Honours** | **$3.50 - 4.49$**: **Second Class Upper (2:1)**

---

## 11. Maintenance & Troubleshooting

* **Missing Resend API Key**:
  If `RESEND_API_KEY` is not set in `.env`, the system gracefully operates in `--preview / dry-run` mode, generating full HTML and plaintext email previews in `output/emails/`.
* **Updating Bundled Dashboard Data**:
  Run `python3 -m preuni_system.bundle_dashboard` (or `make bundle`) whenever JSON datasets in `data/` are edited.
* **Database Backup**:
  Use the **"Backup JSON"** button in the dashboard header or copy `preuni_system.sqlite3`.

---

## 12. License & Integrity

This system is released under the **MIT License**. Created with dedication to educational excellence, character development, and empowering the next generation of Nigerian healthcare leaders.
