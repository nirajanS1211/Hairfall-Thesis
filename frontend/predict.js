/* Predict tab: one patient at a time -> CatBoost / TabPFN / TabFM, saved as history (Postgres + MinIO). */
const P = {
  schema: null, fields: [], byName: {},
  models: { catboost: "Full", tabpfn: "2000", tabfm: "2000" },   // chosen model -> context size
  modelsOn: { catboost: true, tabpfn: true, tabfm: true },
  history: [], current: null, viewing: null, trueClass: null, q: "",
};
const CLS = ["Low", "Moderate", "High"];
const MODEL_NAMES = { catboost: "CatBoost", tabpfn: "TabPFN", tabfm: "TabFM" };
const pct = (x) => (x * 100).toFixed(1) + "%";
const clsBadge = (c) => (c == null ? "" : `<span class="cls c${c}">${CLS[c]}</span>`);
const fmtVal = (f, v) => (v == null || v === "" ? "–" : f.kind === "choice" ? (f.options.find((o) => o.value == v) || {}).label
  : f.kind === "bool" ? (Number(v) ? "Yes" : "No") : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }));
const decimals = (step) => (step >= 1 ? 0 : Math.round(-Math.log10(step)));

/* ---------- form ---------- */
function buildForm() {
  const groups = {};
  P.fields.forEach((f) => (groups[f.group] ||= []).push(f));
  $("#pfFields").innerHTML = Object.entries(groups).map(([g, fs]) => {
    const bools = fs.every((f) => f.kind === "bool");
    return `<div class="pf-sec"><div class="pf-sec-h">${esc(g)}${g === "Blood tests" ? `<span class="n muted" style="text-transform:none;letter-spacing:0;font-weight:400">green band = clinical normal range</span>` : ""}</div>
      <div class="pf-grid ${bools ? "bools" : ""}">${fs.map(fieldHtml).join("")}</div></div>`;
  }).join("");
  P.fields.forEach(wireField);
  $("#pfModels").innerHTML = Object.entries(P.schema.models).map(([k, sizes]) => `
    <div class="mdl ${P.modelsOn[k] ? "on" : ""}" data-m="${k}">
      <label><input type="checkbox" ${P.modelsOn[k] ? "checked" : ""}>${MODEL_NAMES[k]}</label>
      ${sizes.length > 1 ? `<select title="Context rows given to the model">${sizes.map((s) => `<option ${s === P.models[k] ? "selected" : ""}>${s}</option>`).join("")}</select>`
        : `<span class="muted">${k === "catboost" ? "trained · Full" : sizes[0]}</span>`}
    </div>`).join("");
  document.querySelectorAll(".mdl").forEach((el) => {
    const k = el.dataset.m;
    el.querySelector("input").onchange = (e) => { P.modelsOn[k] = e.target.checked; el.classList.toggle("on", e.target.checked); saveModelPrefs(); validateAll(); };
    const sel = el.querySelector("select");
    if (sel) sel.onchange = () => { P.models[k] = sel.value; saveModelPrefs(); warmHint(); };
  });
  warmHint();
}

function fieldHtml(f) {
  if (f.kind === "bool") return `<div class="fld b" data-f="${f.name}"><span class="lb"><b title="${esc(f.label)}">${esc(f.label)}</b></span>
    <div class="seg yes"><button type="button" data-v="0">No</button><button type="button" data-v="1">Yes</button></div></div>`;
  if (f.kind === "choice") return `<div class="fld" data-f="${f.name}"><span class="lb"><b>${esc(f.label)}</b></span>
    <div class="seg">${f.options.map((o) => `<button type="button" data-v="${o.value}">${esc(o.label)}</button>`).join("")}</div><span class="hint">&nbsp;</span></div>`;
  const span = f.max - f.min, nz = f.normal ? `<span class="nz" style="left:${((f.normal[0] - f.min) / span) * 100}%;width:${((Math.min(f.normal[1], f.max) - f.normal[0]) / span) * 100}%"></span>` : "";
  return `<div class="fld" data-f="${f.name}" title="${esc(f.help || f.label)}${f.normal ? ` · normal ${f.normal[0]}–${f.normal[1]} ${f.unit}` : ""}">
    <span class="lb"><b>${esc(f.label)}</b><span class="u">${esc(f.unit)}</span><span class="fl"></span></span>
    <input class="in" type="number" inputmode="decimal" min="${f.min}" max="${f.max}" step="${f.step}" placeholder="e.g. ${f.default}">
    <div class="rg">${nz}<span class="mk hidden"></span></div>
    <span class="hint"><span>${f.min}</span><span class="err"></span><span>${f.max}</span></span></div>`;
}

function fieldEl(name) { return document.querySelector(`.fld[data-f="${name}"]`); }

function wireField(f) {
  const el = fieldEl(f.name);
  if (f.kind === "bool" || f.kind === "choice") {
    el.querySelectorAll(".seg button").forEach((b) => b.onclick = () => { setValue(f.name, Number(b.dataset.v)); markDirty(); });
    return;
  }
  const inp = el.querySelector("input");
  // block characters that can never be valid (e, +, and minus when the range is non-negative)
  inp.addEventListener("keydown", (e) => {
    if (["e", "E", "+"].includes(e.key) || (e.key === "-" && f.min >= 0) || (e.key === "." && f.kind === "int")) e.preventDefault();
    if (e.key === "Enter") { e.preventDefault(); const all = [...document.querySelectorAll("#pfFields input.in")]; all[all.indexOf(inp) + 1]?.focus(); }
  });
  inp.addEventListener("input", () => { paintField(f); markDirty(); validateAll(); });
  // leaving the box: out-of-range values are pulled back to the nearest limit, and rounded to the field's precision
  inp.addEventListener("change", () => {
    if (inp.value === "") { paintField(f); validateAll(); return; }
    let v = Number(inp.value);
    const c = Math.min(f.max, Math.max(f.min, v));
    const r = Number(c.toFixed(decimals(f.step)));
    if (r !== v) { inp.value = r; inp.classList.remove("flash"); void inp.offsetWidth; inp.classList.add("flash");
      flashNote(`${f.label}: ${v} is outside ${f.min}–${f.max} ${f.unit} → set to ${r}`); }
    paintField(f); validateAll();
  });
}

function getValue(name) {
  const f = P.byName[name], el = fieldEl(name);
  if (f.kind === "bool" || f.kind === "choice") { const on = el.querySelector(".seg button.on"); return on ? Number(on.dataset.v) : null; }
  const v = el.querySelector("input").value;
  return v === "" ? null : Number(v);
}
function setValue(name, v) {
  const f = P.byName[name], el = fieldEl(name);
  if (f.kind === "bool" || f.kind === "choice") el.querySelectorAll(".seg button").forEach((b) => b.classList.toggle("on", v != null && Number(b.dataset.v) === Number(v)));
  else el.querySelector("input").value = v == null ? "" : v;
  paintField(f); validateAll();
}

function fieldError(f, v) {
  if (v == null || Number.isNaN(v)) return "required";
  if (v < f.min || v > f.max) return `${f.min}–${f.max}`;
  if ((f.kind === "int" || f.kind === "choice" || f.kind === "bool") && !Number.isInteger(v)) return "whole number";
  return "";
}

function paintField(f) {
  const el = fieldEl(f.name), v = getValue(f.name);
  if (f.kind === "bool" || f.kind === "choice") { el.querySelector(".seg").classList.toggle("need", P.showErrors && v == null); return; }
  const inp = el.querySelector("input"), err = fieldError(f, v);
  const shown = err && (v != null || P.showErrors);
  inp.classList.toggle("bad", !!shown);
  el.querySelector(".err").textContent = shown ? err : "";
  const mk = el.querySelector(".mk"), fl = el.querySelector(".fl");
  if (v == null || err) { mk.classList.add("hidden"); fl.textContent = ""; fl.className = "fl"; return; }
  mk.classList.remove("hidden");
  mk.style.left = ((v - f.min) / (f.max - f.min)) * 100 + "%";
  const st = f.normal ? (v < f.normal[0] ? "low" : v > f.normal[1] ? "high" : "ok") : "";
  fl.className = "fl " + st;
  fl.textContent = st === "low" ? "LOW" : st === "high" ? "HIGH" : st === "ok" ? "normal" : "";
}

function validateAll() {
  const missing = P.fields.filter((f) => fieldError(f, getValue(f.name)));
  const noModel = !Object.values(P.modelsOn).some(Boolean);
  const st = $("#pfStatus"), btn = $("#pfPredict");
  const busy = P.current && ["queued", "running"].includes(P.current.status);
  btn.disabled = !!busy;
  if (missing.length) { st.textContent = `${missing.length} field${missing.length > 1 ? "s" : ""} left: ${missing.slice(0, 3).map((f) => f.label).join(", ")}${missing.length > 3 ? "…" : ""}`; st.className = "pf-status"; }
  else if (noModel) { st.textContent = "Pick at least one model"; st.className = "pf-status bad"; }
  else { st.textContent = "✓ All fields valid"; st.className = "pf-status"; }
  return !missing.length && !noModel;
}

let noteTimer;
function flashNote(t, sticky = false) {
  const n = $("#pfNote"); n.textContent = t; n.classList.remove("hidden");
  clearTimeout(noteTimer); if (!sticky) noteTimer = setTimeout(() => n.classList.add("hidden"), 3500);
}

function markDirty() {   // editing a loaded history record turns it into a new patient
  if (P.viewing) { P.viewing = null; P.trueClass = null; $("#pfTitle").textContent = "New patient (edited from history)"; paintHistory(); }
}

function fill(inputs) { P.fields.forEach((f) => setValue(f.name, inputs[f.name] ?? null)); }

function clearForm() {
  P.viewing = null; P.trueClass = null; P.showErrors = false;
  $("#pfLabel").value = ""; fill({});
  P.fields.filter((f) => f.kind === "bool").forEach((f) => setValue(f.name, 0));   // yes/no questions start at "No"
  $("#pfTitle").textContent = "New patient"; $("#pfNote").classList.add("hidden");
  P.current = null; paintResult(); paintHistory();
  document.querySelector("#pfFields input.in")?.focus();
}

function saveModelPrefs() { localStorageSet("predModels", JSON.stringify({ m: P.models, on: P.modelsOn })); }
function loadModelPrefs() {
  try { const s = JSON.parse(localStorageGet("predModels") || "null"); if (s) { Object.assign(P.models, s.m); Object.assign(P.modelsOn, s.on); } } catch { /* ignore */ }
}
function warmHint() {
  const loaded = new Set(P.schema.loaded || []);
  const cold = Object.keys(P.models).filter((k) => P.modelsOn[k] && k !== "catboost" && !loaded.has(`${k}·${P.models[k]}`));
  $("#pfWarm").textContent = (cold.length ? `First use of ${cold.map((k) => `${MODEL_NAMES[k]} ${P.models[k]}`).join(", ")} loads the model (~20 s). After that: CatBoost instant, TabPFN/TabFM a few seconds. ` : "Models are loaded — predictions take a few seconds. ")
    + (P.models.tabpfn === "Full" && P.modelsOn.tabpfn ? "TabPFN Full ≈ 40 s per patient on this Mac." : "");
}

/* ---------- predict ---------- */
async function doPredict() {
  P.showErrors = true;
  P.fields.forEach(paintField);
  if (!validateAll()) {
    const first = P.fields.find((f) => fieldError(f, getValue(f.name)));
    fieldEl(first.name)?.scrollIntoView({ block: "center", behavior: "smooth" });
    fieldEl(first.name)?.querySelector("input")?.focus();
    return;
  }
  const inputs = Object.fromEntries(P.fields.map((f) => [f.name, getValue(f.name)]));
  const models = Object.fromEntries(Object.keys(P.models).filter((k) => P.modelsOn[k]).map((k) => [k, P.models[k]]));
  try {
    const r = await fetch("/api/predict", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ label: $("#pfLabel").value, inputs, models, true_class: P.trueClass }) });
    const d = await r.json();
    if (!r.ok) {
      const errs = d.detail && d.detail.fields;
      flashNote(errs ? "Server rejected: " + Object.entries(errs).map(([k, v]) => `${P.byName[k]?.label || k} ${v}`).join("; ") : String(d.detail || r.statusText), true);
      return;
    }
    P.viewing = d.id;
    await loadPrediction(d.id);
    loadHistory();
  } catch (e) { flashNote("Backend offline: " + e.message, true); }
}

let pollTimer;
async function loadPrediction(id, { fillForm = false } = {}) {
  clearTimeout(pollTimer);
  const p = await api(`/api/predictions/${id}`);
  P.current = p;
  if (fillForm) {
    P.viewing = p.id; P.trueClass = p.true_class; P.showErrors = false;
    fill(p.inputs); $("#pfLabel").value = p.label || "";
    Object.keys(P.modelsOn).forEach((k) => { P.modelsOn[k] = k in p.models; if (p.models[k]) P.models[k] = p.models[k]; });
    buildModelsOnly();
    $("#pfTitle").textContent = `Viewing #${p.id}${p.label ? " · " + p.label : ""}`;
    history.replaceState(null, "", "#predict/" + p.id);
    flashNote(`Loaded from history — nothing was re-run. Change any value and press Predict to save it as a new record, or "New patient" to start empty.`);
  }
  paintResult(); paintHistory(); validateAll();
  if (["queued", "running"].includes(p.status)) pollTimer = setTimeout(() => loadPrediction(id), 800);
  else if (fillForm === false) { loadHistory(); refreshSchema(); }
}
function buildModelsOnly() {
  document.querySelectorAll(".mdl").forEach((el) => {
    const k = el.dataset.m; el.classList.toggle("on", P.modelsOn[k]);
    el.querySelector("input").checked = P.modelsOn[k];
    const sel = el.querySelector("select"); if (sel) sel.value = P.models[k];
  });
  warmHint();
}
async function refreshSchema() { try { P.schema.loaded = (await api("/api/predict/schema")).loaded; warmHint(); } catch { /* ignore */ } }

/* ---------- result ---------- */
function stackBar(p) { return `<div class="stack">${p.map((x, i) => `<span class="s${i}" style="width:${x * 100}%" title="${CLS[i]} ${pct(x)}"></span>`).join("")}</div>`; }

function paintResult() {
  const p = P.current, body = $("#prBody");
  if (!p) {
    $("#prTitle").textContent = "Result"; $("#prMeta").textContent = "";
    body.innerHTML = `<div class="pr-empty"><b>Enter one patient's data on the left and press Predict.</b><br>
      Every prediction is saved to history (Postgres + MinIO). Click a history item to reopen it without re-running.<br>
      <span class="muted">“Test patient” fills a real held-out patient so you can check the model against the true class.</span></div>`;
    return;
  }
  const R = p.results || {}, cons = R._consensus, running = ["queued", "running"].includes(p.status);
  $("#prTitle").textContent = `Result · #${p.id}${p.label ? " · " + p.label : ""}`;
  $("#prMeta").textContent = `${new Date(p.created_at).toLocaleString()}${p.seconds != null ? " · " + fmtTime(p.seconds) : ""}`;
  const modelKeys = Object.keys(p.models);

  let html = "";
  if (cons) {
    const c = cons.pred, conf = cons.proba[c];
    html += `<div class="verdict c${c}"><div class="vt"><span class="k">Predicted hair-fall risk${cons.n > 1 ? ` · average of ${cons.n} models` : ""}</span>
      <span class="big">${CLS[c]}</span></div><span class="spacer"></span>
      <div class="conf"><div class="muted">${cons.n > 1 ? (cons.agree ? "✓ all models agree" : "⚠ models disagree") : "probability"}</div><div class="v">${pct(conf)}</div></div></div>
      ${stackBar(cons.proba)}<div class="legend">${cons.proba.map((x, i) => `<span><i class="s${i}" style="background:var(--c${i})"></i>${CLS[i]} ${pct(x)}</span>`).join("")}</div><div style="height:8px"></div>`;
  } else if (running) {
    html += `<div class="verdict"><div class="runline"><span class="spin"></span>Predicting…</div></div>`;
  } else {
    html += `<div class="verdict c2"><div class="vt"><span class="k">Prediction failed</span><span>See the model errors below.</span></div></div>`;
  }
  if (p.true_class != null && cons) {
    const ok = p.true_class === cons.pred;
    html += `<div class="truth ${ok ? "yes" : "no"}">Test-set patient · true class <b>${CLS[p.true_class]}</b> — ${ok ? "✓ prediction correct" : "✗ prediction wrong"}</div>`;
  }

  html += `<div class="pr-sec"><div class="pr-sec-h">Per model</div><table class="mt">
    <tr><th class="l">Model</th><th class="l">Context</th><th class="l">Prediction</th><th class="l pb">Low · Moderate · High</th><th>Low</th><th>Mod</th><th>High</th><th>Time</th></tr>
    ${modelKeys.map((k) => {
      const r = R[k] || { status: "queued", size: p.models[k] };
      if (r.status === "ok") return `<tr><td class="l"><b>${MODEL_NAMES[k]}</b></td><td class="l">${esc(r.size)}</td><td class="l">${clsBadge(r.pred)}</td>
        <td class="l pb"><div class="mbar">${r.proba.map((x, i) => `<span style="width:${x * 100}%;background:var(--c${i})"></span>`).join("")}</div></td>
        ${r.proba.map((x, i) => `<td style="${i === r.pred ? "font-weight:700" : ""}">${pct(x)}</td>`).join("")}<td>${fmtTime(r.seconds)}</td></tr>`;
      if (r.status === "error") return `<tr><td class="l"><b>${MODEL_NAMES[k]}</b></td><td class="l">${esc(r.size)}</td><td class="l" colspan="6"><span class="cls err">error</span> <span class="muted">${esc(r.error)}</span></td></tr>`;
      return `<tr><td class="l"><b>${MODEL_NAMES[k]}</b></td><td class="l">${esc(r.size)}</td><td class="l" colspan="6"><span class="runline">${r.status === "running" ? `<span class="spin"></span>running…` : "waiting…"}</span></td></tr>`;
    }).join("")}</table></div>`;

  const cb = R.catboost && R.catboost.shap;
  if (cb) {
    const mx = Math.max(...cb.top.map((t) => Math.abs(t.value))) || 1;
    html += `<div class="pr-sec"><div class="pr-sec-h">Why? — CatBoost SHAP for “${CLS[cb.class]}”<span class="spacer"></span><span class="n"><span style="color:var(--c${cb.class})">■</span> pushes towards ${CLS[cb.class]} · <span style="color:var(--muted)">■</span> pushes away</span></div>
      ${cb.top.map((t) => { const f = P.byName[t.feature], w = (Math.abs(t.value) / mx) * 50;
        return `<div class="shap-row"><span class="f" title="${esc(f ? f.label : t.feature)}">${esc(f ? f.label : t.feature)} <span class="pv">= ${esc(f ? fmtVal(f, p.inputs[t.feature]) : p.inputs[t.feature])}</span></span>
          <span class="track"><span class="${t.value >= 0 ? "pos" : "neg"}" style="width:${w}%;${t.value >= 0 ? `background:var(--c${cb.class})` : ""}"></span></span><span class="v">${t.value > 0 ? "+" : ""}${t.value.toFixed(3)}</span></div>`; }).join("")}</div>`;
  }

  const flags = P.fields.filter((f) => f.normal).map((f) => { const v = p.inputs[f.name]; return { f, v, st: v < f.normal[0] ? "low" : v > f.normal[1] ? "high" : "" }; }).filter((x) => x.st);
  html += `<div class="pr-sec"><div class="pr-sec-h">Blood tests outside the normal range<span class="n">${flags.length ? "" : " — none"}</span></div>
    <div class="flags">${flags.map(({ f, v, st }) => `<span class="fchip ${st}" title="normal ${f.normal[0]}–${f.normal[1]} ${f.unit}">${esc(f.label)} ${fmtVal(f, v)} ${esc(f.unit)} · ${st.toUpperCase()}</span>`).join("")}</div></div>`;

  html += `<div class="pr-sec"><div class="pr-sec-h">Patient data</div><div class="inp-grid">
    ${P.fields.map((f) => `<div><span>${esc(f.label)}</span><span>${esc(fmtVal(f, p.inputs[f.name]))}${f.unit && f.kind !== "bool" ? " " + esc(f.unit) : ""}</span></div>`).join("")}</div>
    <div class="pr-foot">${p.minio_key ? `<a class="btn" href="/api/files/${p.minio_key}?download=true">⬇ Record (JSON)</a>` : ""}
      <button class="btn ghost-danger" id="prDelete">Delete from history</button></div>
    <div class="disclaimer">Research prototype from the thesis models — not a medical diagnosis.</div></div>`;

  body.innerHTML = html;
  $("#prDelete").onclick = () => deletePrediction(p.id);
}

/* ---------- history ---------- */
async function loadHistory() {
  try { P.history = await api(`/api/predictions${P.q ? "?q=" + encodeURIComponent(P.q) : ""}`); } catch { P.history = []; }
  paintHistory();
}
function paintHistory() {
  const list = $("#phList");
  $("#phCount").textContent = P.history.length ? P.history.length : "";
  if (!P.history.length) { list.innerHTML = `<div class="ph-empty">${P.q ? "No matches." : "No predictions yet."}</div>`; return; }
  let day = "";
  list.innerHTML = P.history.map((h) => {
    const d = new Date(h.created_at), dk = d.toLocaleDateString();
    const head = dk !== day ? `<div class="ph-day">${d.toDateString() === new Date().toDateString() ? "Today" : dk}</div>` : "";
    day = dk;
    const running = ["queued", "running"].includes(h.status);
    const tick = h.true_class != null && h.pred != null ? (h.true_class === h.pred ? " ✓" : " ✗") : "";
    return `${head}<div class="ph-item ${P.current && P.current.id === h.id ? "active" : ""}" data-id="${h.id}" title="${esc(h.label || "Patient #" + h.id)}">
      <span class="nm">${esc(h.label || "Patient #" + h.id)}</span>
      <span class="cl">${running ? `<span class="cls run">…</span>` : h.status === "error" ? `<span class="cls err">error</span>` : clsBadge(h.pred)}</span>
      <span class="mt">#${h.id} · ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · ${Object.keys(h.models).map((k) => ({ catboost: "CB", tabpfn: "PFN", tabfm: "FM" })[k]).join("·")}${tick}</span>
      <button class="del" title="Delete from history">✕</button></div>`;
  }).join("");
  list.querySelectorAll(".ph-item").forEach((el) => {
    el.onclick = (e) => { if (e.target.closest(".del")) return; loadPrediction(Number(el.dataset.id), { fillForm: true }); };
    el.querySelector(".del").onclick = () => deletePrediction(Number(el.dataset.id));
  });
}
async function deletePrediction(id) {
  if (!confirm(`Delete prediction #${id} from history (Postgres + MinIO)?`)) return;
  await api(`/api/predictions/${id}`, { method: "DELETE" });
  if (P.current && P.current.id === id) clearForm();
  loadHistory();
}

/* ---------- split divider ---------- */
(() => {
  const view = $("#predict"), dv = $("#pDivider");
  const set = (px) => view.style.setProperty("--pf-w", px + "px");
  const saved = parseFloat(localStorageGet("pfW")); if (saved) set(saved);
  dv.addEventListener("pointerdown", (e) => { dv.setPointerCapture(e.pointerId); dv.classList.add("drag"); document.body.style.userSelect = "none"; });
  dv.addEventListener("pointermove", (e) => {
    if (!dv.classList.contains("drag")) return;
    const left = $("#pfPane").getBoundingClientRect().left, total = view.getBoundingClientRect().right - left;
    const w = Math.min(total - 260, Math.max(300, e.clientX - left)); set(w); dv.dataset.w = w;
  });
  dv.addEventListener("pointerup", () => { dv.classList.remove("drag"); document.body.style.userSelect = ""; if (dv.dataset.w) localStorageSet("pfW", dv.dataset.w); });
  dv.addEventListener("dblclick", () => { view.style.removeProperty("--pf-w"); localStorageSet("pfW", ""); });
})();

/* ---------- wiring ---------- */
$("#pfPredict").onclick = doPredict;
$("#pfNew").onclick = clearForm;
$("#pfTypical").onclick = () => { markDirty(); P.fields.forEach((f) => { if (f.kind !== "bool") setValue(f.name, f.default); }); flashNote("Filled numbers with typical (median) values — adjust to your patient."); };
$("#pfSample").onclick = async () => {
  const s = await api("/api/predict/sample");
  clearForm(); fill(s.inputs); P.trueClass = s.true_class;
  $("#pfLabel").value = `Test row ${s.row}`;
  $("#pfTitle").textContent = "Test-set patient";
  flashNote(`Real held-out patient (true class: ${CLS[s.true_class]}). Press Predict to check the models.`);
};
$("#pfLabel").addEventListener("input", markDirty);
let phTimer;
$("#phSearch").oninput = (e) => { clearTimeout(phTimer); phTimer = setTimeout(() => { P.q = e.target.value.trim(); loadHistory(); }, 250); };
document.addEventListener("keydown", (e) => {
  if ($("#predict").classList.contains("hidden")) return;
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); if (!$("#pfPredict").disabled) doPredict(); }
});

(async function initPredict() {
  loadModelPrefs();
  try {
    P.schema = await api("/api/predict/schema");
  } catch (e) { $("#pfFields").innerHTML = `<div class="muted">Backend offline (${esc(e.message)}).</div>`; return; }
  P.fields = P.schema.fields; P.byName = Object.fromEntries(P.fields.map((f) => [f.name, f]));
  buildForm(); clearForm(); loadHistory();
  $("#pfLabel").blur();
  const m = location.hash.match(/^#predict\/(\d+)/);   // deep link: /#predict/12 opens that saved prediction
  if (m) loadPrediction(Number(m[1]), { fillForm: true });
})();
