/* Predict tab: a person enters their data -> "will I have hair fall?" in plain words (For you),
   with the full model calculations one click away (Developer). Every check is saved (Postgres + MinIO). */
const P = { schema: null, fields: [], byName: {}, models: {}, history: [], current: null, viewing: null, q: "", showErrors: false,
  view: localStorageGet("prView") || "patient" };
const CLS = ["Low", "Moderate", "High"];
const MODEL_NAMES = { catboost: "CatBoost", tabpfn: "TabPFN", tabfm: "TabFM" };
const pct = (x) => (x * 100).toFixed(1) + "%";
const pct0 = (x) => Math.round(x * 100) + "%";
const clsBadge = (c) => (c == null ? "" : `<span class="cls c${c}">${CLS[c]}</span>`);
const fmtNum = (v) => Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
const fmtVal = (f, v) => (v == null || v === "" ? "–" : f.kind === "choice" ? (f.options.find((o) => o.value == v) || {}).label
  : f.kind === "bool" ? (Number(v) ? "Yes" : "No") : fmtNum(v));
const decimals = (step) => (step >= 1 ? 0 : Math.round(-Math.log10(step)));
const riskScore = (p) => Math.round(p[1] * 50 + p[2] * 100);   // 0 = surely Low, 50 = Moderate, 100 = surely High

/* ================= form ================= */
function buildForm() {
  const groups = {};
  P.fields.forEach((f) => (groups[f.group] ||= []).push(f));
  const notes = { "Blood test results": "from your lab report · green = normal range", "Health & lifestyle": "answer yes or no" };
  $("#pfFields").innerHTML = Object.entries(groups).map(([g, fs]) => `
    <div class="pf-sec"><div class="pf-sec-h">${esc(g)}${notes[g] ? `<span class="n">${notes[g]}</span>` : ""}</div>
      <div class="pf-grid ${fs.every((f) => f.kind === "bool") ? "bools" : ""}">${fs.map(fieldHtml).join("")}</div></div>`).join("");
  P.fields.forEach(wireField);
}

function fieldHtml(f) {
  if (f.kind === "bool") return `<div class="fld b" data-f="${f.name}"><span class="lb"><b title="${esc(f.label)}">${esc(f.label)}</b></span>
    <div class="seg yes"><button type="button" data-v="0">No</button><button type="button" data-v="1">Yes</button></div></div>`;
  if (f.kind === "choice") return `<div class="fld" data-f="${f.name}"><span class="lb"><b>${esc(f.label)}</b></span>
    <div class="seg">${f.options.map((o) => `<button type="button" data-v="${o.value}">${esc(o.label)}</button>`).join("")}</div><span class="hint">&nbsp;</span></div>`;
  const span = f.max - f.min, nz = f.normal ? `<span class="nz" style="left:${((f.normal[0] - f.min) / span) * 100}%;width:${((Math.min(f.normal[1], f.max) - f.normal[0]) / span) * 100}%"></span>` : "";
  return `<div class="fld" data-f="${f.name}" title="${esc(f.help || f.label)}${f.normal ? ` · normal ${f.normal[0]}–${f.normal[1]} ${f.unit}` : ""}">
    <span class="lb"><b>${esc(f.label)}</b><span class="u">${esc(f.unit)}</span><span class="fl"></span></span>
    <input class="in" type="number" inputmode="decimal" min="${f.min}" max="${f.max}" step="${f.step}" placeholder="${f.min} – ${f.max}">
    <div class="rg">${nz}<span class="mk hidden"></span></div>
    <span class="hint"><span>${f.normal ? `normal ${f.normal[0]}–${f.normal[1]}` : ""}</span><span class="err"></span></span></div>`;
}
const fieldEl = (name) => document.querySelector(`.fld[data-f="${name}"]`);

function wireField(f) {
  const el = fieldEl(f.name);
  if (f.kind === "bool" || f.kind === "choice") {
    el.querySelectorAll(".seg button").forEach((b) => b.onclick = () => { setValue(f.name, Number(b.dataset.v)); markDirty(); });
    return;
  }
  const inp = el.querySelector("input");
  inp.addEventListener("keydown", (e) => {   // characters that can never be valid
    if (["e", "E", "+"].includes(e.key) || (e.key === "-" && f.min >= 0) || (e.key === "." && f.kind === "int")) e.preventDefault();
    if (e.key === "Enter") { e.preventDefault(); const all = [...document.querySelectorAll("#pfFields input.in")]; all[all.indexOf(inp) + 1]?.focus(); }
  });
  inp.addEventListener("input", () => { paintField(f); markDirty(); validateAll(); });
  inp.addEventListener("change", () => {   // leaving the box: pull an out-of-range value back to the nearest limit
    if (inp.value === "") { paintField(f); validateAll(); return; }
    const v = Number(inp.value), r = Number(Math.min(f.max, Math.max(f.min, v)).toFixed(decimals(f.step)));
    if (r !== v) { inp.value = r; inp.classList.remove("flash"); void inp.offsetWidth; inp.classList.add("flash");
      flashNote(`${f.label} can only be ${f.min}–${f.max} ${f.unit} — changed ${v} to ${r}.`); }
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
  if (v < f.min || v > f.max) return `only ${f.min}–${f.max}`;
  if (f.kind !== "float" && !Number.isInteger(v)) return "whole number";
  return "";
}
function bioState(f, v) { return !f.normal || v == null ? "" : v < f.normal[0] ? "low" : v > f.normal[1] ? "high" : "ok"; }

function paintField(f) {
  const el = fieldEl(f.name), v = getValue(f.name);
  if (f.kind === "bool" || f.kind === "choice") { el.querySelector(".seg").classList.toggle("need", P.showErrors && v == null); return; }
  const inp = el.querySelector("input"), err = fieldError(f, v), shown = err && (v != null || P.showErrors);
  inp.classList.toggle("bad", !!shown);
  el.querySelector(".err").textContent = shown ? err : "";
  const mk = el.querySelector(".mk"), fl = el.querySelector(".fl");
  if (v == null || err) { mk.classList.add("hidden"); fl.textContent = ""; fl.className = "fl"; return; }
  mk.classList.remove("hidden");
  mk.style.left = ((v - f.min) / (f.max - f.min)) * 100 + "%";
  const st = bioState(f, v);
  fl.className = "fl " + st;
  fl.textContent = st === "low" ? "LOW" : st === "high" ? "HIGH" : st === "ok" ? "normal" : "";
}

function validateAll() {
  const missing = P.fields.filter((f) => fieldError(f, getValue(f.name)));
  const st = $("#pfStatus"), busy = P.current && ["queued", "running"].includes(P.current.status);
  $("#pfPredict").disabled = !!busy;
  st.textContent = missing.length ? `${missing.length} left to fill: ${missing.slice(0, 3).map((f) => f.label).join(", ")}${missing.length > 3 ? "…" : ""}` : "✓ Ready";
  return !missing.length;
}
let noteTimer;
function flashNote(t, sticky = false) {
  const n = $("#pfNote"); n.textContent = t; n.classList.remove("hidden");
  clearTimeout(noteTimer); if (!sticky) noteTimer = setTimeout(() => n.classList.add("hidden"), 4000);
}
function markDirty() { if (P.viewing) { P.viewing = null; $("#pfTitle").textContent = "Your details (edited)"; paintHistory(); } }
function fill(inputs) { P.fields.forEach((f) => setValue(f.name, inputs[f.name] ?? null)); }
function clearForm() {
  P.viewing = null; P.showErrors = false; P.current = null;
  $("#pfLabel").value = ""; fill({});
  P.fields.filter((f) => f.kind === "bool").forEach((f) => setValue(f.name, 0));
  $("#pfTitle").textContent = "Your details"; $("#pfNote").classList.add("hidden");
  if (!$("#predict").classList.contains("hidden")) history.replaceState(null, "", "#predict");
  paintResult(); paintHistory();
  document.querySelector("#pfFields input.in")?.focus();
}

/* ================= run a check ================= */
async function doPredict() {
  P.showErrors = true; P.fields.forEach(paintField);
  if (!validateAll()) {
    const first = P.fields.find((f) => fieldError(f, getValue(f.name)));
    fieldEl(first.name)?.scrollIntoView({ block: "center", behavior: "smooth" });
    fieldEl(first.name)?.querySelector("input")?.focus();
    return;
  }
  const inputs = Object.fromEntries(P.fields.map((f) => [f.name, getValue(f.name)]));
  try {
    const r = await fetch("/api/predict", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ label: $("#pfLabel").value, inputs, models: P.models }) });
    const d = await r.json();
    if (!r.ok) {
      const errs = d.detail && d.detail.fields;
      flashNote(errs ? "Please fix: " + Object.entries(errs).map(([k, v]) => `${P.byName[k]?.label || k} ${v}`).join("; ") : String(d.detail || r.statusText), true);
      return;
    }
    P.viewing = d.id;
    await loadPrediction(d.id);
    loadHistory();
  } catch (e) { flashNote("Could not reach the server: " + e.message, true); }
}

let pollTimer;
async function loadPrediction(id, { fillForm = false } = {}) {
  clearTimeout(pollTimer);
  const p = await api(`/api/predictions/${id}`);
  P.current = p;
  history.replaceState(null, "", "#predict/" + p.id);
  if (fillForm) {
    P.viewing = p.id; P.showErrors = false;
    fill(p.inputs); $("#pfLabel").value = p.label || "";
    $("#pfTitle").textContent = `Your details · check #${p.id}`;
    flashNote("Opened from history — nothing was re-calculated. Change a value and check again to save a new result, or press “New check”.");
  }
  paintResult(); paintHistory(); validateAll();
  if (["queued", "running"].includes(p.status)) pollTimer = setTimeout(() => loadPrediction(id), 800);
  else if (!fillForm) loadHistory();
}

/* ================= plain-language helpers ================= */
const BOOL_TEXT = {
  family_hair_fall_history: ["No family history of hair fall", "Hair fall runs in your family"],
  chronic_illness: ["No chronic illness", "You have a chronic illness"],
  late_night_sleep: ["You don't sleep late", "You sleep late at night"],
  sleep_disturbance: ["Your sleep is undisturbed", "Your sleep is disturbed"],
  water_reason: ["Your water quality is fine", "Poor water quality"],
  chemical_use: ["You avoid chemical hair products", "You use chemical hair products"],
  anemia: ["No anemia", "You have anemia"],
  stress: ["You don't often feel stressed", "You often feel stressed"],
};
function factorText(name, v) {
  const f = P.byName[name];
  if (!f) return name;
  if (f.kind === "bool") return (BOOL_TEXT[name] || [`${f.label}: no`, `${f.label}: yes`])[Number(v)];
  if (name === "age") return `Your age (${v})`;
  if (name === "gender") return `Gender (${fmtVal(f, v)})`;
  if (f.normal) {
    const st = bioState(f, v);
    return `${f.label} is ${st === "low" ? "<b>low</b>" : st === "high" ? "<b>high</b>" : "normal"} — ${fmtNum(v)} ${f.unit} <span class="muted">(normal ${f.normal[0]}–${f.normal[1]})</span>`;
  }
  return `${f.label} ${fmtNum(v)} <span class="muted">of ${f.max}</span>`;
}
const TIPS = {
  iron: "Iron: eat iron-rich food (leafy greens, lentils, beans, meat) and ask a doctor whether you need a supplement.",
  vitamin_d: "Vitamin D: get some safe daily sunlight and ask a doctor about a vitamin D test or supplement.",
  total_protein: "Protein: include enough protein (eggs, dairy, pulses, fish, meat) — hair is made of protein.",
  calcium: "Calcium: discuss your calcium result with a doctor.",
  manganese: "Manganese: discuss your manganese result with a doctor.",
  alt_liver: "Liver (ALT): an unusual ALT result is worth a check-up with a doctor.",
  body_water_content: "Hydration: drink water regularly through the day.",
  stress_level: "Stress: regular exercise, rest and relaxation (walks, breathing, yoga) help lower stress.",
  stress: "Stress: regular exercise, rest and relaxation (walks, breathing, yoga) help lower stress.",
  late_night_sleep: "Sleep: aim for a regular bedtime and 7–8 hours of sleep.",
  sleep_disturbance: "Sleep: aim for a regular bedtime and 7–8 hours of sleep.",
  chemical_use: "Hair care: reduce harsh chemical treatments (colouring, straightening) and heat styling.",
  water_reason: "Water: a filter or a final rinse with clean water can help if your water is hard or dirty.",
  anemia: "Anemia: follow up with a doctor — treating anemia often reduces hair fall.",
  chronic_illness: "Health: keep your chronic illness under regular medical care.",
};
const ANSWER = [
  { a: "Unlikely", t: "Your risk of hair fall is <b>low</b>.", s: "Your results look similar to people who did not have significant hair fall." },
  { a: "Possibly", t: "Your risk of hair fall is <b>moderate</b>.", s: "Some of your results are linked to hair fall. Small changes can help." },
  { a: "Likely", t: "Your risk of hair fall is <b>high</b>.", s: "Several of your results are strongly linked to hair fall. Consider seeing a doctor or dermatologist." },
];
function sureWord(x) { return x >= 0.9 ? "very sure" : x >= 0.7 ? "fairly sure" : x >= 0.5 ? "somewhat sure" : "not very sure"; }

function gauge(score, c) {   // semicircle 0-100 with Low / Moderate / High zones
  const R = 60, cx = 70, cy = 68, pt = (v) => { const a = Math.PI * (1 - v / 100); return [cx + R * Math.cos(a), cy - R * Math.sin(a)]; };
  const arc = (a, b, col) => { const [x1, y1] = pt(a), [x2, y2] = pt(b); return `<path d="M${x1} ${y1} A${R} ${R} 0 0 1 ${x2} ${y2}" stroke="${col}" stroke-width="11" fill="none"/>`; };
  const [nx, ny] = pt(score);
  return `<svg class="gauge" viewBox="0 0 140 80">${arc(0, 33.3, "var(--c0)")}${arc(33.4, 66.6, "var(--c1)")}${arc(66.7, 100, "var(--c2)")}
    <line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="var(--text)" stroke-width="2.5" stroke-linecap="round"/><circle cx="${cx}" cy="${cy}" r="4" fill="var(--text)"/>
    <text x="${cx}" y="${cy - 16}" text-anchor="middle" class="gv c${c}">${score}</text></svg>`;
}

/* ================= result: For you ================= */
function patientView(p) {
  const R = p.results || {}, cons = R._consensus, running = ["queued", "running"].includes(p.status);
  if (running || !cons) {
    if (!running) return `<div class="answer c2"><div><div class="q">Something went wrong</div><div>The check could not be completed. Switch to “Developer” for details.</div></div></div>`;
    const keys = Object.keys(p.models), done = keys.filter((k) => R[k] && ["ok", "error"].includes(R[k].status)).length;
    return `<div class="pr-wait"><span class="spin big"></span><div><b>Analysing your results…</b><br><span class="muted">Step ${Math.min(done + 1, keys.length)} of ${keys.length}. The first check after starting can take up to 30 seconds.</span></div></div>`;
  }
  const c = cons.pred, pr = cons.proba, score = riskScore(pr), A = ANSWER[c];
  let h = `<div class="answer c${c}">
      <div class="ans-l"><div class="q">Will I have hair fall?</div><div class="a">${A.a}</div><div class="t">${A.t}</div><div class="s">${A.s}</div></div>
      <div class="ans-r">${gauge(score, c)}<div class="gl"><span>Low</span><span>Risk score / 100</span><span>High</span></div></div>
    </div>
    <div class="pr-grid">
      <div class="card2"><div class="pr-sec-h">Chance of each outcome</div>
        ${pr.map((x, i) => `<div class="chance"><span class="cn">${["Low risk", "Moderate risk", "High risk"][i]}</span>
          <span class="ctrack"><span style="width:${x * 100}%;background:var(--c${i})"></span></span><span class="cv ${i === c ? "b" : ""}">${pct0(x)}</span></div>`).join("")}
        <div class="muted sure">We are <b>${sureWord(pr[c])}</b> (${pct0(pr[c])})${cons.n > 1 ? (cons.agree ? " — every check gave the same answer." : " — the checks did not fully agree.") : "."}</div>
      </div>
      <div class="card2"><div class="pr-sec-h">Your blood tests</div>${bloodChart(p.inputs)}</div>
    </div>`;

  const risk = R.catboost && R.catboost.shap && R.catboost.shap.risk;
  if (risk) {
    const up = risk.filter((r) => r.value > 0.02).slice(0, 5), down = risk.filter((r) => r.value < -0.02).slice(0, 5);
    const mx = Math.max(...risk.map((r) => Math.abs(r.value))) || 1;
    const item = (r, cls) => `<div class="reason ${cls}"><span class="rt">${factorText(r.feature, p.inputs[r.feature])}</span>
      <span class="rs" title="impact"><span style="width:${Math.max(8, (Math.abs(r.value) / mx) * 100)}%"></span></span></div>`;
    h += `<div class="pr-grid">
      <div class="card2 up"><div class="pr-sec-h">▲ What raises your risk</div>${up.length ? up.map((r) => item(r, "up")).join("") : `<div class="muted">Nothing important.</div>`}</div>
      <div class="card2 down"><div class="pr-sec-h">▼ What lowers your risk</div>${down.length ? down.map((r) => item(r, "down")).join("") : `<div class="muted">Nothing important.</div>`}</div>
    </div>`;
    const tips = [...new Set(up.map((r) => TIPS[r.feature]).filter(Boolean))];
    h += `<div class="card2 tips"><div class="pr-sec-h">What you can do</div>
      ${tips.length ? `<ul>${tips.map((t) => `<li>${esc(t).replace(/^([^:]+):/, "<b>$1:</b>")}</li>`).join("")}</ul>` : `<div>Keep up your current routine — nothing you can change stands out as a risk.</div>`}</div>`;
  }
  h += `<div class="disclaimer">This is an estimate from a research model trained on ${P.schema.context_rows.toLocaleString()} people — not a medical diagnosis. If you are worried about hair fall, talk to a doctor or dermatologist.</div>`;
  return h;
}

function bloodChart(inputs) {
  return `<div class="blood">${P.fields.filter((f) => f.normal).map((f) => {
    const v = inputs[f.name], span = f.max - f.min, st = bioState(f, v);
    return `<div class="brow"><span class="bn">${esc(f.label)}</span>
      <span class="btrack"><span class="bz" style="left:${((f.normal[0] - f.min) / span) * 100}%;width:${((Math.min(f.normal[1], f.max) - f.normal[0]) / span) * 100}%"></span>
        <span class="bm ${st}" style="left:${((v - f.min) / span) * 100}%"></span></span>
      <span class="bv">${fmtNum(v)}</span><span class="fl ${st}">${st === "ok" ? "normal" : st.toUpperCase()}</span></div>`;
  }).join("")}</div>`;
}

/* ================= result: Developer ================= */
function devView(p) {
  const R = p.results || {}, cons = R._consensus, keys = Object.keys(p.models);
  const ok = keys.filter((k) => R[k] && R[k].status === "ok");
  let h = `<div class="pr-sec"><div class="pr-sec-h">Per model<span class="spacer"></span><span class="n">status ${esc(p.status)} · total ${fmtTime(p.seconds)}</span></div><table class="mt">
    <tr><th class="l">Model</th><th class="l">Context rows</th><th class="l">Class</th><th>P(Low)</th><th>P(Moderate)</th><th>P(High)</th><th>Predict</th><th>Total</th></tr>
    ${keys.map((k) => { const r = R[k] || { status: "queued", size: p.models[k] };
      if (r.status === "ok") return `<tr><td class="l"><b>${MODEL_NAMES[k]}</b></td><td class="l">${esc(r.size)}</td><td class="l">${clsBadge(r.pred)}</td>
        ${r.proba.map((x, i) => `<td class="${i === r.pred ? "b" : ""}">${x.toFixed(4)}</td>`).join("")}<td>${fmtTime(r.predict_seconds)}</td><td>${fmtTime(r.seconds)}</td></tr>`;
      return `<tr><td class="l"><b>${MODEL_NAMES[k]}</b></td><td class="l">${esc(r.size)}</td><td class="l" colspan="6">${r.status === "error" ? `<span class="cls err">error</span> ${esc(r.error)}` : `<span class="runline"><span class="spin"></span>${r.status}</span>`}</td></tr>`;
    }).join("")}</table></div>`;
  if (cons) {
    h += `<div class="pr-sec"><div class="pr-sec-h">Calculation</div><div class="calc">
      ${CLS.map((c, i) => `P̄(${c}) = (${ok.map((k) => R[k].proba[i].toFixed(4)).join(" + ")}) / ${ok.length} = <b>${cons.proba[i].toFixed(4)}</b>`).join("<br>")}<br>
      Prediction = argmax P̄ = <b>${CLS[cons.pred]}</b> · models agree: ${cons.agree ? "yes" : "no"}<br>
      Risk score = 50·P̄(Moderate) + 100·P̄(High) = 50·${cons.proba[1].toFixed(4)} + 100·${cons.proba[2].toFixed(4)} = <b>${riskScore(cons.proba)}</b><br>
      Confidence shown to the user = P̄(${CLS[cons.pred]}) = ${pct(cons.proba[cons.pred])} → “${sureWord(cons.proba[cons.pred])}”</div></div>`;
  }
  const sh = R.catboost && R.catboost.shap;
  if (sh && sh.all) {
    const rows = sh.features.map((f, i) => ({ f, i, risk: sh.all.High[i] - sh.all.Low[i] })).sort((a, b) => Math.abs(b.risk) - Math.abs(a.risk));
    h += `<div class="pr-sec"><div class="pr-sec-h">CatBoost SHAP values (log-odds)<span class="spacer"></span><span class="n">reason = SHAP(High) − SHAP(Low); &gt; 0 raises risk, threshold ±0.02</span></div>
      <table class="mt"><tr><th class="l">Feature</th><th>Value</th><th>Low</th><th>Moderate</th><th>High</th><th>High − Low</th></tr>
      ${rows.map(({ f, i, risk }) => `<tr><td class="l">${esc(P.byName[f]?.label || f)}</td><td>${esc(fmtVal(P.byName[f] || {}, p.inputs[f]))}</td>
        ${CLS.map((c) => `<td>${sh.all[c][i].toFixed(3)}</td>`).join("")}<td class="${risk > 0.02 ? "up" : risk < -0.02 ? "down" : ""}">${risk > 0 ? "+" : ""}${risk.toFixed(3)}</td></tr>`).join("")}</table></div>`;
  } else if (sh) {
    h += `<div class="muted">This record was saved before full SHAP values were stored.</div>`;
  }
  if (p.true_class != null) h += `<div class="pr-sec muted">Known true class: <b>${CLS[p.true_class]}</b>${cons ? ` — ${p.true_class === cons.pred ? "correct" : "wrong"}` : ""}</div>`;
  h += `<div class="pr-foot">${p.minio_key ? `<a class="btn" href="/api/files/${p.minio_key}?download=true">⬇ Record JSON (MinIO)</a>` : ""}
    <span class="muted">Postgres table <code>predictions</code> · id ${p.id}</span></div>`;
  return h;
}

/* ================= result pane ================= */
function paintResult() {
  const p = P.current, body = $("#prBody");
  document.querySelectorAll("#prView button").forEach((b) => b.classList.toggle("on", b.dataset.v === P.view));
  if (!p) {
    $("#prTitle").textContent = "Result"; $("#prMeta").textContent = "";
    body.innerHTML = `<div class="pr-empty"><div class="big-q">Will I have hair fall?</div>
      Fill in your details on the left — your blood test results, a few scores and some yes/no questions —<br>then press <b>Check my hair-fall risk</b>.<br>
      <span class="muted">You'll see your risk, the chance of each outcome, the main reasons and what you can do. Every check is saved in the history on the far left.</span></div>`;
    return;
  }
  $("#prTitle").textContent = `Result${p.label ? " · " + p.label : ""}`;
  $("#prMeta").textContent = `#${p.id} · ${new Date(p.created_at).toLocaleString()}`;
  const top = body.scrollTop;
  body.innerHTML = P.view === "dev" ? devView(p) : patientView(p);
  body.scrollTop = top;
}
document.querySelectorAll("#prView button").forEach((b) => b.onclick = () => { P.view = b.dataset.v; localStorageSet("prView", P.view); paintResult(); });

/* ================= history ================= */
async function loadHistory() {
  try { P.history = await api(`/api/predictions${P.q ? "?q=" + encodeURIComponent(P.q) : ""}`); } catch { P.history = []; }
  paintHistory();
}
function paintHistory() {
  const list = $("#phList");
  $("#phCount").textContent = P.history.length || "";
  if (!P.history.length) { list.innerHTML = `<div class="ph-empty">${P.q ? "No matches." : "No checks yet."}</div>`; return; }
  let day = "";
  list.innerHTML = P.history.map((h) => {
    const d = new Date(h.created_at), dk = d.toLocaleDateString();
    const head = dk !== day ? `<div class="ph-day">${d.toDateString() === new Date().toDateString() ? "Today" : dk}</div>` : "";
    day = dk;
    const running = ["queued", "running"].includes(h.status);
    return `${head}<div class="ph-item ${P.current && P.current.id === h.id ? "active" : ""}" data-id="${h.id}" title="${esc(h.label || "Check #" + h.id)}">
      <span class="nm">${esc(h.label || "Check #" + h.id)}</span>
      <span class="cl">${running ? `<span class="cls run">…</span>` : h.status === "error" ? `<span class="cls err">error</span>` : clsBadge(h.pred)}</span>
      <span class="mt">#${h.id} · ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
      <button class="del" title="Delete this check">✕</button></div>`;
  }).join("");
  list.querySelectorAll(".ph-item").forEach((el) => {
    el.onclick = (e) => { if (!e.target.closest(".del")) loadPrediction(Number(el.dataset.id), { fillForm: true }); };
    el.querySelector(".del").onclick = () => deletePrediction(Number(el.dataset.id));
  });
}
async function deletePrediction(id) {
  if (!confirm(`Delete check #${id} from history?`)) return;
  await api(`/api/predictions/${id}`, { method: "DELETE" });
  if (P.current && P.current.id === id) clearForm();
  loadHistory();
}

/* ================= split divider ================= */
(() => {
  const view = $("#predict"), dv = $("#pDivider");
  const set = (px) => view.style.setProperty("--pf-w", px + "px");
  const saved = parseFloat(localStorageGet("pfW")); if (saved) set(saved);
  dv.addEventListener("pointerdown", (e) => { dv.setPointerCapture(e.pointerId); dv.classList.add("drag"); document.body.style.userSelect = "none"; });
  dv.addEventListener("pointermove", (e) => {
    if (!dv.classList.contains("drag")) return;
    const left = $("#pfPane").getBoundingClientRect().left, total = view.getBoundingClientRect().right - left;
    const w = Math.min(total - 300, Math.max(300, e.clientX - left)); set(w); dv.dataset.w = w;
  });
  dv.addEventListener("pointerup", () => { dv.classList.remove("drag"); document.body.style.userSelect = ""; if (dv.dataset.w) localStorageSet("pfW", dv.dataset.w); });
  dv.addEventListener("dblclick", () => { view.style.removeProperty("--pf-w"); localStorageSet("pfW", ""); });
})();

/* ================= wiring ================= */
$("#pfPredict").onclick = doPredict;
$("#pfNew").onclick = clearForm;
$("#pfLabel").addEventListener("input", markDirty);
let phTimer;
$("#phSearch").oninput = (e) => { clearTimeout(phTimer); phTimer = setTimeout(() => { P.q = e.target.value.trim(); loadHistory(); }, 250); };
document.addEventListener("keydown", (e) => {
  if (!$("#predict").classList.contains("hidden") && e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); if (!$("#pfPredict").disabled) doPredict(); }
});

(async function initPredict() {
  try { P.schema = await api("/api/predict/schema"); }
  catch (e) { $("#pfFields").innerHTML = `<div class="muted">Server offline (${esc(e.message)}).</div>`; return; }
  P.fields = P.schema.fields; P.byName = Object.fromEntries(P.fields.map((f) => [f.name, f]));
  P.models = P.schema.default_models;
  const m = location.hash.match(/^#predict\/(\d+)/);   // /#predict/12 opens that saved check
  buildForm(); clearForm(); loadHistory();
  if (m) loadPrediction(Number(m[1]), { fillForm: true });
})();
