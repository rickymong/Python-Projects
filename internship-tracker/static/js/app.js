const STATUS_LABELS = {
  queued: "Queued", ready: "Ready", applied: "Applied", interview: "Interview",
  offer: "Offer", rejected: "Rejected", archived: "Archived",
};
const STATUS_ORDER = ["queued", "ready", "applied", "interview", "offer", "rejected", "archived"];

let currentFilter = "all";
let skills = [];
let jobsCache = [];

/* ---------------- API helpers ---------------- */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  let body = null;
  try { body = await res.json(); } catch (_) {}
  if (!res.ok) {
    const err = new Error(body?.message || body?.error || `Request failed (${res.status})`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

/* ---------------- toasts ---------------- */
function toast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; setTimeout(() => el.remove(), 300); }, 4200);
}

/* ---------------- theme ---------------- */
function initTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon();
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme")
      || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateThemeIcon();
  });
}
function updateThemeIcon() {
  const current = document.documentElement.getAttribute("data-theme")
    || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  document.getElementById("theme-toggle").textContent = current === "dark" ? "☀️" : "🌙";
}

/* ---------------- tabs ---------------- */
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

/* ---------------- stats ---------------- */
function renderStats(stats) {
  const tiles = [
    { label: "Tracked", value: stats.total, dot: "var(--blue)", sub: "postings in your board" },
    { label: "Applied", value: stats.applied, dot: "var(--aqua)", sub: "you've submitted" },
    { label: "Interviews", value: stats.interviews, dot: "var(--violet)", sub: "in progress" },
    { label: "Avg. match", value: `${stats.avg_match}%`, dot: "var(--seq-450)", sub: "keyword alignment" },
  ];
  const row = document.getElementById("stats-row");
  row.innerHTML = "";
  tiles.forEach((t, i) => {
    const el = document.createElement("div");
    el.className = "stat-tile";
    el.style.animationDelay = `${i * 40}ms`;
    el.innerHTML = `
      <div class="stat-label"><span class="stat-dot" style="background:${t.dot}"></span>${t.label}</div>
      <div class="stat-value">${t.value}</div>
      <div class="stat-sub">${t.sub}</div>`;
    row.appendChild(el);
  });
}

async function loadStats() {
  const stats = await api("/api/stats");
  renderStats(stats);
}

/* ---------------- job board ---------------- */
function initFilters() {
  const wrap = document.getElementById("status-filters");
  const chips = [{ key: "all", label: "All" }, ...STATUS_ORDER.map(s => ({ key: s, label: STATUS_LABELS[s] }))];
  wrap.innerHTML = "";
  chips.forEach(c => {
    const btn = document.createElement("button");
    btn.className = "filter-chip" + (c.key === "all" ? " active" : "");
    btn.textContent = c.label;
    btn.dataset.key = c.key;
    btn.addEventListener("click", () => {
      currentFilter = c.key;
      wrap.querySelectorAll(".filter-chip").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      renderJobs();
    });
    wrap.appendChild(btn);
  });
}

async function loadJobs() {
  jobsCache = await api("/api/jobs");
  renderJobs();
}

function renderJobs() {
  const list = document.getElementById("job-list");
  const empty = document.getElementById("empty-state");
  const filtered = currentFilter === "all" ? jobsCache : jobsCache.filter(j => j.status === currentFilter);
  list.innerHTML = "";
  if (filtered.length === 0) {
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");
  const tpl = document.getElementById("tpl-job-card");
  filtered.forEach((job, i) => {
    const node = tpl.content.cloneNode(true);
    const card = node.querySelector(".job-card");
    card.style.animationDelay = `${Math.min(i, 8) * 35}ms`;
    node.querySelector(".job-title").textContent = job.title;
    node.querySelector(".job-company").textContent = job.company;

    const pill = node.querySelector(".status-pill");
    pill.textContent = STATUS_LABELS[job.status];
    pill.classList.add(`status-${job.status}`);

    const metaBits = [job.location, job.deadline ? `Deadline ${job.deadline}` : null].filter(Boolean);
    node.querySelector(".job-meta").textContent = metaBits.join(" · ");

    const fill = node.querySelector(".match-fill");
    const label = node.querySelector(".match-label");
    if (job.resume_path) {
      requestAnimationFrame(() => { fill.style.width = `${job.match_score}%`; });
      label.textContent = `${job.match_score}% match`;
    } else {
      fill.style.width = "0%";
      label.textContent = "not tailored yet";
    }

    if (job.keywords_matched?.length) {
      node.querySelector(".matched-row").classList.remove("hidden");
      const chips = node.querySelector(".matched-chips");
      job.keywords_matched.forEach(k => {
        const c = document.createElement("span"); c.className = "kw-chip"; c.textContent = k; chips.appendChild(c);
      });
    }
    if (job.keywords_missing?.length) {
      node.querySelector(".missing-row").classList.remove("hidden");
      const chips = node.querySelector(".missing-chips");
      job.keywords_missing.slice(0, 8).forEach(k => {
        const c = document.createElement("span"); c.className = "kw-chip"; c.textContent = k; chips.appendChild(c);
      });
    }

    const tailorBtn = node.querySelector(".tailor-btn");
    tailorBtn.addEventListener("click", () => tailorOne(job.id, tailorBtn));

    const resumeLink = node.querySelector(".resume-link");
    const coverLink = node.querySelector(".cover-link");
    if (job.resume_path) { resumeLink.href = `/api/jobs/${job.id}/download/resume`; resumeLink.classList.remove("hidden"); }
    if (job.cover_letter_path) { coverLink.href = `/api/jobs/${job.id}/download/cover-letter`; coverLink.classList.remove("hidden"); }

    const openLink = node.querySelector(".open-link");
    if (job.url) { openLink.href = job.url; openLink.classList.remove("hidden"); }

    const select = node.querySelector(".status-select");
    STATUS_ORDER.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s; opt.textContent = STATUS_LABELS[s];
      if (s === job.status) opt.selected = true;
      select.appendChild(opt);
    });
    select.addEventListener("change", async () => {
      try {
        await api(`/api/jobs/${job.id}`, { method: "PATCH", body: JSON.stringify({ status: select.value }) });
        toast(`Marked "${job.title}" as ${STATUS_LABELS[select.value]}`, "success");
        await Promise.all([loadJobs(), loadStats()]);
      } catch (e) { toast(e.message, "error"); }
    });

    node.querySelector(".delete-btn").addEventListener("click", async () => {
      if (!confirm(`Remove "${job.title}" at ${job.company} from your tracker?`)) return;
      await api(`/api/jobs/${job.id}`, { method: "DELETE" });
      toast("Removed from tracker", "success");
      await Promise.all([loadJobs(), loadStats()]);
    });

    list.appendChild(node);
  });
}

async function tailorOne(jobId, btn) {
  btn.disabled = true;
  const original = btn.textContent;
  btn.textContent = "Tailoring…";
  try {
    await api(`/api/jobs/${jobId}/tailor`, { method: "POST" });
    toast("Draft resume + cover letter generated", "success");
    await Promise.all([loadJobs(), loadStats()]);
  } catch (e) {
    toast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

/* ---------------- add posting ---------------- */
function initAddForm() {
  const form = document.getElementById("add-job-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      await api("/api/jobs", { method: "POST", body: JSON.stringify(data) });
      toast(`Added ${data.title} at ${data.company}`, "success");
      form.reset();
      document.querySelector('.tab-btn[data-tab="board"]').click();
      await Promise.all([loadJobs(), loadStats()]);
    } catch (e) {
      if (e.status === 409) toast(e.message, "error");
      else toast(e.message, "error");
    }
  });
}

/* ---------------- activate assistant ---------------- */
function initActivate() {
  const btn = document.getElementById("activate-btn");
  btn.addEventListener("click", async () => {
    btn.classList.add("running");
    btn.disabled = true;
    const label = btn.querySelector(".activate-label");
    const originalLabel = label.textContent;
    label.textContent = "Scanning queue…";
    try {
      const result = await api("/api/activate", { method: "POST" });
      if (result.tailored === 0) {
        toast("Nothing queued to tailor — add a posting first.", "info");
      } else {
        toast(`Tailored materials for ${result.tailored} posting${result.tailored === 1 ? "" : "s"}. Review before sending anything.`, "success");
      }
      await Promise.all([loadJobs(), loadStats()]);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      btn.classList.remove("running");
      btn.disabled = false;
      label.textContent = originalLabel;
    }
  });
}

/* ---------------- profile ---------------- */
function renderSkillChips() {
  const wrap = document.getElementById("skills-chips");
  wrap.innerHTML = "";
  skills.forEach((s, i) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.innerHTML = `${s} <button type="button" aria-label="remove">×</button>`;
    chip.querySelector("button").addEventListener("click", () => { skills.splice(i, 1); renderSkillChips(); });
    wrap.appendChild(chip);
  });
}

function initSkillsInput() {
  const input = document.getElementById("skills-input");
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const val = input.value.trim().replace(/,$/, "");
      if (val && !skills.some(s => s.toLowerCase() === val.toLowerCase())) {
        skills.push(val);
        renderSkillChips();
      }
      input.value = "";
    }
  });
  input.addEventListener("blur", () => {
    const val = input.value.trim();
    if (val && !skills.some(s => s.toLowerCase() === val.toLowerCase())) {
      skills.push(val);
      renderSkillChips();
    }
    input.value = "";
  });
}

function addRepeatBlock(kind, data = {}) {
  const tpl = document.getElementById(`tpl-${kind}`);
  const list = document.getElementById(`${kind}-list`);
  const node = tpl.content.cloneNode(true);
  const block = node.querySelector(".repeat-block");
  block.querySelectorAll("[data-field]").forEach(el => {
    const field = el.dataset.field;
    if (field === "bullets") el.value = (data.bullets || []).join("\n");
    else el.value = data[field] || "";
  });
  block.querySelector(".remove-btn").addEventListener("click", () => block.remove());
  list.appendChild(node);
}

function collectRepeatBlocks(kind) {
  return [...document.querySelectorAll(`#${kind}-list .repeat-block`)].map(block => {
    const obj = {};
    block.querySelectorAll("[data-field]").forEach(el => {
      const field = el.dataset.field;
      if (field === "bullets") obj.bullets = el.value.split("\n").map(s => s.trim()).filter(Boolean);
      else obj[field] = el.value.trim();
    });
    return obj;
  });
}

async function loadProfile() {
  const profile = await api("/api/profile");
  const form = document.getElementById("profile-form");
  ["name", "email", "phone", "location", "linkedin_url", "portfolio_url", "summary"].forEach(f => {
    if (form.elements[f]) form.elements[f].value = profile[f] || "";
  });
  skills = [...(profile.skills || [])];
  renderSkillChips();
  document.getElementById("experience-list").innerHTML = "";
  (profile.experience || []).forEach(exp => addRepeatBlock("experience", exp));
  document.getElementById("education-list").innerHTML = "";
  (profile.education || []).forEach(edu => addRepeatBlock("education", edu));
}

function initProfileForm() {
  document.getElementById("add-experience").addEventListener("click", () => addRepeatBlock("experience"));
  document.getElementById("add-education").addEventListener("click", () => addRepeatBlock("education"));

  const form = document.getElementById("profile-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fields = Object.fromEntries(new FormData(form).entries());
    fields.skills = skills;
    fields.experience = collectRepeatBlocks("experience");
    fields.education = collectRepeatBlocks("education");
    try {
      await api("/api/profile", { method: "PUT", body: JSON.stringify(fields) });
      toast("Profile saved", "success");
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

/* ---------------- init ---------------- */
(async function init() {
  initTheme();
  initTabs();
  initFilters();
  initAddForm();
  initActivate();
  initSkillsInput();
  initProfileForm();
  try {
    await Promise.all([loadJobs(), loadStats(), loadProfile()]);
  } catch (e) {
    toast(`Failed to load: ${e.message}`, "error");
  }
})();
