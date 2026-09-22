"""
Data models and schemas for the Pre-University System.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class Course:
    id: str
    name: str
    provider: str
    url: str
    category: str
    cost: str = "Free"
    certificate: bool = False
    duration: str = "4 weeks"
    difficulty: str = "Beginner"
    eligibility: str = "Open to all"
    age_suitability: str = "Suitable (15-19)"
    scores: Dict[str, Any] = field(default_factory=dict)
    recommended_month: int = 1
    status: str = "Not started"  # "Not started", "In progress", "Completed"
    practical_assignment: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VolunteeringOpportunity:
    id: str
    name: str
    organization: str
    category: str
    description: str
    url: str
    location: str
    geographic_priority: str = "A"  # A (Benin/Edo), B (Nigeria), C (Online), D (Intl)
    date: str = "Ongoing / Regular"
    deadline: Optional[str] = None
    age_requirement: str = "16+"
    cost: str = "Free"
    time_commitment_hours: int = 4
    skills_gained: List[str] = field(default_factory=list)
    safety_score: int = 95
    credibility_score: int = 95
    relevance_score: int = 90
    overall_score: int = 92
    parent_approval_required: bool = True
    status: str = "Available"  # "Available", "Applied", "Active", "Completed", "Archived"
    hours_completed: int = 0
    reflection: str = ""
    contact_info: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthcareCareer:
    id: str
    title: str
    degree_name: str
    overview: str
    responsibilities: List[str] = field(default_factory=list)
    uniben_faculty_dept: str = ""
    duration_years: int = 5
    utme_subjects: List[str] = field(default_factory=lambda: ["English", "Biology", "Chemistry", "Physics"])
    olevel_requirements: str = "5 Credits (English, Math, Biology, Chemistry, Physics) in max 2 sittings"
    post_utme_profile: str = "High Cutoff (UNIBEN Post-UTME CBT)"
    clinical_rotations: str = ""
    regulatory_body: str = ""
    career_progression: List[str] = field(default_factory=list)
    specializations: List[str] = field(default_factory=list)
    work_environments: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    international_mobility: str = "High"
    entrepreneurial_possibilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Opportunity:
    id: str
    title: str
    organizer: str
    category: str  # Course, Scholarship, Event, Volunteering, Competition, Mentorship, Career Exposure
    url: str
    description: str
    location: str = "Online / Nigeria"
    date: str = ""
    deadline: Optional[str] = None
    cost: str = "Free"
    eligibility: str = "Pre-University / Teenagers (16-19)"
    geographic_priority: str = "A"
    min_level: str = "pre-university"  # Lowest study level that can apply (see Config.STUDY_LEVELS)
    max_level: Optional[str] = None  # Highest study level that can apply (None = no upper limit)
    scores: Dict[str, Any] = field(default_factory=dict)
    total_score: int = 85
    is_immediate_alert: bool = False
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReadingItem:
    id: str
    month: int
    week: int
    title: str
    author: str
    genre: str
    url: str = ""
    summary: str = ""
    key_concepts: List[str] = field(default_factory=list)
    reflection_questions: List[str] = field(default_factory=list)
    practical_exercise: str = ""
    status: str = "Not read"  # "Not read", "Reading", "Completed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SoftSkillAssessment:
    id: str
    quarter: int  # 1 to 6
    date: str
    communication: int = 3
    confidence: int = 3
    critical_thinking: int = 3
    emotional_intelligence: int = 3
    time_management: int = 3
    problem_solving: int = 3
    teamwork: int = 3
    leadership: int = 3
    financial_discipline: int = 3
    digital_literacy: int = 3
    professionalism: int = 3
    resilience: int = 3
    creativity: int = 3
    self_advocacy: int = 3
    learning_ability: int = 3
    evidence_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WeeklyCalendarItem:
    global_week: int
    month: int
    week_in_month: int
    phase: str
    subject: str
    topic: str
    weekly_objectives: List[str] = field(default_factory=list)
    daily_focus: str = ""
    core_keywords: List[str] = field(default_factory=list)
    recommended_assignment: str = ""
    long_term_connection: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DailyLearningFocus:
    date_str: str
    global_week: int
    month: int
    week_in_month: int
    phase: str
    subject: str
    topic: str
    daily_focus: str
    weekly_objectives: List[str] = field(default_factory=list)
    recommended_assignment: str = ""
    long_term_connection: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpportunityAlertMatch:
    opportunity_id: str
    title: str
    provider: str
    url: str
    category: str
    match_type: str  # "learn_now" or "long_term"
    relevance_score: int
    why_it_matches: str
    where_it_fits: str = ""
    difficulty_level: str = "Beginner / Pre-University"
    estimated_time: str = "45-60 mins"
    cost: str = "Free"
    practical_task: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AlertHistoryItem:
    id: str
    opportunity_id: str
    url_normalized: str
    date_alerted: str
    alert_type: str  # "learn_now", "long_term", "daily_reminder"
    week_number: int
    relevance_score: int
    consumed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
