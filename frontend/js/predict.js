/* Risk check: guided form -> plain-language report (For you) with the model details one click away (Developer).
   Every check is saved in Postgres + MinIO and listed under History. */
const P = {
  schema: null, fields: [], byName: {}, values: {}, label: "", showErrors: false,
  current: null, history: [], q: "", mode: "new",
  view: new URLSearchParams(location.search).get("view") === "dev" ? "dev" : store.get("prView", "patient"),
};

const GROUP_META = {
  "About you": { icon: "user", sub: "" },
  "Blood test results": { icon: "flask", sub: "Copy the numbers from your lab report (green band = healthy range). In the data, LOW protein, calcium, iron, vitamin D, manganese or body water go with more hair fall — a high ALT does too. High healthy-side values lower the risk." },
  "Other scores": { icon: "gauge", sub: "Rate each one on its scale." },
  "Health & lifestyle": { icon: "heart", sub: "Answer each question, or use “None of these apply”." },
};
const GROUP_TITLE = { "Other scores": "Wellbeing scores" };
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
const TIPS = {
  iron: ["food", "Boost your iron", "Eat iron-rich food such as leafy greens, lentils, beans and meat, and ask a doctor whether you need a supplement."],
  vitamin_d: ["sun", "Raise your vitamin D", "Get some safe daily sunlight and ask a doctor about a vitamin D test or supplement."],
  total_protein: ["food", "Eat enough protein", "Hair is made of protein — include eggs, dairy, pulses, fish or meat every day."],
  calcium: ["steth", "Check your calcium", "Your calcium result is outside the normal range — discuss it with a doctor."],
  manganese: ["steth", "Check your manganese", "Your manganese result is unusual — discuss it with a doctor."],
  alt_liver: ["steth", "Liver check-up", "An unusual ALT result is worth a check-up with a doctor."],
  body_water_content: ["drop", "Stay hydrated", "Drink water regularly through the day."],
  stress_level: ["heart", "Lower your stress", "Regular exercise, rest and relaxation — walks, breathing, yoga — help lower stress."],
  stress: ["heart", "Lower your stress", "Regular exercise, rest and relaxation — walks, breathing, yoga — help lower stress."],
  late_night_sleep: ["moon", "Sleep on time", "Aim for a regular bedtime and 7–8 hours of sleep."],
  sleep_disturbance: ["moon", "Improve your sleep", "Keep a regular bedtime, limit screens late at night and aim for 7–8 hours."],
  chemical_use: ["scissors", "Be gentle with your hair", "Reduce harsh chemical treatments (colouring, straightening) and heat styling."],
  water_reason: ["drop", "Wash with clean water", "A filter or a final rinse with clean water helps if your water is hard or dirty."],
  anemia: ["steth", "Follow up on anemia", "Treating anemia with a doctor often reduces hair fall."],
  chronic_illness: ["steth", "Keep your illness managed", "Keep your chronic illness under regular medical care."],
};
const ANSWER = [
  { a: "Unlikely", lead: "Your risk of hair fall is low.", sub: "Your results look like those of people who did not have significant hair fall." },
  { a: "Possibly", lead: "Your risk of hair fall is moderate.", sub: "Some of your results are linked to hair fall. A few changes can make a difference." },
  { a: "Likely", lead: "Your risk of hair fall is high.", sub: "Several of your results are strongly linked to hair fall. Consider talking to a doctor or dermatologist." },
];
const riskScore = (p) => Math.round(p[1] * 50 + p[2] * 100);   // 0 = surely Low · 50 = Moderate · 100 = surely High
const sureWord = (x) => (x >= 0.9 ? "very sure" : x >= 0.7 ? "fairly sure" : x >= 0.5 ? "somewhat sure" : "not very sure");
const decimals = (step) => (step >= 1 ? 0 : Math.round(-Math.log10(step)));
const bioState = (f, v) => (!f.normal || v == null ? "" : v < f.normal[0] ? "low" : v > f.normal[1] ? "high" : "ok");
const fmtVal = (f, v) => (v == null ? "–" : f.kind === "choice" ? (f.options.find((o) => o.value == v) || {}).label
  : f.kind === "bool" ? (Number(v) ? "Yes" : "No") : fmtNum(v));
const initials = (s) => (s || "").split(/[^\p{L}\p{N}]+/u).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "#";

/* ======================= shell ======================= */
function pShell() {
  $("#pWrap").innerHTML = `
    <div class="page-head">
      <div><h1>Hair-fall risk check</h1><p>Enter your lab results and a few answers about your lifestyle — see your risk and what drives it.</p></div>
      <span class="spacer"></span>
      <div class="seg" id="pSeg"><button data-m="new">${icon("plus")}New check</button><button data-m="history">${icon("history")}History <span class="count" id="pCount">0</span></button></div>
    </div>
    <div id="pForm"></div><div id="pResult" class="hidden"></div><div id="pHistory" class="hidden"></div>`;
  $$("#pSeg button").forEach((b) => b.onclick = () => {
    if (b.dataset.m === "new" && P.mode === "result") { resetValues(); paintAll(); }   // leaving a report starts a fresh check
    go("predict", b.dataset.m);
  });
}
function setMode(mode) {
  P.mode = mode;
  $("#pForm").classList.toggle("hidden", mode !== "new");
  $("#pResult").classList.toggle("hidden", mode !== "result");
  $("#pHistory").classList.toggle("hidden", mode !== "history");
  $$("#pSeg button").forEach((b) => b.classList.toggle("on", b.dataset.m === (mode === "history" ? "history" : "new")));
  $("#pPage").scrollTop = 0;
}

/* ======================= form ======================= */
function buildForm() {
  const groups = {};
  P.fields.forEach((f) => (groups[f.group] ||= []).push(f));
  $("#pForm").innerHTML = `<div class="note form-note hidden" id="pNote"></div><div class="stack-lg">${Object.entries(groups).map(([g, fs]) => {
    const meta = GROUP_META[g] || { icon: "info", sub: "" };
    const body = g === "Health & lifestyle" ? `<div class="qgrid">${fs.map(boolHtml).join("")}</div>`
      : g === "Other scores" ? `<div class="fgrid scores">${fs.map(sliderHtml).join("")}</div>`
      : `<div class="fgrid">${g === "About you" ? nameHtml() : ""}${fs.map(fieldHtml).join("")}</div>`;
    return `<section class="card card-pad"><div class="card-head"><span class="card-icon">${icon(meta.icon)}</span>
      <div><h2>${esc(GROUP_TITLE[g] || g)}</h2>${meta.sub ? `<p>${meta.sub}</p>` : ""}</div>
      ${g === "Health & lifestyle" ? `<span class="spacer"></span><button class="btn sm" id="pNone" title="Answer “No” to every question you have not answered yet">${icon("check")}None of these apply</button>` : ""}</div>${body}</section>`;
  }).join("")}</div>
    <div class="submit-bar">
      <div class="prog"><div class="prog-top"><span id="pProgText">–</span><b id="pProgPct"></b></div><div class="bar"><span id="pProgBar"></span></div></div>
      <button class="btn ghost" id="pClear">${icon("undo")}Clear</button>
      <button class="btn primary lg" id="pSubmit">Check my risk ${icon("arrow")}</button>
    </div>`;
  $("#pName").oninput = (e) => { P.label = e.target.value; };
  P.fields.forEach(wireField);
  $("#pNone").onclick = () => { P.fields.filter((f) => f.kind === "bool" && P.values[f.name] == null).forEach((f) => { P.values[f.name] = 0; paintField(f); }); paintProgress(); };
  $("#pClear").onclick = () => { if (confirm("Clear every answer and start again?")) { resetValues(); paintAll(); } };
  $("#pSubmit").onclick = submit;
}
const nameHtml = () => `<div class="field span2"><span class="flabel">Name <span class="opt">optional</span></span><input class="input" id="pName" maxlength="80" placeholder="Your name or patient ID"></div>`;
function fieldHtml(f) {
  if (f.kind === "choice") return `<div class="field span2" data-f="${f.name}"><span class="flabel">${esc(f.label)}</span>
    <div class="seg full">${f.options.map((o) => `<button type="button" data-v="${o.value}">${esc(o.label)}</button>`).join("")}</div></div>`;
  const span = f.max - f.min;
  const nz = f.normal ? `<span class="nz" style="left:${((f.normal[0] - f.min) / span) * 100}%;width:${((Math.min(f.normal[1], f.max) - f.normal[0]) / span) * 100}%"></span>` : "";
  return `<div class="field" data-f="${f.name}"><span class="flabel">${esc(f.label)}<span class="tag"></span></span>
    <div class="unit-in"><input class="input" type="number" inputmode="decimal" min="${f.min}" max="${f.max}" step="${f.step}" placeholder="${f.min} – ${f.max}"><span class="u">${esc(f.unit)}</span></div>
    ${f.normal ? `<div class="rtrack">${nz}<span class="mk hidden"></span></div>` : ""}
    <div class="fhint"><span>${f.normal ? `Healthy ${f.normal[0]}–${f.normal[1]} ${esc(f.unit)}` : `Allowed ${f.min}–${f.max}`}</span>${dirHtml(f)}<span class="err"></span></div></div>`;
}
function dirHtml(f) {   // which direction raises the risk in the training data (nothing shown when the effect is negligible)
  const e = f.risk_effect;
  if (Math.abs(e) < 0.12) return `<span class="dir none" data-tip="${esc(f.label)} has almost no effect on the result in this dataset">≈ no effect</span>`;
  const up = e > 0, strong = Math.abs(e) > 0.45;
  return `<span class="dir ${up ? "up" : "down"}" data-tip="In this dataset ${up ? "higher" : "lower"} ${esc(f.label.toLowerCase())} goes with ${strong ? "clearly " : ""}more hair fall">${up ? "↑ raises risk" : "↓ raises risk"}</span>`;
}
function sliderHtml(f) {
  return `<div class="field" data-f="${f.name}"><span class="flabel">${esc(f.label)}<span class="opt">${esc(f.unit)}</span></span>
    <div class="slider-row"><input type="range" min="${f.min}" max="${f.max}" step="1"><input class="input" type="number" inputmode="numeric" min="${f.min}" max="${f.max}" step="1" placeholder="–"></div>
    <div class="fhint"><span>${esc(f.help || "")}</span>${dirHtml(f)}<span class="err"></span></div></div>`;
}
const boolHtml = (f) => `<div class="q" data-f="${f.name}"><span class="qt">${esc(f.label)}</span>
  <div class="seg"><button type="button" data-v="0">No</button><button type="button" data-v="1">Yes</button></div></div>`;
const fieldEl = (n) => $(`#pForm [data-f="${n}"]`);

function wireField(f) {
  const el = fieldEl(f.name);
  if (f.kind === "bool" || f.kind === "choice") {
    $$(".seg button", el).forEach((b) => b.onclick = () => { P.values[f.name] = Number(b.dataset.v); paintField(f); paintProgress(); });
    return;
  }
  const inp = $("input[type=number]", el), range = $("input[type=range]", el);
  inp.addEventListener("keydown", (e) => {   // characters that can never be valid here
    if (["e", "E", "+"].includes(e.key) || (e.key === "-" && f.min >= 0) || (e.key === "." && f.kind === "int")) e.preventDefault();
    if (e.key === "Enter") { e.preventDefault(); const all = $$("#pForm input[type=number]"); all[all.indexOf(inp) + 1]?.focus(); }
  });
  inp.addEventListener("input", () => { P.values[f.name] = inp.value === "" ? null : Number(inp.value); paintField(f, true); paintProgress(); });
  inp.addEventListener("change", () => {   // leaving the box pulls an out-of-range value back to the nearest limit
    if (inp.value === "") return;
    const v = Number(inp.value), r = Number(Math.min(f.max, Math.max(f.min, v)).toFixed(decimals(f.step)));
    if (r !== v) {
      inp.classList.remove("flash"); void inp.offsetWidth; inp.classList.add("flash");
      showNote(`${f.label} can only be between ${f.min} and ${f.max} ${f.unit} — ${v} was changed to ${r}.`, true);
    }
    P.values[f.name] = r; paintField(f); paintProgress();
  });
  if (range) range.addEventListener("input", () => { P.values[f.name] = Number(range.value); paintField(f); paintProgress(); });
}

function fieldError(f, v) {
  if (v == null || Number.isNaN(v)) return "Required";
  if (v < f.min || v > f.max) return `Only ${f.min}–${f.max}`;
  if (f.kind !== "float" && !Number.isInteger(v)) return "Whole number";
  return "";
}
function paintField(f, typing = false) {
  const el = fieldEl(f.name), v = P.values[f.name];
  if (f.kind === "bool" || f.kind === "choice") {
    $$(".seg button", el).forEach((b) => b.classList.toggle("on", v != null && Number(b.dataset.v) === v));
    if (f.kind === "bool") el.classList.toggle("yes", v === 1);
    $(".seg", el).classList.toggle("need", P.showErrors && v == null);
    return;
  }
  const inp = $("input[type=number]", el), range = $("input[type=range]", el);
  if (!typing) inp.value = v == null ? "" : v;
  if (range) { range.value = v == null ? Math.round((f.min + f.max) / 2) : v; range.classList.toggle("unset", v == null); }
  const err = fieldError(f, v), shown = err && (v != null || P.showErrors);
  inp.classList.toggle("bad", !!shown);
  $(".err", el).textContent = shown ? err : "";
  const tag = $(".tag", el), mk = $(".mk", el), st = err ? "" : bioState(f, v);
  if (tag) { tag.className = "tag " + st; tag.textContent = st === "low" ? "LOW" : st === "high" ? "HIGH" : st === "ok" ? "HEALTHY" : ""; }
  if (mk) { mk.classList.toggle("hidden", !!err); mk.className = "mk " + st + (err ? " hidden" : ""); mk.style.left = ((v - f.min) / (f.max - f.min)) * 100 + "%"; }
}
function paintProgress() {
  const done = P.fields.filter((f) => !fieldError(f, P.values[f.name])).length, n = P.fields.length;
  $("#pProgText").innerHTML = done === n ? `<b>All ${n} answers complete</b> — ready to check` : `${done} of ${n} answered`;
  $("#pProgPct").textContent = Math.round((done / n) * 100) + "%";
  $("#pProgBar").style.width = (done / n) * 100 + "%";
}
function paintAll() { $("#pName").value = P.label; P.fields.forEach((f) => paintField(f)); paintProgress(); }
function resetValues() {
  P.values = {}; P.label = ""; P.showErrors = false;
  P.fields.forEach((f) => { P.values[f.name] = null; });   // nothing is pre-answered, so the progress bar starts at 0
  $("#pNote")?.classList.add("hidden");
}
let noteTimer;
function showNote(text, warn = false) {
  const n = $("#pNote");
  n.className = "note form-note" + (warn ? " warn" : "");
  n.innerHTML = icon("info") + `<span>${esc(text)}</span>`;
  clearTimeout(noteTimer); noteTimer = setTimeout(() => n.classList.add("hidden"), 6000);
}

async function submit() {
  P.showErrors = true; P.fields.forEach((f) => paintField(f));
  const missing = P.fields.find((f) => fieldError(f, P.values[f.name]));
  if (missing) {
    fieldEl(missing.name).scrollIntoView({ block: "center", behavior: "smooth" });
    $("input[type=number]", fieldEl(missing.name))?.focus({ preventScroll: true });
    return;
  }
  $("#pSubmit").disabled = true;
  try {
    const d = await api("/api/predict", { method: "POST", body: JSON.stringify({ label: P.label, inputs: P.values, models: P.schema.default_models }) });
    go("predict", String(d.id));
  } catch (e) {
    const errs = e.detail && e.detail.fields;
    showNote(errs ? "Please check: " + Object.entries(errs).map(([k, v]) => `${P.byName[k]?.label || k} ${v}`).join("; ") : "Could not reach the server: " + e.message, true);
  } finally { $("#pSubmit").disabled = false; }
}

/* ======================= result ======================= */
let pollTimer;
async function openResult(id) {
  clearTimeout(pollTimer);
  try { P.current = await api(`/api/predictions/${id}`); }
  catch { $("#pResult").innerHTML = `<div class="card empty">${icon("info")}<h3>Check #${esc(id)} not found</h3><p>It may have been deleted.</p></div>`; return; }
  renderResult();
  if (["queued", "running"].includes(P.current.status)) pollTimer = setTimeout(() => { if (P.mode === "result") openResult(id); }, 900);
  else loadHistory();
}

function renderResult() {
  const p = P.current, R = p.results || {}, cons = R._consensus;
  const running = ["queued", "running"].includes(p.status);
  const date = new Date(p.created_at);
  const head = `<div class="report-head">
      <div class="who"><h1>${esc(p.label || "Your result")}</h1><div class="meta">Check #${p.id} · ${date.toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" })}, ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div></div>
      ${running ? "" : `<div class="seg" id="pView"><button data-v="patient">${icon("user")}For you</button><button data-v="dev">${icon("code")}Developer</button></div>`}
      <button class="btn" id="pEdit">${icon("undo")}Edit answers</button>
    </div>`;
  let body;
  if (running) {
    const keys = Object.keys(p.models), done = keys.filter((k) => R[k] && ["ok", "error"].includes(R[k].status)).length;
    body = `<div class="card waiting"><span class="spin"></span><h2>Analysing your results…</h2>
      <div class="steps-dots">${keys.map((_, i) => `<i class="${i < done ? "done" : ""}"></i>`).join("")}</div>
      <p class="muted">Three independent models are checking your answers. The first check after starting the app can take up to 30 seconds.</p></div>`;
  } else if (!cons) {
    body = `<div class="card empty">${icon("info")}<h3>This check could not be completed</h3><p>Open the Developer view for the error details.</p></div>`;
    if (P.view === "dev") body += `<div style="margin-top:20px">${devView(p)}</div>`;
  } else body = P.view === "dev" ? devView(p) : patientView(p);
  $("#pResult").innerHTML = head + body;
  $$("#pView button").forEach((b) => { b.classList.toggle("on", b.dataset.v === P.view); b.onclick = () => { P.view = b.dataset.v; store.set("prView", P.view); renderResult(); }; });
  $("#pEdit").onclick = () => { P.values = { ...p.inputs }; P.label = p.label || ""; P.showErrors = false; paintAll(); go("predict", "new"); showNote(`Answers from check #${p.id} loaded — change anything and check again. The original result stays saved.`); };
}

function factorText(name, v) {
  const f = P.byName[name];
  if (!f) return esc(name);
  if (f.kind === "bool") return esc((BOOL_TEXT[name] || [`${f.label}: no`, `${f.label}: yes`])[Number(v)]);
  if (name === "age") return `Your age <small>${v} years</small>`;
  if (name === "gender") return `Gender <small>${esc(fmtVal(f, v))}</small>`;
  if (f.normal) {
    const st = bioState(f, v);
    return `${esc(f.label)} is ${st === "low" ? "<b>low</b>" : st === "high" ? "<b>high</b>" : "healthy"}<small>${fmtNum(v)} ${esc(f.unit)} · healthy ${f.normal[0]}–${f.normal[1]}</small>`;
  }
  return `${esc(f.label)}<small>${fmtNum(v)} on a ${f.min}–${f.max} scale</small>`;
}

function patientView(p) {
  const R = p.results, cons = R._consensus, c = cons.pred, pr = cons.proba, A = ANSWER[c], score = riskScore(pr);
  const sure = `${icon(cons.agree ? "check" : "info")}We are <b>&nbsp;${sureWord(pr[c])}&nbsp;</b>(${pct(pr[c])})${cons.n > 1 ? (cons.agree ? " — all three models agree" : " — the models did not fully agree") : ""}`;
  let h = `<div class="stack-lg">
    <div class="hero risk${c}">
      <div><div class="eyebrow">Will I have hair fall?</div><div class="answer">${A.a}</div><div class="lead">${A.lead}</div><div class="sub">${A.sub}</div><div class="sure">${sure}</div></div>
      <div>${gauge(score)}<div class="gauge-legend"><span>Low</span><span>Risk score out of 100</span><span>High</span></div></div>
    </div>
    <div class="chances">${pr.map((x, i) => `<div class="chance risk${i} ${i === c ? "me" : ""}"><div class="cl"><i></i>${RISK[i]} risk</div>
      <div class="cv">${pct(x)}</div><div class="bar"><span style="width:${x * 100}%"></span></div></div>`).join("")}</div>`;

  const sh = R.catboost && R.catboost.shap;
  if (sh && sh.risk) {
    const top = sh.risk.filter((r) => Math.abs(r.value) > 0.02).slice(0, 8);
    const mx = Math.max(...top.map((r) => Math.abs(r.value))) || 1;
    const strength = (v) => (Math.abs(v) / mx > 0.66 ? "strong" : Math.abs(v) / mx > 0.33 ? "moderate" : "slight");
    h += `<section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("sparkle")}</span>
        <div><h2>Why this result?</h2><p>The factors that moved your risk the most, from strongest to weakest.</p></div><span class="spacer"></span>
        <div class="why-legend"><span><i style="background:var(--good)"></i>Lowers your risk</span><span><i style="background:var(--crit)"></i>Raises your risk</span></div></div>
      <div class="why-axis"><span></span><span class="l">← lowers</span><span class="r">raises →</span></div>
      <div class="why">${top.map((r) => {
        const w = (Math.abs(r.value) / mx) * 92, tipTxt = `${strength(r.value)} effect — ${r.value > 0 ? "raises" : "lowers"} your risk`;
        return `<div class="why-row"><span class="wt">${factorText(r.feature, p.inputs[r.feature])}</span>
          <span class="side l">${r.value < 0 ? `<span style="width:${w}%" data-tip="${esc(tipTxt)}"></span>` : ""}</span>
          <span class="side r">${r.value > 0 ? `<span style="width:${w}%" data-tip="${esc(tipTxt)}"></span>` : ""}</span></div>`;
      }).join("")}</div></section>`;
    const tips = [], seen = new Set();
    sh.risk.filter((r) => r.value > 0.02).forEach((r) => { const t = TIPS[r.feature]; if (t && !seen.has(t[1])) { seen.add(t[1]); tips.push(t); } });
    h += `<div class="grid-2">
      <section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("flask")}</span><div><h2>Your blood tests</h2><p>Where each result sits compared with the healthy range.</p></div></div>${bloodRows(p.inputs)}</section>
      <section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("bulb")}</span><div><h2>What you can do</h2><p>Based on the factors that raise your risk.</p></div></div>
        ${tips.length ? `<ul class="tips">${tips.slice(0, 5).map(([ic, t, s]) => `<li>${icon(ic)}<div><b>${esc(t)}</b><span>${esc(s)}</span></div></li>`).join("")}</ul>`
          : `<p class="muted">Nothing you can change stands out as a risk — keep up your current routine.</p>`}</section></div>`;
  } else {
    h += `<section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("flask")}</span><div><h2>Your blood tests</h2></div></div>${bloodRows(p.inputs)}</section>`;
  }
  h += `<div class="disclaimer">${icon("info")}<span>This is an estimate from research models trained on ${P.schema.context_rows.toLocaleString()} people — it is not a medical diagnosis. If you are worried about hair fall, talk to a doctor or dermatologist.</span></div></div>`;
  return h;
}

function bloodRows(inputs) {
  return P.fields.filter((f) => f.normal).map((f) => {
    const v = inputs[f.name], span = f.max - f.min, st = bioState(f, v);
    return `<div class="blood-row"><span class="bn">${esc(f.label)}</span>
      <div class="rtrack" data-tip="${esc(f.label)}: <b>${fmtNum(v)} ${esc(f.unit)}</b><br>healthy ${f.normal[0]}–${f.normal[1]}"><span class="nz" style="left:${((f.normal[0] - f.min) / span) * 100}%;width:${((Math.min(f.normal[1], f.max) - f.normal[0]) / span) * 100}%"></span>
        <span class="mk ${st}" style="left:${((v - f.min) / span) * 100}%"></span></div>
      <span class="bv">${fmtNum(v)} <small>${esc(f.unit)}</small></span><span class="tag ${st}">${st === "ok" ? "HEALTHY" : st.toUpperCase()}</span></div>`;
  }).join("");
}

function devView(p) {
  const R = p.results || {}, cons = R._consensus, keys = ["catboost", "tabpfn", "tabfm"].filter((k) => k in p.models);
  const ok = keys.filter((k) => R[k] && R[k].status === "ok");
  let h = `<div class="stack-lg"><div class="mcards">${keys.map((k) => {
    const r = R[k] || { status: "queued", size: p.models[k] };
    const head = `<div class="mh"><span class="model-dot"></span><b>${MODEL_LABEL[k]}</b><span class="spacer"></span>${r.status === "ok" ? `<span class="pill risk risk${r.pred}"><i></i>${RISK[r.pred]}</span>` : `<span class="pill ${r.status}">${esc(r.status)}</span>`}</div>
      <div class="ms">${k === "catboost" ? "Trained model · Full training set" : `Foundation model · ${r.size} context rows`}${r.seconds != null ? ` · ${fmtTime(r.seconds)}` : ""}</div>`;
    if (r.status !== "ok") return `<div class="card mcard m-${k}">${head}<p class="muted" style="margin:10px 0 0">${esc(r.error || "")}</p></div>`;
    return `<div class="card mcard m-${k}">${head}
      <div class="pbar">${r.proba.map((x, i) => `<span style="width:${x * 100}%;background:var(--${["good", "warn", "crit"][i]})" data-tip="${RISK[i]} ${pct(x, 1)}"></span>`).join("")}</div>
      <div class="plist">${r.proba.map((x, i) => `<div><span>P(${RISK[i]})</span><b>${x.toFixed(4)}</b></div>`).join("")}</div></div>`;
  }).join("")}</div>`;
  if (cons) {
    h += `<section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("code")}</span><div><h2>How the answer is calculated</h2><p>Soft-voting ensemble: the class probabilities of the models are averaged.</p></div></div>
      <div class="calc">${RISK.map((c, i) => `P̄(${c}) = (${ok.map((k) => R[k].proba[i].toFixed(4)).join(" + ")}) / ${ok.length} = <b>${cons.proba[i].toFixed(4)}</b>`).join("<br>")}<br>
      Prediction = argmax P̄ = <b>${RISK[cons.pred]}</b> · models agree: <b>${cons.agree ? "yes" : "no"}</b><br>
      Risk score = 50 × P̄(Moderate) + 100 × P̄(High) = 50 × ${cons.proba[1].toFixed(4)} + 100 × ${cons.proba[2].toFixed(4)} = <b>${riskScore(cons.proba)}</b><br>
      Confidence = P̄(${RISK[cons.pred]}) = ${pct(cons.proba[cons.pred], 1)} → “${sureWord(cons.proba[cons.pred])}”</div></section>`;
  }
  const sh = R.catboost && R.catboost.shap;
  if (sh && sh.all) {
    const rows = sh.features.map((f, i) => ({ f, i, risk: sh.all.High[i] - sh.all.Low[i] })).sort((a, b) => Math.abs(b.risk) - Math.abs(a.risk));
    h += `<section class="card card-pad"><div class="card-head"><span class="card-icon">${icon("sparkle")}</span><div><h2>CatBoost SHAP values</h2>
        <p>Exact TreeSHAP in log-odds per class. “Why this result” uses High − Low (&gt; 0 raises risk), shown when |value| &gt; 0.02.</p></div></div>
      <div class="table-wrap"><table class="t compact"><thead><tr><th class="l">Feature</th><th>Value</th><th>Low</th><th>Moderate</th><th>High</th><th>High − Low</th></tr></thead><tbody>
      ${rows.map(({ f, i, risk }) => `<tr><td class="l">${esc(P.byName[f]?.label || f)}</td><td>${esc(fmtVal(P.byName[f] || {}, p.inputs[f]))}</td>
        ${RISK.map((c) => `<td>${sh.all[c][i].toFixed(3)}</td>`).join("")}<td class="${risk > 0.02 ? "up" : risk < -0.02 ? "down" : ""}">${risk > 0 ? "+" : ""}${risk.toFixed(3)}</td></tr>`).join("")}
      </tbody></table></div></section>`;
  }
  h += `<div class="disclaimer">${icon("db")}<span>Saved as row <code>${p.id}</code> in the Postgres table <code>predictions</code>${p.minio_key ? ` and as <a href="/api/files/${p.minio_key}?download=true">${esc(p.minio_key)}</a> in MinIO` : ""}. Total time ${fmtTime(p.seconds)}.</span></div></div>`;
  return h;
}

/* ======================= history ======================= */
async function loadHistory() {
  try { P.history = await api(`/api/predictions${P.q ? "?q=" + encodeURIComponent(P.q) : ""}`); } catch { P.history = []; }
  if (!P.q) $("#pCount").textContent = P.history.length;
  if (P.mode === "history") paintHistory();
}
function topReason(h) {
  const r = h.results?.catboost?.shap?.risk?.find((x) => x.value > 0.02);
  if (!r) return "";
  const f = P.byName[r.feature], v = h.inputs[r.feature];
  if (!f) return "";
  return f.kind === "bool" ? (BOOL_TEXT[r.feature] || [])[Number(v)] || f.label : `${f.label} ${fmtNum(v)} ${f.unit}`.trim();
}
function paintHistory() {
  const box = $("#pHistory");
  if (!box.firstChild) {
    box.innerHTML = `<div class="card"><div class="hist-toolbar"><div class="search">${icon("search")}<input class="input" id="pSearch" type="search" placeholder="Search by name or #number"></div>
      <span class="spacer"></span><span class="muted" id="pHistInfo"></span></div>
      <div class="hcols hist-head"><span></span><span>Person</span><span>Result</span><span>Risk score</span><span>Main reason</span><span></span></div><div id="pHistList"></div></div>`;
    let t;
    $("#pSearch").oninput = (e) => { clearTimeout(t); t = setTimeout(() => { P.q = e.target.value.trim(); loadHistory(); }, 250); };
  }
  $("#pHistInfo").textContent = `${P.history.length} check${P.history.length === 1 ? "" : "s"}`;
  const list = $("#pHistList");
  if (!P.history.length) {
    list.innerHTML = `<div class="empty">${icon("history")}<h3>${P.q ? "No matches" : "No checks yet"}</h3><p>${P.q ? "Try another name." : "Every risk check you run is saved here."}</p></div>`;
    return;
  }
  list.innerHTML = P.history.map((h) => {
    const cons = h.results?._consensus, c = cons ? cons.pred : null, d = new Date(h.created_at);
    const running = ["queued", "running"].includes(h.status);
    return `<div class="hcols hrow ${c != null ? "risk" + c : ""}" data-id="${h.id}">
      <span class="av">${esc(initials(h.label || "#"))}</span>
      <span class="nm"><b>${esc(h.label || "Unnamed check")}</b><span>#${h.id} · ${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span></span>
      <span>${running ? `<span class="pill running"><i></i>Running</span>` : c != null ? `<span class="pill risk"><i></i>${RISK[c]} risk</span>` : `<span class="pill error">Failed</span>`}</span>
      <span class="sc">${cons ? `<b>${riskScore(cons.proba)}</b> <span>/ 100</span>` : "–"}</span>
      <span class="rs">${esc(topReason(h))}</span>
      <button class="btn ghost warn sm icon del" title="Delete this check">${icon("trash")}</button></div>`;
  }).join("");
  $$(".hrow", list).forEach((row) => {
    row.onclick = (e) => { if (!e.target.closest(".del")) go("predict", row.dataset.id); };
    $(".del", row).onclick = async () => {
      if (!confirm(`Delete check #${row.dataset.id}? This removes it from Postgres and MinIO.`)) return;
      await api(`/api/predictions/${row.dataset.id}`, { method: "DELETE" });
      if (P.current && String(P.current.id) === row.dataset.id) P.current = null;
      loadHistory();
    };
  });
}

/* ======================= view ======================= */
let pReady = null;
async function pInit() {
  pShell();
  P.schema = await api("/api/predict/schema");
  P.fields = P.schema.fields;
  P.byName = Object.fromEntries(P.fields.map((f) => [f.name, f]));
  buildForm(); resetValues(); paintAll(); loadHistory();
}
Views.predict = {
  lastSub: () => (P.mode === "result" && P.current ? String(P.current.id) : P.mode === "history" ? "history" : null),
  async show(sub) {
    if (!pReady) pReady = pInit().catch((e) => { $("#pWrap").innerHTML = `<div class="card empty">${icon("info")}<h3>Server offline</h3><p>${esc(e.message)}</p></div>`; pReady = null; throw e; });
    await pReady;
    if (sub === "history") { setMode("history"); paintHistory(); loadHistory(); }
    else if (sub && /^\d+$/.test(sub)) { setMode("result"); if (!P.current || String(P.current.id) !== sub) $("#pResult").innerHTML = `<div class="card waiting"><span class="spin"></span></div>`; openResult(sub); }
    else setMode("new");
  },
};
document.addEventListener("keydown", (e) => {
  if (currentTab === "predict" && P.mode === "new" && e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit(); }
});
