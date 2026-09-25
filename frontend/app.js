const $ = (s) => document.querySelector(s);
const api = async (path, opts = {}) => {
  const r = await fetch(path, { headers: { "content-type": "application/json" }, ...opts });
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const stripAnsi = (s) => String(s).replace(/\x1b\[[0-9;]*m/g, "");
const fmtTime = (s) => (s == null ? "" : s < 60 ? `${s.toFixed(1)}s` : s < 3600 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.floor(s / 3600)}h ${Math.round((s % 3600) / 60)}m`);

function localStorageGet(k) { try { return localStorage.getItem(k); } catch { return null; } }
function localStorageSet(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } }

let steps = [];
let selected = localStorageGet("step");
let status = { running: null, queued: 0 };
const drafts = {};          // edited code per step, kept while you move between steps
let viewRun = null;         // a run picked from history (null = latest)
let loadedKey = "";         // which step/run the editor currently holds
let outKey = "";            // what the output pane currently shows
let histKey = "";
const summaries = new Map(); // run id -> parsed metrics.json / shap_summary.json (or null)

const curStep = () => steps.find((x) => x.id === selected);
const isBusy = (r) => !!r && (r.status === "running" || r.status === "queued");

/* ---------------- tabs ---------------- */
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  ["predict", "notebook", "compare", "dataset"].forEach((v) => $("#" + v).classList.toggle("hidden", t.dataset.tab !== v));
  if (t.dataset.tab === "dataset" && !ds.loaded) loadDataset();
  if (t.dataset.tab === "compare") renderCompare();
}));

/* ---------------- top actions ---------------- */
$("#runAll").onclick = async () => {
  if (!confirm("Run all steps in order?\n\nThe Full-size TabPFN / TabFM steps and their SHAP steps can take many hours on a laptop. The run stops at the first error.")) return;
  await api("/api/run-all", { method: "POST" });
  refresh();
};
const stopAll = async () => { await api("/api/stop", { method: "POST" }); refresh(); };
$("#stopAll").onclick = stopAll;
$("#restart").onclick = async () => {
  if (!confirm("Restart the Python kernel? Variables in memory are cleared (saved results are kept).")) return;
  await api("/api/restart", { method: "POST" }); refresh();
};

/* ---------------- sidebar ---------------- */
const CHEV = `<svg class="chev" viewBox="0 0 8 8"><path d="M1 2.5l3 3.5 3-3.5z"/></svg>`;
let shut = {};
try { shut = JSON.parse(localStorageGet("shutGroups") || "{}"); } catch { shut = {}; }
let sbCollapsed = localStorageGet("sbCollapsed") === "1";

let sbKey = "";
function renderSidebar() {
  const key = JSON.stringify([steps.map((s) => [s.id, s.last_run && s.last_run.status, s.last_run && s.last_run.seconds]), selected, sbCollapsed]);
  if (key === sbKey) return;
  sbKey = key;
  const groups = {};
  steps.forEach((s) => (groups[s.group] ||= []).push(s));
  const sb = $("#sidebar"), top = sb.scrollTop;
  sb.classList.toggle("collapsed", sbCollapsed);
  sb.innerHTML = `
    <div class="sb-top"><span>${steps.filter((s) => s.last_run && s.last_run.status === "ok").length} / ${steps.length} done</span>
      <button class="btn icon ghost-danger" id="sbToggle" title="${sbCollapsed ? "Expand" : "Collapse"} sidebar">${sbCollapsed ? "»" : "«"}</button></div>` +
    Object.entries(groups).map(([g, items]) => `
    <div class="group ${shut[g] ? "shut" : ""}" data-g="${esc(g)}">
      <div class="group-head" data-g="${esc(g)}">${CHEV}<span class="gname">${esc(g)}</span>
        <span class="gcount">${items.filter((s) => s.last_run && s.last_run.status === "ok").length}/${items.length}</span>
        <button class="gbtn" data-from="${items[0].id}" data-to="${items[items.length - 1].id}" title="Run this group in order"><svg class="ic" viewBox="0 0 16 16"><path d="M4 2.5l9 5.5-9 5.5z"/></svg></button>
      </div>
      ${items.map((s) => {
        const r = s.last_run, st = r ? r.status : "";
        return `<div class="step-item ${s.id === selected ? "active" : ""}" data-id="${s.id}" title="${esc(s.label + " — " + s.title)}">
          <span class="dot ${st}"></span><span class="lbl">${esc(s.label)}</span>
          <span class="ttl">${esc(s.title)}</span>
          <span class="time">${r && r.seconds != null ? fmtTime(r.seconds) : ""}</span></div>`;
      }).join("")}
    </div>`).join("");
  sb.scrollTop = top;
  $("#sbToggle").onclick = () => { sbCollapsed = !sbCollapsed; localStorageSet("sbCollapsed", sbCollapsed ? "1" : "0"); renderSidebar(); };
  sb.querySelectorAll(".step-item").forEach((el) => el.onclick = () => select(el.dataset.id));
  sb.querySelectorAll(".group-head").forEach((h) => h.onclick = (e) => {
    if (e.target.closest(".gbtn")) return;
    shut[h.dataset.g] = !shut[h.dataset.g];
    localStorageSet("shutGroups", JSON.stringify(shut));
    h.parentElement.classList.toggle("shut", shut[h.dataset.g]);
  });
  sb.querySelectorAll(".gbtn").forEach((b) => b.onclick = async () => {
    if (!confirm("Run this whole group in order?")) return;
    await api(`/api/run-all?from_step=${b.dataset.from}&to_step=${b.dataset.to}`, { method: "POST" });
    refresh();
  });
}

function select(id) {
  stashDraft();
  selected = id; viewRun = null; loadedKey = ""; outKey = ""; histKey = "";
  localStorageSet("step", id);
  renderSidebar(); renderStep();
}

function stepBy(delta) {
  const i = steps.findIndex((s) => s.id === selected);
  const n = steps[i + delta];
  if (n) { select(n.id); $("#sidebar .step-item.active")?.scrollIntoView({ block: "nearest" }); }
}

/* ---------------- editor ---------------- */
const ed = $("#editor"), gutter = $("#gutter");
function updateGutter() {
  const n = ed.value.split("\n").length;
  gutter.textContent = Array.from({ length: n }, (_, i) => i + 1).join("\n");
  gutter.scrollTop = ed.scrollTop;
}
function stashDraft() { if (selected && loadedKey) drafts[selected] = ed.value; }
let baseCode = "";   // what the editor held when the step / run was loaded
function updateModified() {
  const s = curStep();
  $("#modTag").classList.toggle("hidden", ed.value === baseCode);
  $("#reset").disabled = !s || ed.value === s.default_code;
}
ed.addEventListener("scroll", () => { gutter.scrollTop = ed.scrollTop; });
ed.addEventListener("input", () => { drafts[selected] = ed.value; updateGutter(); updateModified(); });
ed.addEventListener("keydown", (e) => {
  if (e.key === "Tab") {
    e.preventDefault();
    ed.setRangeText("    ", ed.selectionStart, ed.selectionEnd, "end");
    drafts[selected] = ed.value; updateGutter(); updateModified();
  }
});
$("#reset").onclick = () => {
  const s = curStep();
  if (s && confirm("Replace the editor with the original step code?")) {
    ed.value = s.default_code; drafts[s.id] = ed.value; updateGutter(); updateModified();
  }
};
$("#toggleCode").onclick = () => {
  const hidden = $("#split").classList.toggle("code-hidden");
  $("#toggleCode").classList.toggle("on", hidden);
  localStorageSet("codeHidden", hidden ? "1" : "0");
};
if (localStorageGet("codeHidden") === "1") { $("#split").classList.add("code-hidden"); $("#toggleCode").classList.add("on"); }

/* ---------------- draggable divider ---------------- */
const split = $("#split"), divider = $("#divider");
const setCodeW = (pct) => split.style.setProperty("--code-w", pct + "%");
setCodeW(parseFloat(localStorageGet("codeW")) || 45);
divider.addEventListener("pointerdown", (e) => {
  divider.setPointerCapture(e.pointerId); divider.classList.add("drag");
  document.body.style.userSelect = "none";
});
divider.addEventListener("pointermove", (e) => {
  if (!divider.classList.contains("drag")) return;
  const r = split.getBoundingClientRect();
  const pct = Math.min(75, Math.max(20, ((e.clientX - r.left) / r.width) * 100));
  setCodeW(pct); divider.dataset.pct = pct;
});
divider.addEventListener("pointerup", () => {
  divider.classList.remove("drag"); document.body.style.userSelect = "";
  if (divider.dataset.pct) localStorageSet("codeW", divider.dataset.pct);
});
divider.addEventListener("dblclick", () => { setCodeW(45); localStorageSet("codeW", "45"); });

/* ---------------- run / stop button ---------------- */
async function train() {
  const s = curStep();
  if (!s) return;
  drafts[s.id] = ed.value;
  await api(`/api/steps/${s.id}/run`, { method: "POST", body: JSON.stringify({ code: ed.value }) });
  viewRun = null; outKey = ""; histKey = "";
  $("#history").value = "";
  refresh();
}
$("#runBtn").onclick = () => { const s = curStep(); if (s && isBusy(s.last_run)) stopAll(); else train(); };

function paintRunBtn(busy) {
  const b = $("#runBtn");
  b.classList.toggle("primary", !busy); b.classList.toggle("danger", busy);
  b.title = busy ? "Stop the running step" : "Run this step (⌘/Ctrl + Enter)";
  b.innerHTML = busy
    ? `<span class="spin"></span>Stop`
    : `<svg class="ic" viewBox="0 0 16 16"><path d="M4 2.5l9 5.5-9 5.5z"/></svg>Run`;
}

/* ---------------- step view ---------------- */
function renderStep() {
  const s = curStep();
  if (!s) return;
  const run = viewRun || s.last_run;

  // editor: loaded once per step / picked run, never overwritten by polling
  const key = s.id + "|" + (viewRun ? viewRun.id : "");
  if (loadedKey !== key) {
    loadedKey = key;
    baseCode = viewRun ? viewRun.code : s.code;
    ed.value = viewRun ? viewRun.code : (drafts[s.id] ?? s.code);
    ed.scrollTop = 0; updateGutter();
  }
  updateModified();

  $("#wsTitle").textContent = `Step ${s.label} — ${s.title}`;
  $("#wsSub").textContent = `${s.group} · ${s.id}`;
  const badge = $("#badge");
  badge.className = "badge " + (run ? run.status : "");
  badge.textContent = run ? `${run.status}${run.seconds != null ? " · " + fmtTime(run.seconds) : ""}` : "not run yet";
  paintRunBtn(isBusy(s.last_run));
  $("#outTitle").textContent = run ? `Output · run #${run.id}${run.started_at ? " · " + new Date(run.started_at).toLocaleString() : ""}` : "Output";
  $("#savedNote").innerHTML = s.saved ? `saved → <code>thesis_project/${esc(s.id)}/</code>` : "";

  paintOutput(run);
  const hk = s.id + "|" + (s.last_run ? s.last_run.id + s.last_run.status : "") + "|" + (viewRun ? viewRun.id : "");
  if (hk !== histKey) { histKey = hk; loadHistory(s.id); }
}

function outSize(run) {
  return run.outputs.reduce((n, o) => n + (o.text ? o.text.length : 0), 0);
}

function paintOutput(run) {
  const out = $("#output"), files = $("#files"), jump = $("#jump");
  if (!run) { out.innerHTML = ""; files.classList.add("hidden"); $("#chips").classList.add("hidden"); outKey = ""; return; }
  const k = JSON.stringify([run.id, run.status, run.outputs.length, outSize(run), run.files.length]);
  if (k === outKey) return;
  const first = !outKey.startsWith(`[${run.id},`);
  outKey = k;

  const pinned = first || out.scrollHeight - out.scrollTop - out.clientHeight < 40;
  const prevTop = out.scrollTop;
  out.innerHTML = renderOutputs(run);
  // follow the log while it is running (or when you were already at the bottom); otherwise keep your place
  if (isBusy(run) && pinned) out.scrollTop = out.scrollHeight;
  else if (first) out.scrollTop = run.status === "ok" ? 0 : out.scrollHeight;
  else out.scrollTop = prevTop;
  jump.classList.toggle("hidden", !(isBusy(run) && out.scrollHeight - out.scrollTop - out.clientHeight > 40));

  files.classList.toggle("hidden", !run.files.length);
  files.innerHTML = run.files.map((f) => `<a class="file" href="/api/files/${f.key}?download=true">⬇ ${esc(f.name)}</a>`).join("");
  paintChips(run);
}
$("#output").addEventListener("scroll", () => {
  const o = $("#output"), s = curStep();
  const run = viewRun || (s && s.last_run);
  $("#jump").classList.toggle("hidden", !(run && isBusy(run) && o.scrollHeight - o.scrollTop - o.clientHeight > 40));
});
$("#jump").onclick = () => { const o = $("#output"); o.scrollTop = o.scrollHeight; $("#jump").classList.add("hidden"); };

function renderOutputs(run) {
  return run.outputs.map((o) => {
    if (o.type === "stream") return `<pre class="out-stream ${o.name}">${esc(stripAnsi(o.text))}</pre>`;
    if (o.type === "error") return `<pre class="out-error">${esc(stripAnsi(o.text))}</pre>`;
    if (o.type === "image") return `<img class="out-img" src="/api/files/${o.key}" loading="lazy">`;
    if (o.type === "result") return o.html ? `<div class="out-html">${o.html}</div>` : `<pre class="out-stream">${esc(o.text)}</pre>`;
    return "";
  }).join("");
}

/* ---------------- metric chips ---------------- */
async function runSummary(run) {
  if (summaries.has(run.id)) return summaries.get(run.id);
  const f = (run.files || []).find((x) => x.name === "metrics.json" || x.name === "shap_summary.json");
  if (!f) { if (run.status === "ok") summaries.set(run.id, null); return null; }
  try {
    const d = await (await fetch(`/api/files/${f.key}`)).json();
    d._kind = f.name === "metrics.json" ? "metrics" : "shap";
    summaries.set(run.id, d);
    return d;
  } catch { return null; }
}
const chip = (k, v, cls = "") => `<span class="chip ${cls}"><span class="k">${k}</span><span class="v">${esc(v)}</span></span>`;

async function paintChips(run) {
  const box = $("#chips");
  const d = run.status === "ok" ? await runSummary(run) : null;
  const cur = viewRun || (curStep() && curStep().last_run);
  if (!cur || cur.id !== run.id) return;
  if (!d) { box.classList.add("hidden"); return; }
  box.classList.remove("hidden");
  if (d._kind === "metrics") {
    box.innerHTML = [
      chip("accuracy", d.accuracy), chip("macro F1", d.macro_f1), chip("weighted F1", d.weighted_f1), chip("ROC-AUC", d.roc_auc_ovr),
      chip("context", (d.context_rows ?? "").toLocaleString()), chip("test", (d.test_rows ?? "").toLocaleString()),
      chip("fit", fmtTime(d.fit_seconds)),
      d.predict_seconds === 0 && d.fit_seconds != null && /TabPFN|TabFM/.test(d.model || "")
        ? chip("predict", "0s · checkpoint reused?", "warn") : chip("predict", fmtTime(d.predict_seconds)),
    ].join("");
  } else {
    box.innerHTML = [chip("rows explained", d.rows_explained), chip("time", fmtTime(d.seconds)),
      ...(d.top_5 || []).map((f, i) => chip(`#${i + 1}`, f, "feat"))].join("");
  }
}

/* ---------------- history ---------------- */
async function loadHistory(stepId) {
  const runs = await api(`/api/steps/${stepId}/history`).catch(() => []);
  const h = $("#history");
  if (stepId !== selected) return;
  h.innerHTML = `<option value="">Latest run</option>` + runs.map((r) =>
    `<option value="${r.id}" ${viewRun && viewRun.id === r.id ? "selected" : ""}>#${r.id} · ${r.status} · ${fmtTime(r.seconds)} · ${new Date(r.created_at).toLocaleDateString()}</option>`).join("");
  h.onchange = async () => {
    stashDraft();
    viewRun = h.value ? await api(`/api/runs/${h.value}`) : null;
    loadedKey = ""; outKey = "";
    renderStep();
  };
}

/* ---------------- compare tab ---------------- */
const SIZE_ORDER = { "500": 0, "2000": 1, "Full": 2 };
const bySizeOrder = (a, b) => a.d.model.localeCompare(b.d.model) || (SIZE_ORDER[a.d.size] ?? 9) - (SIZE_ORDER[b.d.size] ?? 9);
let cmpRows = [], cmpSig = "";

function parseCSV(text) {
  const rows = []; let row = [], f = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const [head, ...body] = rows.filter((r) => r.length > 1 || r[0] !== "");
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}
async function stepFile(stepPrefix, name) {
  const s = steps.find((x) => x.id.startsWith(stepPrefix));
  const f = s && s.last_run && s.last_run.status === "ok" && (s.last_run.files || []).find((x) => x.name === name);
  return f ? { key: f.key, text: await (await fetch(`/api/files/${f.key}`)).text() } : null;
}
const fmtP = (p) => (p < 0.001 ? "<0.001" : p.toFixed(3));
const num = (v) => (v === "" || v == null ? NaN : Number(v));
const isFast = (d) => d.predict_seconds === 0 && /TabPFN|TabFM/.test(d.model);

async function renderCompare() {
  const page = $("#cmpPage");
  if (!cmpRows.length) page.innerHTML = `<div class="muted">Loading…</div>`;
  const okSteps = steps.filter((s) => s.last_run && s.last_run.status === "ok");
  const [got, dsStats, mc, fin] = await Promise.all([
    Promise.all(okSteps.map(async (s) => ({ s, d: await runSummary(s.last_run) }))),
    api("/api/dataset/stats").catch(() => null),
    stepFile("Step_09", "mcnemar_results.csv").catch(() => null),
    (async () => {
      const s = steps.find((x) => x.id.startsWith("Step_10"));
      return s && s.last_run && s.last_run.status === "ok" ? s.last_run.files.filter((f) => f.name.endsWith(".png")) : [];
    })(),
  ]);
  const met = got.filter((x) => x.d && x.d._kind === "metrics").sort(bySizeOrder);
  const shap = got.filter((x) => x.d && x.d._kind === "shap").sort(bySizeOrder);
  cmpRows = met;
  const models = [...new Set(met.map((x) => x.d.model))];
  const sizes = ["500", "2000", "Full"];
  const cell = (m, sz) => met.find((x) => x.d.model === m && x.d.size === sz)?.d;

  // dataset strip
  const t = dsStats ? dsStats.target : {};
  const testRows = met[0]?.d.test_rows, trainFull = Math.max(0, ...met.map((x) => x.d.context_rows || 0));
  const strip = dsStats ? `<div class="cards">
    ${[["Patients", dsStats.rows.toLocaleString()], ["Columns", dsStats.columns], ["Missing", dsStats.missing],
       ["Low", (t[0] || 0).toLocaleString(), (((t[0] || 0) / dsStats.rows) * 100).toFixed(0) + "%"],
       ["Moderate", (t[1] || 0).toLocaleString(), (((t[1] || 0) / dsStats.rows) * 100).toFixed(0) + "%"],
       ["High", (t[2] || 0).toLocaleString(), (((t[2] || 0) / dsStats.rows) * 100).toFixed(0) + "%"],
       ["Train", trainFull.toLocaleString()], ["Test", (testRows || 0).toLocaleString()]]
      .map(([k, v, sub]) => `<div class="stat"><span class="k">${k}</span><span class="v">${v}</span>${sub ? `<span class="s">${sub}</span>` : ""}</div>`).join("")}</div>` : "";

  // main metrics table
  const cols = [["accuracy", "Accuracy"], ["macro_f1", "Macro F1"], ["weighted_f1", "Wtd F1"], ["roc_auc_ovr", "ROC-AUC"]];
  const best = {}, lo = {};
  cols.forEach(([k]) => { best[k] = Math.max(...met.map((x) => x.d[k] ?? -1)); lo[k] = Math.min(...met.map((x) => x.d[k] ?? 9)); });
  let prev = null;
  const mainRows = met.map(({ s, d }) => {
    const sep = prev && prev !== d.model ? "sep" : ""; prev = d.model;
    return `<tr class="${sep}"><td class="l"><code>${esc(s.label)}</code></td><td class="l">${esc(d.model)}</td><td class="l">${esc(d.size)}</td>
      <td>${(d.context_rows ?? 0).toLocaleString()}</td>
      ${cols.map(([k]) => `<td class="${d[k] === best[k] ? "best" : ""}">${d[k]}<span class="bar" style="width:${Math.round(((d[k] - lo[k] * 0.98) / (best[k] - lo[k] * 0.98 || 1)) * 30)}px"></span></td>`).join("")}
      <td>${fmtTime(d.fit_seconds)}</td><td class="${isFast(d) ? "warn" : ""}" title="${isFast(d) ? "0s: predictions came from a saved checkpoint" : ""}">${fmtTime(d.predict_seconds)}</td></tr>`;
  }).join("");

  // pivots (model x size)
  const pivot = (title, fn, higherBetter) => {
    const vals = met.map((x) => fn(x.d)).filter((v) => v != null);
    const top = higherBetter ? Math.max(...vals) : null;
    return `<div class="sec"><div class="sec-head"><h2>${title}</h2></div><div class="table-wrap"><table class="data cmp">
      <tr><th class="l">Model</th>${sizes.map((z) => `<th>${z}</th>`).join("")}<th>Δ 500→Full</th></tr>
      ${models.map((m) => {
        const v = sizes.map((z) => { const d = cell(m, z); return d ? fn(d) : null; });
        const delta = v[0] != null && v[2] != null ? v[2] - v[0] : null;
        return `<tr><td class="l">${esc(m)}</td>${v.map((x) => `<td class="${higherBetter && x === top ? "best" : ""}">${x == null ? "–" : (higherBetter ? x.toFixed(4) : fmtTime(x))}</td>`).join("")}
          <td>${delta == null ? "–" : (delta >= 0 ? "+" : "") + (higherBetter ? delta.toFixed(4) : fmtTime(Math.abs(delta)))}</td></tr>`;
      }).join("")}</table></div></div>`;
  };

  // McNemar
  let mcHtml = `<div class="muted">Run Step 9 to see McNemar tests.</div>`;
  if (mc) {
    const rows = parseCSV(mc.text);
    mcHtml = `<div class="table-wrap"><table class="data cmp">
      <tr><th class="l">Size</th><th class="l">Comparison</th><th>Only A right</th><th>Only B right</th><th>χ²</th><th>p</th><th>Result (α = 0.05)</th></tr>
      ${rows.map((r) => {
        const [A, B] = r.comparison.split(" vs ");
        const a = num(r[`only_${A}_correct`]), b = num(r.only_other_correct), p = num(r.p_value), sig = String(r["significant_0.05"]).toLowerCase() === "true";
        const win = sig ? (a > b ? A : B) : null;
        return `<tr><td class="l">${esc(r.size)}</td><td class="l">${esc(A)} vs ${esc(B)}</td><td>${a}</td><td>${b}</td><td>${num(r.chi2).toFixed(2)}</td><td>${fmtP(p)}</td>
          <td class="${sig ? "sig" : "ns"}">${sig ? `${esc(win)} better` : "no difference"}</td></tr>`;
      }).join("")}</table></div>`;
  }

  // SHAP
  const shapHtml = shap.length ? `<div class="table-wrap"><table class="data cmp">
    <tr><th class="l">Model</th><th class="l">Size</th><th>Rows</th><th>Time</th><th class="l">Top 5 features</th></tr>
    ${shap.map(({ d }) => `<tr><td class="l">${esc(d.model)}</td><td class="l">${esc(d.size)}</td><td>${d.rows_explained}</td><td>${fmtTime(d.seconds)}</td>
      <td class="ft">${(d.top_5 || []).map((f) => `<span class="fchip">${esc(f)}</span>`).join("")}</td></tr>`).join("")}</table></div>`
    : `<div class="muted">No SHAP runs yet.</div>`;

  page.innerHTML = `${strip}
    <div class="sec"><div class="sec-head"><h2>Model comparison</h2><span class="note">${met.length} runs · best per column highlighted · orange predict time = checkpoint reused</span><span class="spacer"></span>
      <button class="btn" id="cmpCopy">Copy CSV</button></div>
      <div class="table-wrap"><table class="data cmp">
      <tr><th class="l">Step</th><th class="l">Model</th><th class="l">Size</th><th>Context</th>${cols.map((c) => `<th>${c[1]}</th>`).join("")}<th>Fit</th><th>Predict</th></tr>
      ${mainRows || `<tr><td class="l" colspan="10">No finished runs with metrics yet.</td></tr>`}</table></div></div>
    <div class="grid2">
      ${pivot("Macro F1 vs context size", (d) => d.macro_f1, true)}
      ${pivot("ROC-AUC vs context size", (d) => d.roc_auc_ovr, true)}
      ${pivot("Predict time vs context size", (d) => (isFast(d) ? null : d.predict_seconds), false)}
    </div>
    <div class="grid2">
      <div class="sec"><div class="sec-head"><h2>McNemar's tests</h2><span class="note">paired, same 4,322 test rows</span></div>${mcHtml}</div>
      <div class="sec"><div class="sec-head"><h2>SHAP — top features</h2></div>${shapHtml}</div>
    </div>
    ${fin.length ? `<div class="sec"><div class="sec-head"><h2>Final figures</h2><span class="note">click to enlarge</span></div>
      <div class="imgrow">${fin.map((f) => `<img src="/api/files/${f.key}" title="${esc(f.name)}">`).join("")}</div></div>` : ""}`;
  $("#cmpCopy").onclick = () => {
    const head = ["step", "model", "size", "context_rows", "accuracy", "macro_f1", "weighted_f1", "roc_auc_ovr", "fit_seconds", "predict_seconds"];
    const csv = [head.join(","), ...cmpRows.map(({ s, d }) => [s.id, d.model, d.size, d.context_rows, d.accuracy, d.macro_f1, d.weighted_f1, d.roc_auc_ovr, d.fit_seconds, d.predict_seconds].join(","))].join("\n");
    navigator.clipboard.writeText(csv).then(() => { $("#cmpCopy").textContent = "Copied ✓"; setTimeout(() => ($("#cmpCopy").textContent = "Copy CSV"), 1500); });
  };
}

/* click any output / compare image to open it full size */
document.addEventListener("click", (e) => { if (e.target.matches(".out-img, .imgrow img")) window.open(e.target.src, "_blank"); });

/* ---------------- font size (A- / A+) ---------------- */
let fs = parseFloat(localStorageGet("fs")) || 9;
function applyFs() {
  document.documentElement.style.setProperty("--fs", fs + "px");
  document.documentElement.style.setProperty("--fm", Math.max(6.5, fs - 0.5) + "px");
  localStorageSet("fs", String(fs));
}
applyFs();
$("#fsDown").onclick = () => { fs = Math.max(7, fs - 0.5); applyFs(); };
$("#fsUp").onclick = () => { fs = Math.min(14, fs + 0.5); applyFs(); };

/* ---------------- keyboard ---------------- */
document.addEventListener("keydown", (e) => {
  if ($("#notebook").classList.contains("hidden")) return;
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); const s = curStep(); if (s && !isBusy(s.last_run)) train(); }
  else if (e.altKey && e.key === "ArrowDown") { e.preventDefault(); stepBy(1); }
  else if (e.altKey && e.key === "ArrowUp") { e.preventDefault(); stepBy(-1); }
});

/* ---------------- polling ---------------- */
async function refresh() {
  try {
    const [st, list] = await Promise.all([api("/api/status"), api("/api/steps")]);
    steps = list; status = st;
    if (!selected || !steps.some((s) => s.id === selected)) selected = steps[0]?.id;
    const running = st.running ? steps.find((s) => s.last_run && s.last_run.id === st.running) : null;
    $("#status").textContent = running ? `Running ${running.label}${st.queued ? ` · ${st.queued} queued` : ""}` : st.queued ? `${st.queued} queued` : "Idle";
    $("#status").classList.toggle("busy", !!(st.running || st.queued));
    $("#stopAll").classList.toggle("hidden", !(st.running || st.queued));
    renderSidebar(); renderStep();
    if (!$("#compare").classList.contains("hidden")) {   // keep the compare tab current without re-rendering every poll
      const sig = JSON.stringify(steps.map((x) => x.last_run && [x.last_run.id, x.last_run.status]));
      if (sig !== cmpSig) { cmpSig = sig; renderCompare(); }
    }
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

/* remember the open tab across reloads: /#compare, /#dataset */
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  if (location.hash.slice(1).split("/")[0] !== t.dataset.tab) history.replaceState(null, "", "#" + t.dataset.tab);
}));
{ const h = location.hash.slice(1).split("/")[0]; if (h) document.querySelector(`.tab[data-tab="${h}"]`)?.click(); }
