/**
 * Progress helpers for the dashboard (no DOM access, so they also run under Node for tests).
 *
 * Progress is stored per item ID as {status, updated}. Course and book details always come
 * from the bundled data (data.js), so dataset updates such as fixed links reach every browser,
 * and when two sources disagree the most recently updated status wins.
 */
(function (root) {
  // Same scale as Config.STUDY_LEVELS in preuni_system/config.py
  const STUDY_LEVELS = ["secondary", "pre-university", "100L", "200L", "300L+", "postgraduate"];
  // Sample project that earlier versions pre-filled into every browser
  const DEMO_TAILORING_IDS = ["tailor-001"];

  function levelBounds(minLevel, maxLevel, studentLevel) {
    const student = STUDY_LEVELS.indexOf(studentLevel);
    const lowest = minLevel ? STUDY_LEVELS.indexOf(minLevel) : 0;
    const highest = maxLevel ? STUDY_LEVELS.indexOf(maxLevel) : STUDY_LEVELS.length - 1;
    return student < 0 || lowest < 0 || highest < 0 ? null : [lowest, highest, student];
  }

  /** True if a student at studentLevel can apply now. */
  function isLevelEligible(minLevel, maxLevel, studentLevel) {
    const b = levelBounds(minLevel, maxLevel, studentLevel);
    return !!b && b[0] <= b[2] && b[2] <= b[1];
  }

  /** True if the student can apply now or later at university (not outgrown, not postgraduate-only). */
  function isLevelRelevant(minLevel, maxLevel, studentLevel) {
    const b = levelBounds(minLevel, maxLevel, studentLevel);
    return !!b && b[1] >= b[2] && minLevel !== "postgraduate";
  }

  /** Merge {id: {status, updated}} maps; for each ID the most recently updated entry wins. */
  function mergeProgress(...maps) {
    const merged = {};
    maps.forEach(map => Object.entries(map || {}).forEach(([id, entry]) => {
      if (!entry || !entry.status) return;
      if (!merged[id] || (entry.updated || "") > (merged[id].updated || "")) merged[id] = entry;
    }));
    return merged;
  }

  /** Copy items with their status taken from the progress map (falling back to the item's own status). */
  function applyProgress(items, progress, defaultStatus) {
    return (items || []).map(item => ({
      ...item,
      status: (progress[item.id] && progress[item.id].status) || item.status || defaultStatus
    }));
  }

  function emptyState() {
    return {
      version: 2,
      course_progress: {},
      reading_progress: {},
      tailoring_projects: [],
      volunteer_logs: [],
      checklist_completed: [],
      rubric_scores: {}
    };
  }

  /**
   * Convert saved state or a backup file from any version to version 2.
   * Version 1 stored whole course objects, which froze old course details in the browser.
   */
  function normalizeState(saved, now) {
    const state = emptyState();
    if (!saved || typeof saved !== "object") return state;
    const stamp = now || new Date().toISOString();

    if (saved.version === 2) {
      Object.keys(state).forEach(key => {
        if (key !== "version" && saved[key] !== undefined) state[key] = saved[key];
      });
    } else {
      (saved.courses || []).forEach(c => {
        if (c && c.id && c.status && c.status !== "Not started") state.course_progress[c.id] = { status: c.status, updated: stamp };
      });
      (saved.reading || []).forEach(r => {
        if (r && r.id && r.status && r.status !== "Not read") state.reading_progress[r.id] = { status: r.status, updated: stamp };
      });
      state.tailoring_projects = saved.tailoring_projects || [];
      state.volunteer_logs = saved.volunteer_logs || [];
      state.checklist_completed = saved.checklist_completed || [];
      state.rubric_scores = saved.rubric_scores || {};
    }
    state.tailoring_projects = state.tailoring_projects.filter(p => p && !DEMO_TAILORING_IDS.includes(p.id));
    return state;
  }

  /** Merge a restored backup into the current state without losing anything from either. */
  function mergeStates(current, incoming) {
    const a = normalizeState(current);
    const b = normalizeState(incoming);
    const unionById = (xs, ys) => {
      const byId = new Map();
      [...xs, ...ys].forEach(x => { if (x && x.id && !byId.has(x.id)) byId.set(x.id, x); });
      return [...byId.values()];
    };
    return {
      version: 2,
      course_progress: mergeProgress(a.course_progress, b.course_progress),
      reading_progress: mergeProgress(a.reading_progress, b.reading_progress),
      tailoring_projects: unionById(a.tailoring_projects, b.tailoring_projects),
      volunteer_logs: unionById(a.volunteer_logs, b.volunteer_logs),
      checklist_completed: [...new Set([...a.checklist_completed, ...b.checklist_completed])],
      rubric_scores: { ...a.rubric_scores, ...b.rubric_scores }
    };
  }

  /** Status-only file for data/progress.json: no reflections, customer names or other notes. */
  function buildSharedProgress(state, now) {
    return {
      updated: now || new Date().toISOString(),
      courses: state.course_progress || {},
      reading: state.reading_progress || {}
    };
  }

  const api = {
    STUDY_LEVELS, isLevelEligible, isLevelRelevant, mergeProgress, applyProgress,
    emptyState, normalizeState, mergeStates, buildSharedProgress
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.PreuniProgress = api;
})(typeof window !== "undefined" ? window : this);
