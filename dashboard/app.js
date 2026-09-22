/**
 * Main Application Logic for Pre-University Development & Opportunity System Dashboard.
 * Offline-first, reactive state with localStorage persistence.
 */

// Saved progress: only statuses and the student's own entries (see progress.js)
const STORAGE_KEY = "PREUNI_STATE_V2";
const LEGACY_STORAGE_KEY = "PREUNI_STATE_V1";

// Global State
let appState = {
  courses: [],
  volunteering: [],
  careers: [],
  scholarships: [],
  reading: [],
  uniben: null,
  soft_skills: [],
  course_progress: {},
  reading_progress: {},
  tailoring_projects: [],
  volunteer_logs: [],
  checklist_completed: [],
  rubric_scores: {},
  active_modal_course_id: null
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  loadData();
  initNavigation();
  renderOverview();
  renderCurriculum();
  renderCourses();
  renderVolunteering();
  renderCareers();
  renderTailoring();
  renderUniben();
  renderReading();
  initRubricChart();
  initEmailPreview();
  initModalsAndEvents();
  lucide.createIcons();
});

// 1. Data Loader & State Sync
function readSavedState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    console.error("Error loading saved progress:", e);
    return null;
  }
}

function currentProgressState() {
  return {
    version: 2,
    course_progress: appState.course_progress,
    reading_progress: appState.reading_progress,
    tailoring_projects: appState.tailoring_projects,
    volunteer_logs: appState.volunteer_logs,
    checklist_completed: appState.checklist_completed,
    rubric_scores: appState.rubric_scores
  };
}

function persistState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(currentProgressState()));
    localStorage.removeItem(LEGACY_STORAGE_KEY);
  } catch (e) {
    console.error("Could not save progress:", e);
  }
}

function loadData() {
  const baseData = window.PREUNI_DATA || {};
  const shared = baseData.progress || {};  // data/progress.json, if it has been committed
  const saved = readSavedState();
  const local = PreuniProgress.normalizeState(saved);

  appState.course_progress = PreuniProgress.mergeProgress(shared.courses, local.course_progress);
  appState.reading_progress = PreuniProgress.mergeProgress(shared.reading, local.reading_progress);
  appState.tailoring_projects = local.tailoring_projects;
  appState.volunteer_logs = local.volunteer_logs;
  appState.checklist_completed = local.checklist_completed;
  appState.rubric_scores = local.rubric_scores;

  // Details always come from the latest bundled data; only statuses come from saved progress
  appState.courses = PreuniProgress.applyProgress(baseData.courses, appState.course_progress, "Not started");
  appState.reading = PreuniProgress.applyProgress(baseData.reading_list, appState.reading_progress, "Not read");
  appState.volunteering = baseData.volunteering || [];
  appState.careers = baseData.healthcare_careers || [];
  appState.scholarships = baseData.scholarships_competitions || [];
  appState.uniben = baseData.uniben_data || null;
  appState.soft_skills = baseData.soft_skills || [];

  // Rewrite progress saved by an older version in the new format
  if (saved && saved.version !== 2) persistState();
}

function saveState() {
  persistState();
  updateSummaryMetrics();
}

function setItemStatus(item, progressMap, status) {
  item.status = status;
  progressMap[item.id] = { status, updated: new Date().toISOString() };
  saveState();
}

// 2. Navigation Tabs
function initNavigation() {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.add("hidden"));

      btn.classList.add("active");
      const targetId = `tab-${btn.dataset.tab}`;
      const target = document.getElementById(targetId);
      if (target) {
        target.classList.remove("hidden");
      }
      lucide.createIcons();
    });
  });
}

// 3. Overview Tab Rendering
function renderOverview() {
  const container = document.getElementById("overviewTopOpps");
  if (!container) return;

  // Same rules as the emails: open to the student now first, then ones for later study years
  const level = (window.PREUNI_CONFIG || {}).student_level || "pre-university";
  const byScore = (a, b) => (b.total_score || 0) - (a.total_score || 0);
  const active = (appState.scholarships || []).filter(op => op.is_active !== false);
  const openNow = active.filter(op => PreuniProgress.isLevelEligible(op.min_level, op.max_level, level)).sort(byScore);
  const later = active
    .filter(op => !PreuniProgress.isLevelEligible(op.min_level, op.max_level, level) && PreuniProgress.isLevelRelevant(op.min_level, op.max_level, level))
    .sort(byScore);
  const topOpps = [...openNow.map(op => ({ op, isOpen: true })), ...later.map(op => ({ op, isOpen: false }))].slice(0, 4);

  container.innerHTML = topOpps.map(({ op, isOpen }) => `
    <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col gap-1">
      <div class="flex items-center justify-between gap-2">
        <span class="font-bold text-slate-900 line-clamp-1">${op.title}</span>
        <span class="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold ${isOpen ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}">${isOpen ? 'Open now' : `From ${op.min_level}`}</span>
      </div>
      <p class="text-slate-500 text-[11px] line-clamp-2">${op.description}</p>
      <div class="flex items-center justify-between text-[11px] mt-1 pt-1 border-t border-slate-200/60">
        <span class="text-rose-600 font-semibold">Deadline: ${op.deadline || 'Not yet announced'}</span>
        <a href="${op.url}" target="_blank" class="text-brand-600 font-bold hover:underline">${isOpen ? 'Apply' : 'Details'} &rarr;</a>
      </div>
    </div>
  `).join("");

  updateSummaryMetrics();
}

function updateSummaryMetrics() {
  const completedCourses = appState.courses.filter(c => c.status === "Completed").length;
  const inProgCourses = appState.courses.filter(c => c.status === "In progress").length;
  const totalVolunteerHours = appState.volunteer_logs.reduce((sum, item) => sum + (parseInt(item.hours) || 0), 0);
  const totalTailoringProfit = appState.tailoring_projects.reduce((sum, item) => sum + (parseFloat(item.profit) || 0), 0);
  const booksRead = appState.reading.filter(r => r.status === "Completed").length;

  document.getElementById("statCoursesCompleted").textContent = `${completedCourses} / ${appState.courses.length}`;
  document.getElementById("statCoursesInProg").textContent = `${inProgCourses} in progress`;
  document.getElementById("statVolunteerHours").textContent = `${totalVolunteerHours} hrs`;
  document.getElementById("statTailoringProjects").textContent = appState.tailoring_projects.length;
  document.getElementById("statTailoringProfit").textContent = `₦${totalTailoringProfit.toLocaleString('en-US', {minimumFractionDigits: 2})} profit`;
  document.getElementById("statBooksRead").textContent = `${booksRead} / ${appState.reading.length}`;
  document.getElementById("tabCourseCount").textContent = appState.courses.length;

  const overallProgress = Math.min(100, Math.round(((completedCourses / Math.max(1, appState.courses.length)) * 40) + ((totalVolunteerHours / 30) * 30) + ((appState.tailoring_projects.length / 7) * 30)));
  document.getElementById("statOverallProgress").textContent = `${overallProgress}%`;
}

// 4. Curriculum Roadmap Rendering
function renderCurriculum() {
  const container = document.getElementById("roadmapAccordion");
  if (!container) return;

  const months = [
    { m: 1, title: "Foundation, Habit Stacking & Digital Setup", academic: "Biology review (Cell Transport) & Anki flashcard system", tailoring: "Establish daily measurement and time ledger", reading: "Atomic Habits by James Clear" },
    { m: 2, title: "Learning How to Learn & General Chemistry", academic: "General Chemistry (Atomic Structure & Redox)", tailoring: "Precision pattern drafting for skirts & blouses", reading: "A Mind for Numbers by Barbara Oakley" },
    { m: 3, title: "Human Anatomy, Vital Signs & Dexterity", academic: "Cardiovascular system & vital signs (OpenStax Fundamentals of Nursing)", tailoring: "Intricate hand-stitching linking craft to clinical finesse", reading: "Gifted Hands by Ben Carson" },
    { m: 4, title: "Digital & Financial Costing Systems", academic: "Healthcare Math, dosage calculations & Excel budgets", tailoring: "Scientific unit costing formula on 3 bespoke garments", reading: "Things Fall Apart by Chinua Achebe" },
    { m: 5, title: "Communication, Public Speaking & Bedside Empathy", academic: "Medical Genetics & Patient Communication", tailoring: "5 structured customer intake consultations", reading: "The Richest Man in Babylon" },
    { m: 6, title: "Money, Entrepreneurship & Sewing for Charity", academic: "Organic Chemistry functional groups & biomolecules", tailoring: "Mend 10 school uniforms for community donation drive", reading: "The E-Myth Revisited by Michael Gerber" },
    { m: 7, title: "Research Methodology & Bioethics", academic: "Scientific report writing (OpenLearn) & PubMed deconstruction", tailoring: "Zero-waste fabric pattern layouts", reading: "The Immortal Life of Henrietta Lacks" },
    { m: 8, title: "Healthcare Career Matrix & Public Health", academic: "Immunology & antimicrobial resistance (OpenLearn)", tailoring: "Construct professional medical scrub set prototype", reading: "Mountains Beyond Mountains (Dr. Paul Farmer)" },
    { m: 9, title: "Emotional Intelligence, Leadership & Resilience", academic: "University Physics (Fluid pressure & hemodynamics)", tailoring: "Train junior apprentice on precision seams", reading: "Grit by Angela Duckworth" },
    { m: 10, title: "UNIBEN Simulation Semester", academic: "Timed mock exams for 100L BIO111, CHM111, PHY111", tailoring: "Manage full client queue under study deadlines", reading: "How to Win Friends and Influence People" },
    { m: 11, title: "Career Portfolio & Professional Launchpad", academic: "UNIBEN Post-UTME screening drills (CBT)", tailoring: "Compile complete digital fashion lookbook", reading: "Half of a Yellow Sun by Chimamanda Adichie" },
    { m: 12, title: "University Transition & Survival Handbook", academic: "UNIBEN 100L syllabus pre-reading & study routines", tailoring: "2-Page small business plan for custom brand", reading: "Deep Work by Cal Newport" }
  ];

  container.innerHTML = months.map(item => `
    <div class="border border-slate-200 rounded-xl overflow-hidden bg-slate-50/50">
      <button class="w-full text-left px-5 py-4 font-bold text-slate-900 bg-white hover:bg-slate-50 flex items-center justify-between transition" onclick="toggleAccordion('cur-m-${item.m}')">
        <span class="flex items-center gap-3">
          <span class="w-7 h-7 rounded-lg bg-brand-100 text-brand-700 font-extrabold flex items-center justify-center text-xs">M${item.m}</span>
          <span>${item.title}</span>
        </span>
        <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400"></i>
      </button>
      <div id="cur-m-${item.m}" class="hidden px-5 py-4 border-t border-slate-100 bg-slate-50 text-xs space-y-2">
        <div><strong class="text-brand-800">🔬 Academic & Science Target:</strong> <span class="text-slate-700">${item.academic}</span></div>
        <div><strong class="text-emerald-800">✂️ Tailoring & Business Target:</strong> <span class="text-slate-700">${item.tailoring}</span></div>
        <div><strong class="text-amber-800">📖 Reading & Reflection:</strong> <span class="text-slate-700">${item.reading}</span></div>
      </div>
    </div>
  `).join("");
}

function toggleAccordion(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("hidden");
  lucide.createIcons();
}

// 5. Courses Database Rendering
function renderCourses() {
  const container = document.getElementById("courseCardsGrid");
  const search = (document.getElementById("courseSearchInput")?.value || "").toLowerCase();
  const category = document.getElementById("courseCategoryFilter")?.value || "ALL";
  const status = document.getElementById("courseStatusFilter")?.value || "ALL";

  if (!container) return;

  const filtered = appState.courses.filter(c => {
    const matchSearch = !search || c.name.toLowerCase().includes(search) || c.category.toLowerCase().includes(search) || c.provider.toLowerCase().includes(search);
    const matchCat = category === "ALL" || c.category.toLowerCase().includes(category.toLowerCase());
    const matchStatus = status === "ALL" || c.status === status;
    return matchSearch && matchCat && matchStatus;
  });

  container.innerHTML = filtered.map(c => {
    const score = c.scores?.total_score || 85;
    const statusBg = c.status === "Completed" ? "bg-emerald-100 text-emerald-800 border-emerald-200" : (c.status === "In progress" ? "bg-sky-100 text-sky-800 border-sky-200" : "bg-slate-100 text-slate-600 border-slate-200");

    return `
      <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between hover-card">
        <div>
          <div class="flex items-start justify-between gap-2 mb-2">
            <span class="text-[11px] font-bold text-brand-700 uppercase tracking-wider line-clamp-1">${c.category}</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-brand-50 text-brand-700 border border-brand-200">${score}/100</span>
          </div>
          <h4 class="font-bold text-slate-900 text-sm leading-snug mb-1 line-clamp-2">${c.name}</h4>
          <p class="text-xs text-slate-500 mb-3">${c.provider} • <span class="font-medium text-slate-700">${c.duration}</span></p>
          <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-slate-700 text-xs line-clamp-2 mb-3">
            🎯 <strong>Task:</strong> ${c.practical_assignment || 'Review concepts and create notes.'}
          </div>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
          <select class="text-[11px] font-semibold rounded-lg px-2 py-1 border ${statusBg} focus:outline-none" onchange="updateCourseStatus('${c.id}', this.value)">
            <option value="Not started" ${c.status === 'Not started' ? 'selected' : ''}>Not Started</option>
            <option value="In progress" ${c.status === 'In progress' ? 'selected' : ''}>In Progress</option>
            <option value="Completed" ${c.status === 'Completed' ? 'selected' : ''}>Completed</option>
          </select>

          <button class="text-brand-600 font-bold hover:underline inline-flex items-center gap-1" onclick="openCourseModal('${c.id}')">
            View Task &rarr;
          </button>
        </div>
      </div>
    `;
  }).join("");
}

function updateCourseStatus(courseId, newStatus) {
  const course = appState.courses.find(c => c.id === courseId);
  if (course) {
    setItemStatus(course, appState.course_progress, newStatus);
    renderCourses();
  }
}

function openCourseModal(courseId) {
  const course = appState.courses.find(c => c.id === courseId);
  if (!course) return;

  appState.active_modal_course_id = courseId;
  document.getElementById("courseModalTitle").textContent = course.name;
  document.getElementById("courseModalProvider").textContent = course.provider;
  document.getElementById("courseModalDuration").textContent = course.duration;
  document.getElementById("courseModalAssignment").textContent = course.practical_assignment || "Summarize chapter and build active recall flashcards.";
  document.getElementById("courseModalNotes").textContent = course.notes || "Official course mapped to pre-university preparation.";
  document.getElementById("courseModalLink").href = course.url;

  const btnToggle = document.getElementById("btnToggleCourseStatus");
  btnToggle.textContent = course.status === "Completed" ? "Mark In Progress" : "Mark Completed";
  btnToggle.onclick = () => {
    setItemStatus(course, appState.course_progress, course.status === "Completed" ? "In progress" : "Completed");
    renderCourses();
    closeModal("courseModal");
  };

  document.getElementById("courseModal").classList.remove("hidden");
}

// 6. Volunteering Hub Rendering
function renderVolunteering() {
  const container = document.getElementById("volunteeringCardsGrid");
  const selectOrg = document.getElementById("volModalOrg");
  if (!container) return;

  container.innerHTML = (appState.volunteering || []).map(v => `
    <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between hover-card">
      <div>
        <div class="flex items-start justify-between gap-2 mb-2">
          <span class="text-[10px] font-bold px-2.5 py-0.5 rounded-full ${v.geographic_priority === 'A' ? 'badge-priority-a' : (v.geographic_priority === 'B' ? 'badge-priority-b' : 'badge-priority-c')}">
            Priority ${v.geographic_priority}: ${v.geographic_priority === 'A' ? 'Benin City / Edo' : (v.geographic_priority === 'B' ? 'Nigeria' : 'Online')}
          </span>
          <span class="text-[11px] font-extrabold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">Safety: ${v.safety_score}/100</span>
        </div>
        <h4 class="font-bold text-slate-900 text-sm mb-1">${v.name}</h4>
        <p class="text-xs font-semibold text-rose-700 mb-2">${v.organization}</p>
        <p class="text-xs text-slate-600 leading-relaxed mb-3">${v.description}</p>
        <p class="text-[11px] text-slate-500 mb-2">📍 <strong>Location:</strong> ${v.location}</p>
      </div>

      <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <span class="text-slate-500 font-medium">${v.time_commitment_hours || 4} hrs commitment</span>
        <a href="${v.url}" target="_blank" class="text-brand-600 font-bold hover:underline">Official Portal &rarr;</a>
      </div>
    </div>
  `).join("");

  if (selectOrg) {
    selectOrg.innerHTML = (appState.volunteering || []).map(v => `<option value="${v.organization}">${v.organization} (${v.name})</option>`).join("");
  }
}

// 7. Healthcare Careers Matrix
function renderCareers() {
  const container = document.getElementById("careersAccordion");
  if (!container) return;

  container.innerHTML = (appState.careers || []).map(c => `
    <div class="border border-slate-200 rounded-xl overflow-hidden bg-slate-50/50">
      <button class="w-full text-left px-5 py-4 font-bold text-slate-900 bg-white hover:bg-slate-50 flex items-center justify-between transition" onclick="toggleAccordion('car-${c.id}')">
        <div class="flex items-center gap-3">
          <span class="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-xs">
            <i data-lucide="stethoscope" class="w-4 h-4"></i>
          </span>
          <div>
            <div class="text-sm font-bold text-slate-900">${c.title} <span class="text-xs font-normal text-slate-500">(${c.degree_name})</span></div>
            <div class="text-[11px] text-indigo-700 font-medium">${c.uniben_faculty_dept || 'UNIBEN Medical Sciences'} • ${c.duration_years} Years</div>
          </div>
        </div>
        <i data-lucide="chevron-down" class="w-4 h-4 text-slate-400"></i>
      </button>

      <div id="car-${c.id}" class="hidden px-5 py-4 border-t border-slate-100 bg-slate-50 text-xs space-y-3">
        <p class="text-slate-700 leading-relaxed font-medium">${c.overview}</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 bg-white p-3 rounded-lg border border-slate-200">
          <div>
            <strong class="text-slate-900 block mb-1">📋 Admission Requirements:</strong>
            <p class="text-slate-600"><strong>UTME:</strong> ${Array.isArray(c.utme_subjects) ? c.utme_subjects.join(", ") : c.utme_subjects}</p>
            <p class="text-slate-600 mt-1"><strong>O'Level:</strong> ${c.olevel_requirements}</p>
            <p class="text-slate-600 mt-1"><strong>Regulatory Body:</strong> ${c.regulatory_body}</p>
          </div>
          <div>
            <strong class="text-slate-900 block mb-1">💼 Entrepreneurial Possibilities:</strong>
            <ul class="list-disc list-inside text-slate-600 space-y-0.5">
              ${(c.entrepreneurial_possibilities || []).map(p => `<li>${p}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

// 8. Tailoring Studio & Costing Calculator
function renderTailoring() {
  const container = document.getElementById("tailoringProjectsList");
  if (!container) return;

  const totalProfit = appState.tailoring_projects.reduce((sum, item) => sum + (parseFloat(item.profit) || 0), 0);
  document.getElementById("tailoringNetProfitBadge").textContent = `Net Profit: ₦${totalProfit.toLocaleString('en-US', {minimumFractionDigits: 2})}`;

  container.innerHTML = appState.tailoring_projects.map((p, idx) => `
    <div class="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div>
        <div class="flex items-center gap-2">
          <span class="font-bold text-slate-900 text-sm">${p.project_name}</span>
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Completed</span>
        </div>
        <p class="text-xs text-slate-500 mt-0.5">Client: <strong>${p.customer_name || 'Bespoke Order'}</strong> • Date: ${p.date_completed || 'Recent'}</p>
        <p class="text-xs text-slate-600 mt-1">Skills: ${p.skills_practiced}</p>
      </div>
      <div class="text-right sm:min-w-[140px]">
        <div class="text-sm font-extrabold text-emerald-700">₦${p.selling_price?.toLocaleString('en-US')}</div>
        <div class="text-[11px] text-emerald-600 font-semibold">+₦${p.profit?.toLocaleString('en-US')} profit</div>
      </div>
    </div>
  `).join("");

  // Attach calculator event listeners
  ["calcMaterialCost", "calcHours", "calcRate", "calcOverhead", "calcMargin"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", calculateTailoringPrice);
  });
  calculateTailoringPrice();
}

function calculateTailoringPrice() {
  const mat = parseFloat(document.getElementById("calcMaterialCost")?.value || 0);
  const hours = parseFloat(document.getElementById("calcHours")?.value || 0);
  const rate = parseFloat(document.getElementById("calcRate")?.value || 0);
  const overhead = parseFloat(document.getElementById("calcOverhead")?.value || 0);
  const marginPct = parseFloat(document.getElementById("calcMargin")?.value || 0) / 100;

  const labor = hours * rate;
  const baseCost = mat + labor + overhead;
  const profit = baseCost * marginPct;
  const finalPrice = baseCost + profit;

  document.getElementById("calcBaseCost").textContent = `₦${baseCost.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
  document.getElementById("calcProfit").textContent = `₦${profit.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
  document.getElementById("calcFinalPrice").textContent = `₦${finalPrice.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
}

// 9. UNIBEN Readiness & 5.0 CGPA Simulator
function renderUniben() {
  const container = document.getElementById("cgpaInputsContainer");
  const checklistContainer = document.getElementById("unibenChecklistContainer");
  if (!container || !appState.uniben) return;

  const courses100L = appState.uniben.first_year_pre_med_curriculum?.first_semester || [];
  container.innerHTML = courses100L.map((c, i) => `
    <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200">
      <span class="font-bold text-slate-800">${c.code} (${c.units}u)</span>
      <select class="cgpa-select text-xs border border-slate-300 rounded p-1 font-bold" data-units="${c.units}" onchange="recalculateCGPA()">
        <option value="5">A (5.0)</option>
        <option value="4">B (4.0)</option>
        <option value="3">C (3.0)</option>
        <option value="2">D (2.0)</option>
        <option value="1">E (1.0)</option>
        <option value="0">F (0.0)</option>
      </select>
    </div>
  `).join("");

  recalculateCGPA();

  // Render Checklist
  const checklist = appState.uniben.first_30_days_action_checklist || [];
  checklistContainer.innerHTML = checklist.map(item => {
    const isDone = appState.checklist_completed.includes(item.step);
    return `
      <label class="flex items-start gap-3 p-3 rounded-xl border ${isDone ? 'bg-purple-50/60 border-purple-200' : 'bg-slate-50 border-slate-200'} cursor-pointer transition">
        <input type="checkbox" ${isDone ? 'checked' : ''} class="mt-0.5 rounded text-purple-600 focus:ring-purple-500" onchange="toggleChecklistStep(${item.step})">
        <div>
          <span class="font-bold text-slate-900">${item.day_range}: ${item.action}</span>
        </div>
      </label>
    `;
  }).join("");

  document.getElementById("checklistProgressText").textContent = `${appState.checklist_completed.length} / ${checklist.length} Completed`;
}

function recalculateCGPA() {
  const selects = document.querySelectorAll(".cgpa-select");
  let totalUnits = 0;
  let totalPoints = 0;

  selects.forEach(s => {
    const units = parseInt(s.dataset.units) || 0;
    const gp = parseInt(s.value) || 0;
    totalUnits += units;
    totalPoints += (units * gp);
  });

  const cgpa = totalUnits > 0 ? (totalPoints / totalUnits).toFixed(2) : "0.00";
  document.getElementById("cgpaTotalUnits").textContent = totalUnits;
  document.getElementById("cgpaValue").textContent = cgpa;

  // Same scale as calculate_uniben_cgpa in preuni_system/utils.py
  const value = parseFloat(cgpa);
  let classification = "Probation / Fail";
  if (value >= 4.50) classification = "First Class Honours";
  else if (value >= 3.50) classification = "Second Class Honours (Upper Division)";
  else if (value >= 2.40) classification = "Second Class Honours (Lower Division)";
  else if (value >= 1.50) classification = "Third Class Honours";
  else if (value >= 1.00) classification = "Pass";
  document.getElementById("cgpaClass").textContent = classification;
}

function toggleChecklistStep(step) {
  if (appState.checklist_completed.includes(step)) {
    appState.checklist_completed = appState.checklist_completed.filter(s => s !== step);
  } else {
    appState.checklist_completed.push(step);
  }
  saveState();
  renderUniben();
}

// 10. Reading Library Rendering
function renderReading() {
  const container = document.getElementById("readingBooksGrid");
  if (!container) return;

  container.innerHTML = (appState.reading || []).map(b => `
    <div class="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between hover-card">
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800">Month ${b.month}</span>
          <span class="text-[11px] font-semibold text-slate-500">${b.genre}</span>
        </div>
        <h4 class="font-bold text-slate-900 text-sm mb-1">${b.title}</h4>
        <p class="text-xs font-semibold text-amber-800 mb-2">Author: ${b.author}</p>
        <p class="text-xs text-slate-600 leading-relaxed mb-3">${b.summary}</p>
      </div>

      <div class="p-3 rounded-lg bg-amber-50/60 border border-amber-200/60 text-amber-950 text-xs">
        <strong>📝 Exercise:</strong> ${b.practical_exercise}
      </div>

      <div class="flex items-center justify-between pt-3 mt-3 border-t border-slate-100 text-xs">
        <span class="text-slate-500 font-medium">Reading status</span>
        <select class="text-[11px] font-semibold rounded-lg px-2 py-1 border ${b.status === 'Completed' ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : (b.status === 'Reading' ? 'bg-sky-100 text-sky-800 border-sky-200' : 'bg-slate-100 text-slate-600 border-slate-200')} focus:outline-none" onchange="updateReadingStatus('${b.id}', this.value)">
          <option value="Not read" ${b.status === 'Not read' ? 'selected' : ''}>Not Read</option>
          <option value="Reading" ${b.status === 'Reading' ? 'selected' : ''}>Reading</option>
          <option value="Completed" ${b.status === 'Completed' ? 'selected' : ''}>Completed</option>
        </select>
      </div>
    </div>
  `).join("");
}

function updateReadingStatus(readingId, newStatus) {
  const book = appState.reading.find(b => b.id === readingId);
  if (book) {
    setItemStatus(book, appState.reading_progress, newStatus);
    renderReading();
  }
}

// 11. Soft-Skills Radar Chart & Sliders
let radarChartInstance = null;
const skillNames = [
  "Communication", "Public Speaking", "Critical Thinking", "Problem Solving",
  "Emotional Intelligence", "Confidence", "Leadership", "Teamwork",
  "Time Management", "Financial Discipline", "Customer Service",
  "Negotiation", "Professionalism", "Resilience", "Learning Ability"
];

function selectedQuarter() {
  return document.getElementById("rubricQuarterSelect")?.value || "1";
}

function skillKey(name) {
  return name.toLowerCase().replace(/ /g, "_");
}

function initRubricChart() {
  const ctx = document.getElementById("softSkillsChart");
  if (!ctx) return;

  radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: skillNames,
      datasets: [{
        label: 'Competency Score (1–5)',
        data: [],
        backgroundColor: 'rgba(2, 132, 199, 0.2)',
        borderColor: '#0284c7',
        pointBackgroundColor: '#0284c7',
        borderWidth: 2
      }]
    },
    options: {
      scales: {
        r: {
          min: 0,
          max: 5,
          ticks: { stepSize: 1 }
        }
      }
    }
  });
  renderRubric();
}

// Show the selected quarter's scores (skills not yet scored show as 3)
function renderRubric() {
  const slidersContainer = document.getElementById("skillSlidersContainer");
  const scores = appState.rubric_scores[selectedQuarter()] || {};

  if (radarChartInstance) {
    radarChartInstance.data.datasets[0].data = skillNames.map(name => scores[skillKey(name)] || 3);
    radarChartInstance.update();
  }
  if (!slidersContainer) return;

  slidersContainer.innerHTML = skillNames.map(name => {
    const key = skillKey(name);
    const val = scores[key] || 3;
    return `
      <div class="space-y-1">
        <div class="flex justify-between font-semibold text-slate-700">
          <span>${name}</span>
          <span id="val-${key}" class="font-bold text-brand-600">${val}/5</span>
        </div>
        <input type="range" min="1" max="5" value="${val}" class="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600" oninput="updateSkillSlider('${key}', this.value)">
      </div>
    `;
  }).join("");
}

function updateSkillSlider(key, val) {
  const lbl = document.getElementById(`val-${key}`);
  if (lbl) lbl.textContent = `${val}/5`;

  const q = selectedQuarter();
  if (!appState.rubric_scores[q]) appState.rubric_scores[q] = {};
  appState.rubric_scores[q][key] = parseInt(val);

  if (radarChartInstance) {
    radarChartInstance.data.datasets[0].data = skillNames.map(name => appState.rubric_scores[q][skillKey(name)] || 3);
    radarChartInstance.update();
  }
}

// 12. Email Previews: this week's real emails, rendered by `make bundle` (preuni_system/bundle_dashboard.py)
const EMAIL_PREVIEW_LABELS = {
  daily_alert: "daily learning guide",
  weekly_digest: "weekly digest",
  immediate_alert: "immediate alert"
};

function initEmailPreview() {
  document.getElementById("btnPreviewDailyAlert")?.addEventListener("click", () => {
    fetchEmailTemplate("daily_alert");
  });
  document.getElementById("btnPreviewDigest")?.addEventListener("click", () => {
    fetchEmailTemplate("weekly_digest");
  });
  document.getElementById("btnPreviewAlert")?.addEventListener("click", () => {
    fetchEmailTemplate("immediate_alert");
  });

  const generated = (window.PREUNI_CONFIG || {}).previews_generated;
  const note = document.getElementById("emailPreviewNote");
  if (note && generated) {
    note.textContent = `This week's emails as of ${generated}, rendered with the same templates the scheduled jobs use.`;
  }
}

async function fetchEmailTemplate(type) {
  const iframe = document.getElementById("emailPreviewFrame");
  if (!iframe) return;

  try {
    const res = await fetch(`emails/${type}.html`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    iframe.srcdoc = await res.text();
  } catch (e) {
    iframe.srcdoc = `<p style="padding:20px;font-family:sans-serif;">No ${EMAIL_PREVIEW_LABELS[type]} preview is available yet. Previews are created when the dashboard is rebuilt (<code>make bundle</code>, or automatically when it deploys).</p>`;
  }
}

// 13. Modals and Action Handlers
function initModalsAndEvents() {
  document.getElementById("btnLogVolunteerModal")?.addEventListener("click", () => {
    document.getElementById("volunteerModal")?.classList.remove("hidden");
  });
  document.getElementById("btnCloseVolModal")?.addEventListener("click", () => {
    closeModal("volunteerModal");
  });
  document.getElementById("btnCloseCourseModal")?.addEventListener("click", () => {
    closeModal("courseModal");
  });

  document.getElementById("btnSaveVolunteerHours")?.addEventListener("click", () => {
    const org = document.getElementById("volModalOrg").value;
    const hours = parseInt(document.getElementById("volModalHours").value) || 0;
    const reflection = document.getElementById("volModalReflection").value;

    appState.volunteer_logs.push({
      id: "vlog-" + Date.now(),
      organization: org,
      hours: hours,
      reflection: reflection,
      date: new Date().toISOString().split("T")[0]
    });
    saveState();
    closeModal("volunteerModal");
    alert(`✅ Successfully logged ${hours} volunteer hours with ${org}!`);
  });

  document.getElementById("btnSaveTailoringProject")?.addEventListener("click", () => {
    const name = document.getElementById("calcProjectName").value || "Custom Bespoke Project";
    const mat = parseFloat(document.getElementById("calcMaterialCost").value || 0);
    const hours = parseFloat(document.getElementById("calcHours").value || 0);
    const rate = parseFloat(document.getElementById("calcRate").value || 0);
    const overhead = parseFloat(document.getElementById("calcOverhead").value || 0);
    const marginPct = parseFloat(document.getElementById("calcMargin").value || 0) / 100;

    const baseCost = mat + (hours * rate) + overhead;
    const profit = baseCost * marginPct;
    const sellingPrice = baseCost + profit;

    appState.tailoring_projects.unshift({
      id: "tailor-" + Date.now(),
      project_name: name,
      garment_type: "Bespoke Garment",
      date_completed: new Date().toISOString().split("T")[0],
      material_cost: mat,
      labor_cost: hours * rate,
      selling_price: sellingPrice,
      profit: profit,
      customer_name: "Client Commission",
      skills_practiced: "Scientific costing, fitting, pattern drafting"
    });

    saveState();
    renderTailoring();
    alert(`✅ Project "${name}" saved! Quoted price: ₦${sellingPrice.toLocaleString('en-US', {minimumFractionDigits: 2})}`);
  });

  document.getElementById("courseSearchInput")?.addEventListener("input", renderCourses);
  document.getElementById("courseCategoryFilter")?.addEventListener("change", renderCourses);
  document.getElementById("courseStatusFilter")?.addEventListener("change", renderCourses);

  document.getElementById("btnSaveRubric")?.addEventListener("click", () => {
    saveState();
    alert("✅ Quarterly Soft-Skills Rubric saved successfully!");
  });

  document.getElementById("rubricQuarterSelect")?.addEventListener("change", renderRubric);

  // Full backup of this browser's progress, including personal notes - keep it private
  document.getElementById("btnExportData")?.addEventListener("click", () => {
    const today = new Date().toISOString().split('T')[0];
    downloadJson({ format: "preuni-backup", saved: new Date().toISOString(), ...currentProgressState() }, `lara_preuni_system_backup_${today}.json`);
  });

  document.getElementById("btnRestoreData")?.addEventListener("click", () => {
    document.getElementById("restoreFileInput")?.click();
  });

  document.getElementById("restoreFileInput")?.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try {
      const backup = JSON.parse(await file.text());
      const merged = PreuniProgress.mergeStates(currentProgressState(), backup);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
      alert("✅ Backup restored. Reloading your progress...");
      location.reload();
    } catch (e) {
      alert(`❌ Could not restore this file: ${e.message}`);
    }
    event.target.value = "";
  });

  // Status-only file that the email system and other devices read from data/progress.json
  document.getElementById("btnShareProgress")?.addEventListener("click", () => {
    downloadJson(PreuniProgress.buildSharedProgress(currentProgressState()), "progress.json");
    alert("progress.json downloaded (course and book statuses only - no personal notes).\n\n" +
      "Upload it to the data folder of the GitHub repository, replacing data/progress.json. " +
      "The email alerts will then skip finished courses, and every device shows the same progress once the dashboard redeploys.");
  });

  document.getElementById("btnResetData")?.addEventListener("click", () => {
    if (confirm("Reset local progress data to default state?")) {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(LEGACY_STORAGE_KEY);
      location.reload();
    }
  });
}

function downloadJson(data, filename) {
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
}

function closeModal(id) {
  document.getElementById(id)?.classList.add("hidden");
}
