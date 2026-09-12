"""
Learning Calendar Engine for Pre-University Development System.
Dynamically tracks the student's 18-month curriculum roadmap, current phase, month,
week, weekly learning objectives, daily actionable focus, and long-term targets.
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from preuni_system.config import Config, DATA_DIR
from preuni_system.models import WeeklyCalendarItem, DailyLearningFocus
from preuni_system.utils import parse_date


class LearningCalendarEngine:
    """Calculates and serves dynamic curriculum position and learning focus."""

    # Default fallback curriculum mapping by month (Months 1 - 18)
    MONTHLY_CURRICULUM_BLUEPRINT = {
        1: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "Biology & Study Systems",
            "topic": "Cell Biology, Active Recall & Foundation Habits",
            "keywords": ["cell", "biology", "membrane", "transport", "osmosis", "diffusion", "organelles", "study habits", "anki"],
            "long_term": "Foundational requirement for UNIBEN BIO111 and 200L Cell Physiology.",
            "subtopics": [
                "Cell Structure, Transport & Active Recall Habits",
                "Atomic Structure, Electron Configuration & Periodic Trends",
                "Vital Signs Overview & Dexterity Calibration",
                "Costing Formulas, Budgeting & Monthly Review"
            ]
        },
        2: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "General Chemistry & Research Basics",
            "topic": "Chemical Bonding, Redox Reactions & Scientific Literature",
            "keywords": ["chemistry", "bonding", "redox", "oxidation", "reduction", "research", "google scholar"],
            "long_term": "Prerequisite for UNIBEN CHM111 and Medical Biochemistry.",
            "subtopics": [
                "Chemical Bonding & VSEPR Molecular Geometry",
                "Cell Division (Mitosis, Meiosis) & Mendelian Genetics",
                "Scientific Evidence & Boolean Search Operators",
                "Physics in Medicine: Mechanics & Force Vectors"
            ]
        },
        3: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "Anatomy & Physiology",
            "topic": "Cardiovascular, Respiratory & Clinical Hygiene",
            "keywords": ["cardiovascular", "heart", "blood pressure", "respiratory", "lungs", "hygiene", "who", "safety"],
            "long_term": "High-yield topic for UNIBEN BIO111, 200L Physiology, and UBTH clinical rotations.",
            "subtopics": [
                "Cardiovascular System & Hemodynamics",
                "Respiratory System & Gas Exchange Mechanisms",
                "Microbiology Basics & WHO Hand Hygiene Standards",
                "Public Speaking, Patient Empathy & Quarter 1 Review"
            ]
        },
        4: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "Healthcare Mathematics & Digital Systems",
            "topic": "Metric Conversions, Drug Dosages & Spreadsheets",
            "keywords": ["healthcare math", "dosage", "calculations", "metric conversions", "excel", "spreadsheets", "fluid dynamics"],
            "long_term": "Essential for UNIBEN Pharmacology, Nursing Medication Administration, and PHY111.",
            "subtopics": [
                "Metric Conversions & Clinical Dosage Calculations",
                "Excel / Google Sheets for Financial & Academic Tracking",
                "Fluid Dynamics & Poiseuille's Blood Flow Resistance",
                "Digital Lookbook Design & Financial Reconciliations"
            ]
        },
        5: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "Genetics & Professional Communication",
            "topic": "Central Dogma, Molecular Biology & Email Etiquette",
            "keywords": ["dna", "rna", "transcription", "translation", "genetics", "communication", "email", "star method"],
            "long_term": "Core foundation for UNIBEN BIO111, 200L Biochemistry, and professional networking.",
            "subtopics": [
                "DNA Replication, RNA Transcription & Protein Translation",
                "Email Etiquette & STAR Interview Framework",
                "Digestive System Anatomy & Clinical Nutrition",
                "Public Health Promotion & Customer Consultations"
            ]
        },
        6: {
            "phase": "Phase 1: Foundation & Habit Systems",
            "subject": "Organic Chemistry & Community Service",
            "topic": "Functional Groups, Biomolecules & Sewing for Charity",
            "keywords": ["organic chemistry", "functional groups", "biomolecules", "proteins", "amino acids", "volunteering", "charity"],
            "long_term": "Direct prerequisite for UNIBEN CHM102 and service-leadership development.",
            "subtopics": [
                "Organic Chemistry Functional Groups & IUPAC Nomenclature",
                "Biomolecules: Carbohydrates, Lipids & Amino Acids",
                "Mid-Year Community Service Project: Sewing for Charity",
                "1-Page Business Model Canvas & Quarter 2 Review"
            ]
        },
        7: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "Research Methodology & Bioethics",
            "topic": "PICO Framework, Study Designs & Ethics",
            "keywords": ["research", "methodology", "pico", "study design", "bioethics", "informed consent", "pubmed"],
            "long_term": "Prepares for undergraduate research projects and scientific seminars.",
            "subtopics": [
                "Formulating Research Questions via PICO Framework",
                "Observational vs Experimental Clinical Study Designs",
                "Research Ethics, Informed Consent & PubMed Deconstruction",
                "Zero-Waste Pattern Layouts & Fabric Reduction"
            ]
        },
        8: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "Healthcare Careers & Public Health",
            "topic": "Immunology, Disease Surveillance & Medical Scrub Design",
            "keywords": ["immunology", "immunity", "vaccines", "public health", "careers", "nursing", "medicine", "scrubs"],
            "long_term": "Directly tested in UNIBEN 200L Immunology and Clinical Nursing rotations.",
            "subtopics": [
                "Innate vs Adaptive Immunity & Vaccine Mechanisms",
                "Healthcare Career Comparison Matrix Deep-Dive",
                "Infection Prevention & Hospital Epidemiology",
                "Bespoke Medical Scrub Construction & Costing"
            ]
        },
        9: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "Physics & Hemodynamics",
            "topic": "Acoustics, Ultrasound Physics & Mentorship",
            "keywords": ["physics", "waves", "ultrasound", "doppler", "acoustics", "phy112", "leadership"],
            "long_term": "Directly tested in UNIBEN PHY112, Radiography, and Cardiology.",
            "subtopics": [
                "Wave Parameters, Acoustics & Clinical Doppler Ultrasound",
                "Fluid Pressure & Hemodynamics in Blood Vessels",
                "Emotional Intelligence, Conflict Resolution & Resilience",
                "Apprentice Tutoring & Quarter 3 Soft-Skills Review"
            ]
        },
        10: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "University Simulation Semester",
            "topic": "UNIBEN 100L Timed Mock Examinations",
            "keywords": ["mock exam", "uniben", "bio111", "chm111", "phy111", "simulation", "time management"],
            "long_term": "Builds high-pressure exam stamina and guarantees academic readiness for First Class CGPA.",
            "subtopics": [
                "UNIBEN BIO111 Timed Mock Examination & Error Analysis",
                "UNIBEN CHM111 Timed Mock Examination & Problem Review",
                "UNIBEN PHY111 Timed Mechanics & Wave Motion Drills",
                "Commission Queue Management Under Exam Deadlines"
            ]
        },
        11: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "Career Portfolio & Post-UTME Drills",
            "topic": "Student CV, Scholarship Packets & CBT Drills",
            "keywords": ["cv", "portfolio", "post-utme", "scholarships", "cbt", "interview prep"],
            "long_term": "Secures top Post-UTME screening scores and competitive scholarship awards.",
            "subtopics": [
                "2-Page Student CV & Scholarship Packet Assembly",
                "UNIBEN Post-UTME CBT Screening Drills (Biology & Chemistry)",
                "UNIBEN Post-UTME CBT Screening Drills (Physics & English)",
                "Digital Fashion & Skills Photography Lookbook"
            ]
        },
        12: {
            "phase": "Phase 2: Deepening & Scientific Research",
            "subject": "UNIBEN Readiness & Survival Handbook",
            "topic": "Campus Clearance, Geography & 5.0 CGPA Strategy",
            "keywords": ["uniben", "transition", "clearance", "cgpa", "survival guide", "ugbowo", "handbook"],
            "long_term": "Eliminates freshman orientation disorientation and ensures smooth academic launch.",
            "subtopics": [
                "UNIBEN Ugbowo Campus Structure & Medical Library Handbook",
                "First 30 Days Action Checklist & Clearance Documents",
                "University Survival & Success Personal Handbook Completion",
                "12-Month Development Portfolio Review & Year 1 Rubric"
            ]
        },
        13: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Post-UTME Screening Drills",
            "topic": "High-Yield CBT Drills & Speed-Accuracy Optimization",
            "keywords": ["cbt", "post-utme", "drills", "speed", "accuracy", "uniben", "admissions"],
            "long_term": "Maximizes UNIBEN Post-UTME aggregate score.",
            "subtopics": [
                "Post-UTME High-Yield Biology CBT Drills",
                "Post-UTME High-Yield Chemistry Calculations",
                "Post-UTME High-Yield Physics & Mechanics Drills",
                "Speed-Accuracy Error Minimization Strategies"
            ]
        },
        14: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Advanced Medical Terminology",
            "topic": "Greek & Latin Clinical Roots, Prefixes & Case Syntax",
            "keywords": ["medical terminology", "latin roots", "prefixes", "suffixes", "clinical", "nursing", "medicine"],
            "long_term": "Accelerates comprehension in 100L/200L Anatomy, Physiology, and Pathology.",
            "subtopics": [
                "Cardiovascular & Respiratory Root Words & Case Notes",
                "Renal, Hepatic & Gastrointestinal Clinical Syntax",
                "Neurological & Musculoskeletal Diagnostic Terminology",
                "Translation of Sample Hospital Case Summaries"
            ]
        },
        15: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Laboratory Safety & Protocols",
            "topic": "Pre-Lab Preparation & Scientific Instrumentation",
            "keywords": ["laboratory", "biosafety", "microscopy", "titration", "protocols", "uniben"],
            "long_term": "Prepares for 100L practical course components (BIO112, CHM112, PHY112).",
            "subtopics": [
                "Biosafety Level Standards & Chemical Waste Disposal",
                "Optical Microscopy Calibration & Specimen Mounting",
                "Precision Volumetric Titration & Analytical Techniques",
                "Laboratory Report Writing & Standard Error Propagation"
            ]
        },
        16: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Independent Living & Financial Mastery",
            "topic": "Meal Prepping, Domestic Budgeting & Student Banking",
            "keywords": ["independent living", "budgeting", "meal prep", "banking", "time management", "student life"],
            "long_term": "Ensures physical health, proper nutrition, and financial stability during university.",
            "subtopics": [
                "Benin City Cost-of-Living & Monthly Student Budgeting",
                "Nutritious Bulk Meal Prepping & Food Storage on Campus",
                "Student Banking, Digital Security & Emergency Funds",
                "Time-Blocking Schedules for University Workloads"
            ]
        },
        17: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Administrative Clearance & Campus Launch",
            "topic": "JAMB CAPS Acceptance & Physical Clearance File Jackets",
            "keywords": ["clearance", "jamb caps", "uniben", "hostel", "admissions", "file jackets"],
            "long_term": "Guarantees error-free admission clearance and official faculty matriculation.",
            "subtopics": [
                "JAMB CAPS Admission Verification & Acceptance Letter Printout",
                "Preparation of 4 Duplicate Physical Clearance File Jackets",
                "Campus Accommodation Logistics (Hall 1/2 vs BDPA/Osasogie)",
                "Health Centre Medical Screening Requirements & Chest X-Ray"
            ]
        },
        18: {
            "phase": "Phase 3: University Transition & Advanced Mastery",
            "subject": "Matriculation Launch & First 30 Days",
            "topic": "100-Level Execution & First Semester Lecture Schedule",
            "keywords": ["matriculation", "uniben", "first 30 days", "lectures", "cgpa", "ugbowo", "success"],
            "long_term": "Sets immediate trajectory for 5.0 First Class Honours at UNIBEN.",
            "subtopics": [
                "First Week Lecture Hall Locations & Course Representative Election",
                "Course Registration Form Endorsement with Course Adviser",
                "John Harris Library Barcode Card Registration & Study Desks",
                "Full Execution of First 30 Days University Survival Handbook"
            ]
        }
    }

    def __init__(self, schedule_file: Optional[Path] = None, start_date_str: Optional[str] = None):
        self.schedule_file = schedule_file or (DATA_DIR / "calendar_schedule.json")
        self.start_date_str = start_date_str or Config.START_DATE
        self.start_date = parse_date(self.start_date_str) or date(2026, 9, 1)
        self.schedule_items: Dict[int, WeeklyCalendarItem] = {}
        self._load_schedule()

    def _load_schedule(self) -> None:
        """Load schedule from JSON file and fill any gaps dynamically from blueprint."""
        if self.schedule_file.is_file():
            try:
                with open(self.schedule_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        w = WeeklyCalendarItem(
                            global_week=item["global_week"],
                            month=item["month"],
                            week_in_month=item["week_in_month"],
                            phase=item["phase"],
                            subject=item["subject"],
                            topic=item["topic"],
                            weekly_objectives=item.get("weekly_objectives", []),
                            daily_focus=item.get("daily_focus", ""),
                            core_keywords=item.get("core_keywords", []),
                            recommended_assignment=item.get("recommended_assignment", ""),
                            long_term_connection=item.get("long_term_connection", "")
                        )
                        self.schedule_items[item["global_week"]] = w
            except Exception as e:
                print(f"Warning: Failed to parse calendar schedule JSON: {e}")

        # Ensure all 78 weeks are populated seamlessly
        for m in range(1, 19):
            blueprint = self.MONTHLY_CURRICULUM_BLUEPRINT.get(m, self.MONTHLY_CURRICULUM_BLUEPRINT[1])
            for w_in_m in range(1, 5):
                global_w = ((m - 1) * 4) + w_in_m
                if global_w not in self.schedule_items:
                    subtopic_idx = min(w_in_m - 1, len(blueprint["subtopics"]) - 1)
                    subtopic = blueprint["subtopics"][subtopic_idx]
                    self.schedule_items[global_w] = WeeklyCalendarItem(
                        global_week=global_w,
                        month=m,
                        week_in_month=w_in_m,
                        phase=blueprint["phase"],
                        subject=blueprint["subject"],
                        topic=subtopic,
                        weekly_objectives=[
                            f"Master key concepts in {subtopic}",
                            f"Complete active recall flashcards for {blueprint['subject']}",
                            f"Apply concepts to clinical and practical problem solving",
                            f"Track weekly learning milestones and progress audit"
                        ],
                        daily_focus=f"Study core principles of {subtopic} and practice 5 application questions.",
                        core_keywords=blueprint["keywords"],
                        recommended_assignment=f"Complete practice review questions on {subtopic}.",
                        long_term_connection=blueprint["long_term"]
                    )

    def calculate_week_number(self, target_date: Optional[Union[date, datetime, str]] = None) -> int:
        """
        Calculate global week number (1 - 78) from a given date relative to START_DATE.
        """
        if target_date is None:
            calc_date = date.today()
        elif isinstance(target_date, str):
            calc_date = parse_date(target_date) or date.today()
        elif isinstance(target_date, datetime):
            calc_date = target_date.date()
        else:
            calc_date = target_date

        delta_days = (calc_date - self.start_date).days
        if delta_days < 0:
            return 1

        week_num = (delta_days // 7) + 1
        # Clamp between 1 and 78
        return max(1, min(78, week_num))

    def get_week(self, global_week: int) -> WeeklyCalendarItem:
        """Retrieve weekly curriculum item by global week (1 - 78)."""
        clamped_week = max(1, min(78, global_week))
        return self.schedule_items.get(clamped_week) or self.schedule_items[1]

    def get_learning_focus(
        self,
        target_date: Optional[Union[date, str]] = None,
        month: Optional[int] = None,
        week: Optional[int] = None,
        global_week: Optional[int] = None
    ) -> DailyLearningFocus:
        """
        Derive today's DailyLearningFocus context.
        Supports explicit overrides for month/week/global_week, or computes dynamically from date.
        """
        if global_week:
            gw = max(1, min(78, global_week))
        elif month and week:
            gw = max(1, min(78, ((month - 1) * 4) + week))
        elif month:
            gw = max(1, min(78, ((month - 1) * 4) + 1))
        else:
            gw = self.calculate_week_number(target_date)

        week_item = self.get_week(gw)
        date_str = target_date if isinstance(target_date, str) else (target_date.isoformat() if target_date else date.today().isoformat())

        return DailyLearningFocus(
            date_str=date_str,
            global_week=week_item.global_week,
            month=week_item.month,
            week_in_month=week_item.week_in_month,
            phase=week_item.phase,
            subject=week_item.subject,
            topic=week_item.topic,
            daily_focus=week_item.daily_focus,
            weekly_objectives=week_item.weekly_objectives,
            recommended_assignment=week_item.recommended_assignment,
            long_term_connection=week_item.long_term_connection
        )

    def get_upcoming_keywords(self, current_global_week: int, lookahead_weeks: int = 8) -> List[str]:
        """Aggregate keywords for future curriculum modules to score long-term relevance."""
        keywords = set()
        for w in range(current_global_week + 1, min(79, current_global_week + lookahead_weeks + 1)):
            item = self.get_week(w)
            keywords.update(item.core_keywords)
        return list(keywords)
