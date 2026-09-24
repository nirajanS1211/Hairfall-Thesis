const $ = (s) => document.querySelector(s);
const api = async (path, opts = {}) => {
  const r = await fetch(path, { headers: { "content-type": "application/json" }, ...opts });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const stripAnsi = (s) => String(s).replace(/\x1b\[[0-9;]*m/g, "");
const fmtTime = (s) => (s == null ? "" : s < 60 ? `${s.toFixed(1)}s` : s < 3600 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.floor(s / 3600)}h ${Math.round((s % 3600) / 60)}m`);

let steps = [];
let selected = localStorageGet("step");
const drafts = {};          // edited code per step (not yet run)
let viewRun = null;         // a run picked from history (null = latest)
let lastRender = "";

function localStorageGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function localStorageSet(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } }

/* ---------------- tabs ---------------- */
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  $("#notebook").classList.toggle("hidden", t.dataset.tab !== "notebook");
  $("#dataset").classList.toggle("hidden", t.dataset.tab !== "dataset");
  if (t.dataset.tab === "dataset" && !ds.loaded) loadDataset();
}));

/* ---------------- top actions ---------------- */
$("#runAll").onclick = async () => {
  if (!confirm("Run all steps in order?\n\nThe Full-size TabPFN / TabFM steps and their SHAP steps can take many hours on a laptop. The run stops at the first error.")) return;
  await api("/api/run-all", { method: "POST" });
  refresh();
};
$("#stop").onclick = async () => { await api("/api/stop", { method: "POST" }); refresh(); };
$("#restart").onclick = async () => {
  if (!confirm("Restart the Python kernel? Variables in memory are cleared (saved results are kept).")) return;
  await api("/api/restart", { method: "POST" }); refresh();
};

/* ---------------- sidebar ---------------- */
function renderSidebar() {
  const groups = {};
  steps.forEach((s) => (groups[s.group] ||= []).push(s));
  $("#sidebar").innerHTML = Object.entries(groups).map(([g, items]) => `
    <div class="group">
      <div class="group-head"><span>${esc(g)}</span>
        <button class="btn ghost" data-from="${items[0].id}" data-to="${items[items.length - 1].id}" title="Run this group in order">Run group</button>
      </div>
      ${items.map((s) => {
        const r = s.last_run, st = r ? r.status : "";
        return `<div class="step-item ${s.id === selected ? "active" : ""}" data-id="${s.id}">
          <span class="dot ${st}"></span><span class="lbl">${esc(s.label)}</span>
          <span class="ttl" title="${esc(s.title)}">${esc(s.title)}</span>
          <span class="time">${r && r.seconds != null ? fmtTime(r.seconds) : ""}</span></div>`;
      }).join("")}
    </div>`).join("");
  document.querySelectorAll(".step-item").forEach((el) => el.onclick = () => select(el.dataset.id));
  document.querySelectorAll(".group-head button").forEach((b) => b.onclick = async () => {
    await api(`/api/run-all?from_step=${b.dataset.from}&to_step=${b.dataset.to}`, { method: "POST" });
    refresh();
  });
}

function select(id) {
  selected = id; viewRun = null; lastRender = "";
  localStorageSet("step", id);
  renderSidebar(); renderStep(true);
}

/* ---------------- step view ---------------- */
function renderStep(force = false) {
  const s = steps.find((x) => x.id === selected);
  if (!s) return;
  const run = viewRun || s.last_run;
  const key = JSON.stringify([s.id, run && [run.id, run.status, run.outputs.length, run.seconds, run.files.length], viewRun && viewRun.id]);
  if (!force && key === lastRender) return;
  lastRender = key;

  const editorFocused = document.activeElement && document.activeElement.id === "editor";
  const code = drafts[s.id] ?? (viewRun ? viewRun.code : s.code);
  const busy = run && (run.status === "running" || run.status === "queued");
  const statusLabel = run ? `${run.status}${run.seconds != null ? " · " + fmtTime(run.seconds) : ""}` : "not run yet";

  const html = `
    <div class="step-head">
      <div><h1>Step ${esc(s.label)} — ${esc(s.title)}</h1>
        <div class="sub">${esc(s.group)} · <code>${esc(s.id)}</code></div></div>
      <div class="actions">
        <span class="badge ${run ? run.status : ""}">${esc(statusLabel)}</span>
        <select class="btn" id="history" title="Previous runs"><option value="">Latest run</option></select>
        <button class="btn" id="reset" title="Restore the original step code">Reset code</button>
        <button class="btn primary" id="train" ${busy ? "disabled" : ""}>${busy ? "Running…" : "▶ Train / Run"}</button>
      </div>
    </div>
    ${s.saved ? `<div class="saved-note">Last successful run saved to <code>thesis_project/${esc(s.id)}/</code></div>` : ""}
    <div class="card">
      <div class="card-head">code.py <span class="spacer"></span><span>⌘/Ctrl + Enter to run</span></div>
      <textarea id="editor" class="editor" spellcheck="false">${esc(code)}</textarea>
    </div>
    <div class="card">
      <div class="card-head">Output ${run ? `<span>· run #${run.id}${run.started_at ? " · " + new Date(run.started_at).toLocaleString() : ""}</span>` : ""}</div>
      <div class="output" id="output">${run ? renderOutputs(run) : ""}</div>
      ${run && run.files.length ? `<div class="files">${run.files.map((f) =>
        `<a class="file" href="/api/files/${f.key}?download=true">⬇ ${esc(f.name)}</a>`).join("")}</div>` : ""}
    </div>`;

  const scroll = $("#step").scrollTop;
  const sel = editorFocused ? [$("#editor").selectionStart, $("#editor").selectionEnd] : null;
  $("#step").innerHTML = html;
  $("#step").scrollTop = scroll;
  const ed = $("#editor");
  ed.style.height = Math.min(Math.max(240, ed.scrollHeight + 4), 640) + "px";
  if (sel) { ed.focus(); ed.setSelectionRange(...sel); }

  ed.oninput = () => { drafts[s.id] = ed.value; };
  ed.onkeydown = (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart: a, selectionEnd: b } = ed;
      ed.setRangeText("    ", a, b, "end"); drafts[s.id] = ed.value;
    }
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); train(); }
  };
  $("#train").onclick = train;
  $("#reset").onclick = () => { if (confirm("Replace the editor with the original step code?")) { drafts[s.id] = s.default_code; lastRender = ""; renderStep(true); } };
  loadHistory(s.id);
}

function renderOutputs(run) {
  return run.outputs.map((o) => {
    if (o.type === "stream") return `<pre class="out-stream ${o.name}">${esc(stripAnsi(o.text))}</pre>`;
    if (o.type === "error") return `<pre class="out-error">${esc(stripAnsi(o.text))}</pre>`;
    if (o.type === "image") return `<img class="out-img" src="/api/files/${o.key}" loading="lazy">`;
    if (o.type === "result") return o.html ? `<div class="out-html">${o.html}</div>` : `<pre class="out-stream">${esc(o.text)}</pre>`;
    return "";
  }).join("");
}

async function loadHistory(stepId) {
  const runs = await api(`/api/steps/${stepId}/history`).catch(() => []);
  const h = $("#history");
  if (!h || stepId !== selected) return;
  h.innerHTML = `<option value="">Latest run</option>` + runs.map((r) =>
    `<option value="${r.id}" ${viewRun && viewRun.id === r.id ? "selected" : ""}>#${r.id} · ${r.status} · ${fmtTime(r.seconds)} · ${new Date(r.created_at).toLocaleDateString()}</option>`).join("");
  h.onchange = async () => {
    viewRun = h.value ? await api(`/api/runs/${h.value}`) : null;
    delete drafts[stepId];
    renderStep(true);
  };
}

async function train() {
  const s = steps.find((x) => x.id === selected);
  const code = $("#editor").value;
  await api(`/api/steps/${s.id}/run`, { method: "POST", body: JSON.stringify({ code }) });
  delete drafts[s.id]; viewRun = null;
  refresh();
}

/* ---------------- polling ---------------- */
async function refresh() {
  try {
    const [st, list] = await Promise.all([api("/api/status"), api("/api/steps")]);
    steps = list;
    if (!selected || !steps.some((s) => s.id === selected)) selected = steps[0]?.id;
    const running = st.running ? steps.find((s) => s.last_run && s.last_run.id === st.running) : null;
    $("#status").textContent = running ? `Running ${running.label}${st.queued ? ` · ${st.queued} queued` : ""}` : st.queued ? `${st.queued} queued` : "Idle";
    $("#status").classList.toggle("busy", !!(st.running || st.queued));
    renderSidebar(); renderStep();
  } catch (e) {
    $("#status").textContent = "backend offline";
  }
}
refresh();
setInterval(refresh, 2000);

/* ---------------- dataset tab ---------------- */
const ds = { offset: 0, limit: 50, sort: null, desc: false, q: "", loaded: false, total: 0 };
const CLASS = ["Low", "Moderate", "High"];

async function loadDataset() {
  ds.loaded = true;
  const stats = await api("/api/dataset/stats");
  const t = stats.target;
  $("#dsCards").innerHTML = [
    ["Patients", stats.rows.toLocaleString(), "thesis_project/data/data.csv"],
    ["Columns", stats.columns, `${stats.missing} missing values`],
    ...[0, 1, 2].map((k) => [`${CLASS[k]} risk`, (t[k] || 0).toLocaleString(), `${((t[k] || 0) / stats.rows * 100).toFixed(1)}% of patients`]),
    ["Gender", Object.entries(stats.gender).map(([g, n]) => `${g[0]} ${n.toLocaleString()}`).join(" · "), "M / F / O"],
  ].map(([k, v, s]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join("");
  const cols = Object.keys(stats.describe[0] || {});
  $("#dsStats").className = "data";
  $("#dsStats").innerHTML = `<tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr>` +
    stats.describe.map((r) => `<tr>${cols.map((c) => `<td>${esc(r[c])}</td>`).join("")}</tr>`).join("");
  loadRows();
}

async function loadRows() {
  const p = new URLSearchParams({ offset: ds.offset, limit: ds.limit, desc: ds.desc });
  if (ds.sort) p.set("sort", ds.sort);
  if (ds.q) p.set("q", ds.q);
  const d = await api(`/api/dataset?${p}`);
  ds.total = d.total;
  const tbl = $("#dsTable");
  tbl.className = "data";
  tbl.innerHTML = `<tr>${d.columns.map((c) => `<th data-c="${c}" class="${ds.sort === c ? "sorted" : ""}">${esc(c)}${ds.sort === c ? (ds.desc ? " ↓" : " ↑") : ""}</th>`).join("")}</tr>` +
    d.rows.map((r) => `<tr>${r.map((v, i) => `<td class="${d.columns[i] === "full_name" ? "name" : ""}" title="${esc(v)}">${esc(v)}</td>`).join("")}</tr>`).join("");
  tbl.querySelectorAll("th").forEach((th) => th.onclick = () => {
    ds.desc = ds.sort === th.dataset.c ? !ds.desc : false; ds.sort = th.dataset.c; ds.offset = 0; loadRows();
  });
  $("#dsInfo").textContent = d.total ? `Rows ${ds.offset + 1}–${Math.min(ds.offset + ds.limit, d.total)} of ${d.total.toLocaleString()}` : "No rows";
  $("#dsPrev").disabled = ds.offset === 0;
  $("#dsNext").disabled = ds.offset + ds.limit >= d.total;
}
$("#dsPrev").onclick = () => { ds.offset = Math.max(0, ds.offset - ds.limit); loadRows(); };
$("#dsNext").onclick = () => { ds.offset += ds.limit; loadRows(); };
let searchTimer;
$("#dsSearch").oninput = (e) => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { ds.q = e.target.value.trim(); ds.offset = 0; loadRows(); }, 300); };
