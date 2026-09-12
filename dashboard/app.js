/**
 * Main Application Logic for Pre-University Development & Opportunity System Dashboard.
 * Offline-first, reactive state with localStorage persistence.
 */

// Global State
let appState = {
  courses: [],
  volunteering: [],
  careers: [],
  scholarships: [],
  reading: [],
  uniben: null,
  soft_skills: [],
  tailoring_projects: [
    {
      id: "tailor-001",
      project_name: "Bespoke Peplum Blouse & Pencil Skirt",
      garment_type: "Skirt & Blouse",
      date_completed: "2026-08-20",
      material_cost: 3200,
      labor_cost: 4200,
      selling_price: 11000,
      profit: 3600,
      customer_name: "Mrs. Osas",
      skills_practiced: "Invisible zipper insertion, princess darts, neckline facing"
    }
  ],
  volunteer_logs: [],
  checklist_completed: [1, 2],
  rubric_scores: {
    1: { communication: 3, public_speaking: 2, critical_thinking: 3, problem_solving: 3, emotional_intelligence: 3, confidence: 3, leadership: 3, teamwork: 4, time_management: 3, financial_discipline: 3, customer_service: 3, negotiation: 2, professionalism: 4, resilience: 3, learning_ability: 4 }
  },
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
function loadData() {
  const localSaved = localStorage.getItem("PREUNI_STATE_V1");
  const baseData = window.PREUNI_DATA || {};

  appState.courses = baseData.courses || [];
  appState.volunteering = baseData.volunteering || [];
  appState.careers = baseData.healthcare_careers || [];
  appState.scholarships = baseData.scholarships_competitions || [];
  appState.reading = baseData.reading_list || [];
  appState.uniben = baseData.uniben_data || null;
  appState.soft_skills = baseData.soft_skills || [];

  if (localSaved) {
    try {
      const parsed = JSON.parse(localSaved);
      if (parsed.courses) appState.courses = parsed.courses;
      if (parsed.tailoring_projects) appState.tailoring_projects = parsed.tailoring_projects;
      if (parsed.volunteer_logs) appState.volunteer_logs = parsed.volunteer_logs;
      if (parsed.checklist_completed) appState.checklist_completed = parsed.checklist_completed;
      if (parsed.rubric_scores) appState.rubric_scores = parsed.rubric_scores;
    } catch (e) {
      console.error("Error loading localStorage state:", e);
    }
  }
}

function saveState() {
  localStorage.setItem("PREUNI_STATE_V1", JSON.stringify({
    courses: appState.courses,
    tailoring_projects: appState.tailoring_projects,
    volunteer_logs: appState.volunteer_logs,
    checklist_completed: appState.checklist_completed,
    rubric_scores: appState.rubric_scores
  }));
  updateSummaryMetrics();
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

  const topOpps = (appState.scholarships || []).slice(0, 4);
  container.innerHTML = topOpps.map(op => `
    <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex flex-col gap-1">
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-900 line-clamp-1">${op.title}</span>
        <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">${op.total_score || 85}/100</span>
      </div>
      <p class="text-slate-500 text-[11px] line-clamp-2">${op.description}</p>
      <div class="flex items-center justify-between text-[11px] mt-1 pt-1 border-t border-slate-200/60">
        <span class="text-rose-600 font-semibold">Deadline: ${op.deadline || 'Ongoing'}</span>
        <a href="${op.url}" target="_blank" class="text-brand-600 font-bold hover:underline">Apply &rarr;</a>
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
    { m: 3, title: "Human Anatomy, Vital Signs & Dexterity", academic: "Cardiovascular & Vital Signs (Penn on Coursera)", tailoring: "Intricate hand-stitching linking craft to clinical finesse", reading: "Gifted Hands by Ben Carson" },
    { m: 4, title: "Digital & Financial Costing Systems", academic: "Healthcare Math, dosage calculations & Excel budgets", tailoring: "Scientific unit costing formula on 3 bespoke garments", reading: "Things Fall Apart by Chinua Achebe" },
    { m: 5, title: "Communication, Public Speaking & Bedside Empathy", academic: "Medical Genetics & Patient Communication", tailoring: "5 structured customer intake consultations", reading: "The Richest Man in Babylon" },
    { m: 6, title: "Money, Entrepreneurship & Sewing for Charity", academic: "Organic Chemistry functional groups & biomolecules", tailoring: "Mend 10 school uniforms for community donation drive", reading: "The E-Myth Revisited by Michael Gerber" },
    { m: 7, title: "Research Methodology & Bioethics", academic: "Writing in the Sciences (Stanford) & PubMed deconstruction", tailoring: "Zero-waste fabric pattern layouts", reading: "The Immortal Life of Henrietta Lacks" },
    { m: 8, title: "Healthcare Career Matrix & Public Health", academic: "Immunology & Antimicrobial Resistance (WHO)", tailoring: "Construct professional medical scrub set prototype", reading: "Mountains Beyond Mountains (Dr. Paul Farmer)" },
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
    course.status = newStatus;
    saveState();
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
    course.status = course.status === "Completed" ? "In progress" : "Completed";
    saveState();
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

  let classification = "Pass";
  if (cgpa >= 4.50) classification = "First Class Honours";
  else if (cgpa >= 3.50) classification = "Second Class Honours (Upper Division)";
  else if (cgpa >= 2.40) classification = "Second Class Honours (Lower Division)";
  else if (cgpa >= 1.50) classification = "Third Class Honours";
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
    </div>
  `).join("");
}

// 11. Soft-Skills Radar Chart & Sliders
let radarChartInstance = null;
const skillNames = [
  "Communication", "Public Speaking", "Critical Thinking", "Problem Solving",
  "Emotional Intelligence", "Confidence", "Leadership", "Teamwork",
  "Time Management", "Financial Discipline", "Customer Service",
  "Negotiation", "Professionalism", "Resilience", "Learning Ability"
];

function initRubricChart() {
  const ctx = document.getElementById("softSkillsChart");
  const slidersContainer = document.getElementById("skillSlidersContainer");
  if (!ctx || !slidersContainer) return;

  const currentScores = appState.rubric_scores[1] || {};
  const dataValues = skillNames.map(k => currentScores[k.toLowerCase().replace(/ /g, "_")] || 3);

  radarChartInstance = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: skillNames,
      datasets: [{
        label: 'Competency Score (1–5)',
        data: dataValues,
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

  slidersContainer.innerHTML = skillNames.map(name => {
    const key = name.toLowerCase().replace(/ /g, "_");
    const val = currentScores[key] || 3;
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

  const q = document.getElementById("rubricQuarterSelect")?.value || 1;
  if (!appState.rubric_scores[q]) appState.rubric_scores[q] = {};
  appState.rubric_scores[q][key] = parseInt(val);

  if (radarChartInstance) {
    const dataValues = skillNames.map(k => appState.rubric_scores[q][k.toLowerCase().replace(/ /g, "_")] || 3);
    radarChartInstance.data.datasets[0].data = dataValues;
    radarChartInstance.update();
  }
}

// 12. Email Previews
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
}

function fetchEmailTemplate(type) {
  const iframe = document.getElementById("emailPreviewFrame");
  if (!iframe) return;

  if (type === "daily_alert") {
    iframe.srcdoc = `
      <div style="font-family: sans-serif; padding: 24px; color: #1e293b; background: #f8fafc;">
        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 20px; border-radius: 8px;">
          <span style="background: #0284c7; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">PERSONALIZED DAILY LEARNING GUIDE</span>
          <h2 style="margin:8px 0 2px;">General Chemistry: Atomic Structure & Redox</h2>
          <p style="margin:0; font-size: 13px; color: #94a3b8;">Month 1 • Week 2 • Lara (UNIBEN Healthcare Preparation Track)</p>
        </div>
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 14px; margin-top: 16px;">
          <strong style="color: #1d4ed8; font-size: 12px; text-transform: uppercase;">Today's Recommended Focus:</strong>
          <p style="margin: 4px 0 0; color: #1e3a8a; font-weight: bold; font-size: 14px;">Write electron configurations for elements 1 to 30 and balance 5 redox reactions.</p>
        </div>
        <h3 style="color: #16a34a; margin-top: 20px;">🆕 Learn Now (Matched to Current Topic)</h3>
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px;">
          <div style="display:flex; justify-content:space-between;">
            <strong>High School Chemistry: Atomic Structure & Bonding</strong>
            <span style="background: #dcfce7; color: #15803d; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Score: 92/100</span>
          </div>
          <p style="font-size: 12px; color: #64748b; margin: 4px 0;">Provider: Khan Academy • Est. Time: 45 mins • Cost: Free</p>
          <p style="font-size: 12px; color: #15803d;"><strong>Why it matches:</strong> Directly covers electron orbitals, spdf notation, and periodic trends.</p>
        </div>
        <h3 style="color: #0284c7; margin-top: 16px;">🎯 Good Long-Term Match</h3>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px;">
          <div style="display:flex; justify-content:space-between;">
            <strong>Organic Chemistry: Functional Groups & Reactions</strong>
            <span style="background: #e0f2fe; color: #0284c7; font-weight: bold; padding: 2px 6px; border-radius: 4px; font-size: 11px;">Score: 95/100</span>
          </div>
          <p style="font-size: 12px; color: #64748b; margin: 4px 0;">Where it fits: Month 6 Biomolecules & UNIBEN 100L General Chemistry (CHM102)</p>
        </div>
      </div>
    `;
  } else if (type === "weekly_digest") {
    iframe.srcdoc = `
      <div style="font-family: sans-serif; padding: 24px; color: #1e293b;">
        <div style="background: #0f172a; color: white; padding: 20px; border-radius: 8px;">
          <h2 style="margin:0;">THIS WEEK'S PRE-UNIVERSITY DEVELOPMENT DIGEST</h2>
          <p style="margin:4px 0 0; font-size: 13px; color: #94a3b8;">Month 1 • Week 1 • Lara (UNIBEN Healthcare Preparation Track)</p>
        </div>
        <h3 style="color: #0284c7; margin-top: 20px;">🌟 Top Opportunities of the Week</h3>
        <p>1. Seplat Energy PEARLs JV Scholarship (₦300,000 / yr) • Score: 99/100</p>
        <p>2. Nigerian Red Cross Society Youth Health Volunteers (Edo Branch) • Score: 99/100</p>
        <h3 style="color: #0284c7;">🎯 This Week's Skill & Challenge</h3>
        <p><strong>Skill:</strong> Active Listening & Professional Email Communication</p>
        <p><strong>Challenge:</strong> Diagram blood flow pathway through the 4 heart chambers.</p>
        <h3 style="color: #0284c7;">✂️ Tailoring Goal</h3>
        <p>Calculate full costing (Fabric + Labor + Overhead + Margin) for your current peplum top.</p>
      </div>
    `;
  } else {
    iframe.srcdoc = `
      <div style="font-family: sans-serif; padding: 24px; color: #1e293b;">
        <div style="background: #0284c7; color: white; padding: 20px; border-radius: 8px;">
          <span style="background: #22c55e; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">SCORE: 99/100</span>
          <h2 style="margin:8px 0 0;">[PRE-UNIVERSITY ALERT] Seplat Energy PEARLs JV Scholarship</h2>
        </div>
        <p style="margin-top: 16px;">A verified top-tier scholarship opportunity for Edo State residents entering UNIBEN has opened.</p>
        <p><strong>Deadline:</strong> August 31, 2027 • <strong>Cost:</strong> Free to apply</p>
        <a href="https://www.seplatenergy.com" target="_blank" style="display:inline-block; background:#0284c7; color:white; padding:10px 16px; border-radius:6px; text-decoration:none; font-weight:bold; margin-top:10px;">Access Official Application &rarr;</a>
      </div>
    `;
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

  document.getElementById("btnExportData")?.addEventListener("click", () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `lara_preuni_system_backup_${new Date().toISOString().split('T')[0]}.json`);
    dlAnchor.click();
  });

  document.getElementById("btnResetData")?.addEventListener("click", () => {
    if (confirm("Reset local progress data to default state?")) {
      localStorage.removeItem("PREUNI_STATE_V1");
      location.reload();
    }
  });
}

function closeModal(id) {
  document.getElementById(id)?.classList.add("hidden");
}
