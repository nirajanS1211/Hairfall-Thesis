/* Results: every model x training size - metrics, scaling, significance, confusion matrices, SHAP, tuning, data. */
const MODEL_ORDER = ["CatBoost", "TabPFN", "TabFM"];
const MODEL_COLOR = { CatBoost: "var(--m-catboost)", TabPFN: "var(--m-tabpfn)", TabFM: "var(--m-tabfm)" };
const byModelSize = (a, b) => MODEL_ORDER.indexOf(a.d.model) - MODEL_ORDER.indexOf(b.d.model) || SIZES.indexOf(a.d.size) - SIZES.indexOf(b.d.size);
const C = { built: false, sig: "" };
const mdot = (m) => `<span class="model-dot m-${modelKey(m)}"></span>`;

async function cLoad() {
  await Lab.loadSteps();
  const ok = Lab.steps.filter((s) => s.last_run?.status === "ok");
  const got = await Promise.all(ok.map(async (s) => ({ s, d: await Lab.summary(s.last_run) })));
  const met = got.filter((x) => x.d?._kind === "metrics").sort(byModelSize);
  const shap = got.filter((x) => x.d?._kind === "shap").sort(byModelSize);
  const ds = await api("/api/dataset/stats").catch(() => null);
  return { met, shap, ds };
}

function cSection(id, title, sub, body, extra = "") {
  return `<section class="sec" id="c-${id}"><div class="sec-title"><div><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ""}</div><span class="spacer"></span>${extra}</div>${body}</section>`;
}

async function renderCompare() {
  const wrap = $("#cWrap");
  if (!C.built) wrap.innerHTML = `<div class="card waiting"><span class="spin"></span><p class="muted">Loading results…</p></div>`;
  const { met, shap, ds } = await cLoad();
  C.met = met;
  if (!met.length) {
    wrap.innerHTML = `<div class="card empty">${icon("chart")}<h3>No results yet</h3><p>Run the model steps (5–7) in the Notebook, or import the Kaggle runs.</p></div>`;
    return;
  }
  const cell = (m, sz) => met.find((x) => x.d.model === m && x.d.size === sz)?.d;
  const best = met.reduce((a, b) => (b.d.macro_f1 > a.d.macro_f1 ? b : a)).d;
  const small = ["TabPFN", "TabFM"].map((m) => cell(m, "500")).filter(Boolean).sort((a, b) => b.macro_f1 - a.macro_f1)[0];
  const cb500 = cell("CatBoost", "500");

  const nav = [["overview", "Overview"], ["performance", "Performance"], ["scaling", "Scaling"], ["significance", "Significance"],
    ["confusion", "Confusion matrices"], ["shap", "Explainability"], ["tuning", "CatBoost tuning"], ["data", "Data quality"]];
  let h = `<div class="page-head"><div><h1>Results</h1><p>CatBoost vs the TabPFN and TabFM foundation models, each trained on 500, 2,000 and all 17,284 rows, tested on the same ${best.test_rows.toLocaleString()} held-out patients.</p></div></div>
    <nav class="subnav" id="cNav">${nav.map(([id, t]) => `<a href="#compare" data-s="${id}">${t}</a>`).join("")}</nav>`;

  // overview
  h += `<section class="sec" id="c-overview"><div class="stats-row">
    <div class="card stat"><div class="k">${icon("sparkle")}Best model</div><div class="v">${pct(best.macro_f1, 1)}</div><div class="s">${mdot(best.model)}<b style="color:var(--ink)">${best.model} · ${best.size}</b> macro F1</div></div>
    <div class="card stat"><div class="k">${icon("chart")}Small-data advantage</div><div class="v">+${((small.macro_f1 - cb500.macro_f1) * 100).toFixed(1)} pts</div><div class="s">${small.model} vs CatBoost with only 500 rows</div></div>
    <div class="card stat"><div class="k">${icon("gauge")}Best ROC-AUC</div><div class="v">${Math.max(...met.map((x) => x.d.roc_auc_ovr)).toFixed(3)}</div><div class="s">one-vs-rest, macro average</div></div>
    <div class="card stat"><div class="k">${icon("db")}Dataset</div><div class="v">${ds ? ds.rows.toLocaleString() : "–"}</div><div class="s">patients · 3 risk classes · ${ds ? ds.columns - 3 : 20} features</div></div>
  </div></section>`;

  // performance table
  const cols = [["accuracy", "Accuracy"], ["macro_f1", "Macro F1"], ["weighted_f1", "Weighted F1"], ["roc_auc_ovr", "ROC-AUC"]];
  const top = Object.fromEntries(cols.map(([k]) => [k, Math.max(...met.map((x) => x.d[k]))]));
  let prev = null;
  h += cSection("performance", "Performance", "All nine runs on the same test set. ★ marks the best value in each column.",
    `<div class="card table-wrap" style="border-radius:var(--r-lg)"><table class="t"><thead><tr><th class="l">Model</th><th class="l">Training size</th><th>Rows</th>${cols.map((c) => `<th>${c[1]}</th>`).join("")}<th>Fit</th><th>Predict</th><th class="l">Notebook</th></tr></thead><tbody>
    ${met.map(({ s, d }) => { const sep = prev && prev !== d.model ? "group-start" : ""; prev = d.model;
      return `<tr class="${sep}"><td class="l">${mdot(d.model)}<b>${d.model}</b></td><td class="l">${d.size}</td><td>${(d.context_rows ?? 0).toLocaleString()}</td>
        ${cols.map(([k]) => `<td class="${d[k] === top[k] ? "best" : ""}">${d[k].toFixed(4)}</td>`).join("")}
        <td>${fmtTime(d.fit_seconds)}</td><td>${fmtTime(d.predict_seconds)}</td><td class="l"><a href="#notebook/${s.id}">Step ${s.label} →</a></td></tr>`; }).join("")}
    </tbody></table></div>`,
    `<button class="btn sm" id="cCopy">${icon("download")}Copy as CSV</button>`);

  // scaling
  const series = (fn) => MODEL_ORDER.filter((m) => met.some((x) => x.d.model === m)).map((m) => ({ name: m, color: MODEL_COLOR[m], values: SIZES.map((z) => { const d = cell(m, z); return d ? fn(d) : null; }) }));
  const legend = `<div class="legend">${MODEL_ORDER.map((m) => `<span><i style="background:${MODEL_COLOR[m]}"></i>${m}</span>`).join("")}</div>`;
  h += cSection("scaling", "How performance scales with training data", "Foundation models reach high accuracy with very little data; CatBoost needs the full training set to catch up.",
    `<div class="grid-2">
      <div class="card chart-card"><h3>Macro F1</h3><div class="sub">Higher is better · the main thesis metric</div>${lineChart({ series: series((d) => d.macro_f1) })}</div>
      <div class="card chart-card"><h3>ROC-AUC</h3><div class="sub">Higher is better · one-vs-rest, macro average</div>${lineChart({ series: series((d) => d.roc_auc_ovr) })}</div>
      <div class="card chart-card"><h3>Accuracy</h3><div class="sub">Share of the ${best.test_rows.toLocaleString()} test patients classified correctly</div>${lineChart({ series: series((d) => d.accuracy) })}</div>
      <div class="card chart-card"><h3>Time to train + predict</h3><div class="sub">Log scale · Kaggle Tesla T4 GPU · lower is better</div>${lineChart({ series: series((d) => d.fit_seconds + d.predict_seconds), log: true })}</div>
    </div>`, legend);

  h += cSection("significance", "Is the difference real?", "McNemar’s test on the same test patients — a result is significant when p &lt; 0.05.", `<div id="cMcnemar"><div class="card waiting"><span class="spin"></span></div></div>`);
  h += cSection("confusion", "Confusion matrices", "Rows are the true risk class, columns the predicted class. The percentage is the share of that true class (recall).", `<div id="cCM"><div class="card waiting"><span class="spin"></span></div></div>`);
  h += cSection("shap", "Explainability (SHAP)", "Which features each model relies on. Darker = more important within that run.", `<div id="cShap"><div class="card waiting"><span class="spin"></span></div></div>`);
  h += cSection("tuning", "CatBoost hyper-parameter search", "5-fold cross-validated macro F1 for every depth × learning-rate pair. The best combination was used for the final model.", `<div id="cTune"></div>`);
  h += cSection("data", "Data quality", "Biomarkers compared against clinical reference ranges in Step 3. Abnormal values were kept — they carry the signal.", `<div id="cData"></div>`);
  wrap.innerHTML = h;
  C.built = true;

  $("#cCopy").onclick = () => {
    const head = ["model", "size", "rows", "accuracy", "macro_f1", "weighted_f1", "roc_auc_ovr", "fit_seconds", "predict_seconds"];
    const csv = [head.join(","), ...met.map(({ d }) => [d.model, d.size, d.context_rows, d.accuracy, d.macro_f1, d.weighted_f1, d.roc_auc_ovr, d.fit_seconds, d.predict_seconds].join(","))].join("\n");
    navigator.clipboard.writeText(csv).then(() => { $("#cCopy").innerHTML = icon("check") + "Copied"; setTimeout(() => ($("#cCopy").innerHTML = icon("download") + "Copy as CSV"), 1600); });
  };
  $$("#cNav a").forEach((a) => a.onclick = (e) => { e.preventDefault(); $("#c-" + a.dataset.s).scrollIntoView({ behavior: "smooth" }); });
  wireSubnav();
  cMcnemar(); cConfusion(met); cShap(shap); cTuning(met); cData(ds);
}

function wireSubnav() {
  const page = $("#cPage");
  page.onscroll = () => {
    let on = "overview";
    $$("section.sec", page).forEach((s) => { if (s.getBoundingClientRect().top < 140) on = s.id.slice(2); });
    $$("#cNav a").forEach((a) => a.classList.toggle("on", a.dataset.s === on));
  };
  page.onscroll();
}

async function cMcnemar() {
  const f = Lab.file("Step_09", "mcnemar_results.csv"), box = $("#cMcnemar");
  if (!f) { box.innerHTML = `<div class="card empty"><p>Run Step 9 to compute McNemar’s tests.</p></div>`; return; }
  const { head, rows } = parseCSV(await fileText(f.key));
  const R = rows.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
  const n = (v) => (v === "" || v == null ? NaN : Number(v));
  box.innerHTML = `<div class="card table-wrap" style="border-radius:var(--r-lg)"><table class="t"><thead><tr><th class="l">Training size</th><th class="l">Comparison</th><th>Only first right</th><th>Only second right</th><th>χ²</th><th>p-value</th><th class="l">Verdict</th></tr></thead><tbody>
    ${R.map((r, i) => {
      const [A, B] = r.comparison.split(" vs "), a = n(r[`only_${A}_correct`]), b = n(r.only_other_correct), p = n(r.p_value);
      const sig = String(r["significant_0.05"]).toLowerCase() === "true", win = a > b ? A : B;
      return `<tr class="${i && R[i - 1].size !== r.size ? "group-start" : ""}"><td class="l"><b>${esc(r.size)}</b></td><td class="l">${mdot(A)}${esc(A)} <span class="muted">vs</span> ${mdot(B)}${esc(B)}</td>
        <td>${a}</td><td>${b}</td><td>${n(r.chi2).toFixed(2)}</td><td>${p < 0.001 ? "&lt; 0.001" : p.toFixed(3)}</td>
        <td class="l verdict ${sig ? "yes" : "no"}">${sig ? `${icon("check")} ${esc(win)} is significantly better` : "No significant difference"}</td></tr>`;
    }).join("")}</tbody></table></div>`;
}

async function cConfusion(met) {
  const box = $("#cCM");
  const mats = await Promise.all(met.map(async ({ s, d }) => {
    const f = (s.last_run.files || []).find((x) => x.name === "predictions.csv");
    if (!f) return null;
    const { head, rows } = parseCSV(await fileText(f.key));
    const it = head.indexOf("y_true"), ip = head.indexOf("y_pred"), m = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
    rows.forEach((r) => { m[+r[it]][+r[ip]]++; });
    return { d, m };
  }));
  const get = (model, size) => mats.find((x) => x && x.d.model === model && x.d.size === size);
  const models = MODEL_ORDER.filter((m) => met.some((x) => x.d.model === m));
  const cmHtml = (x) => {
    if (!x) return `<div class="card cm empty" style="padding:30px">–</div>`;
    const total = x.m.flat().reduce((a, b) => a + b, 0), correct = x.m[0][0] + x.m[1][1] + x.m[2][2];
    return `<div class="card cm"><div class="cm-top"><span>Accuracy <b>${pct(correct / total, 1)}</b></span><span>Macro F1 <b>${x.d.macro_f1.toFixed(3)}</b></span></div>
      <table><tr><th></th>${RISK.map((c) => `<th>${c}</th>`).join("")}</tr>
      ${x.m.map((row, i) => { const n = row.reduce((a, b) => a + b, 0);
        return `<tr><th class="rl">${RISK[i]}</th>${row.map((v, j) => { const t = v / n, f = seqFill(t);
          return `<td style="background:${f.bg};color:${f.fg}" data-tip="True <b>${RISK[i]}</b> → predicted <b>${RISK[j]}</b><br>${v.toLocaleString()} patients (${pct(t, 1)} of true ${RISK[i]})">${v.toLocaleString()}<small>${pct(t)}</small></td>`; }).join("")}</tr>`; }).join("")}
      </table><div class="axis-l">predicted →</div></div>`;
  };
  box.innerHTML = `<div class="cm-grid"><span></span>${SIZES.map((z) => `<div class="ch">${z === "Full" ? "Full (17,284 rows)" : z + " rows"}</div>`).join("")}
    ${models.map((m) => `<div class="rh">${mdot(m)}${m}</div>${SIZES.map((z) => cmHtml(get(m, z))).join("")}`).join("")}</div>`;
}

async function cShap(shap) {
  const box = $("#cShap");
  if (!shap.length) { box.innerHTML = `<div class="card empty"><p>Run the SHAP steps (8a–8i) to see explanations.</p></div>`; return; }
  const imps = await Promise.all(shap.map(async ({ s, d }) => {
    const f = (s.last_run.files || []).find((x) => x.name === "shap_importance.csv");
    if (!f) return null;
    const { head, rows } = parseCSV(await fileText(f.key));
    const iF = head.indexOf("feature"), iV = head.indexOf("mean_abs_all");
    return { s, d, imp: Object.fromEntries(rows.map((r) => [r[iF], +r[iV]])) };
  }));
  const ok = imps.filter(Boolean);
  const feats = Object.keys(ok[0].imp).sort((a, b) => ok.reduce((t, x) => t + x.imp[b] / Math.max(...Object.values(x.imp)), 0) - ok.reduce((t, x) => t + x.imp[a] / Math.max(...Object.values(x.imp)), 0));
  const heat = `<div class="card table-wrap" style="border-radius:var(--r-lg)"><table class="t compact"><thead><tr><th class="l">Feature</th>
    ${ok.map((x) => `<th class="c">${mdot(x.d.model)}${x.d.model}<br><span style="text-transform:none;font-weight:500">${x.d.size}</span></th>`).join("")}</tr></thead><tbody>
    ${feats.map((f) => `<tr><td class="l"><b>${esc(f)}</b></td>${ok.map((x) => {
      const mx = Math.max(...Object.values(x.imp)), t = x.imp[f] / mx, rank = Object.values(x.imp).filter((v) => v > x.imp[f]).length + 1, c = seqFill(t);
      return `<td class="c" style="background:${c.bg};color:${c.fg};font-weight:600" data-tip="<b>${esc(f)}</b> · ${x.d.model} ${x.d.size}<br>rank ${rank} · mean |SHAP| ${x.imp[f].toFixed(4)}">${rank}</td>`;
    }).join("")}</tr>`).join("")}</tbody></table></div>`;
  const note = `<div class="note" style="margin:16px 0">${icon("info")}<span>Numbers are the importance rank within each run (1 = most important). CatBoost explanations use exact TreeSHAP on 1,000 rows; TabPFN and TabFM use KernelSHAP on 30 and 20 rows because it is far slower.</span></div>`;
  const imgs = (name) => `<div class="img-grid">${shap.map(({ s, d }) => { const f = (s.last_run.files || []).find((x) => x.name === name);
    return f ? `<div class="card img-card"><img class="zoom" src="/api/files/${f.key}" loading="lazy" alt="${esc(d.model)} ${esc(d.size)} — ${esc(name)}"><div class="cap">${mdot(d.model)}<b>${d.model}</b>&nbsp;${d.size}<span>${fmtTime(d.seconds)}</span></div></div>` : ""; }).join("")}</div>`;
  box.innerHTML = heat + note + `<div style="display:flex;align-items:center;gap:12px;margin:24px 0 14px"><h3 style="font-size:16px">SHAP figures</h3><span class="spacer" style="flex:1"></span>
    <div class="seg" id="cShapSeg"><button data-f="shap_global_importance.png" class="on">Global importance</button><button data-f="shap_beeswarm_high.png">Beeswarm · High risk</button></div></div><div id="cShapImgs">${imgs("shap_global_importance.png")}</div>`;
  $$("#cShapSeg button").forEach((b) => b.onclick = () => { $$("#cShapSeg button").forEach((x) => x.classList.toggle("on", x === b)); $("#cShapImgs").innerHTML = imgs(b.dataset.f); });
}

async function cTuning(met) {
  const box = $("#cTune");
  const cb = met.filter((x) => x.d.model === "CatBoost");
  const parts = await Promise.all(cb.map(async ({ s, d }) => {
    const f = (s.last_run.files || []).find((x) => x.name === "grid_search.csv");
    if (!f) return "";
    const { head, rows } = parseCSV(await fileText(f.key));
    const ix = (k) => head.indexOf(k);
    const bestF1 = Math.max(...rows.map((r) => +r[ix("cv_macro_f1")]));
    return `<div class="card chart-card"><h3>${mdot("CatBoost")}CatBoost · ${d.size}</h3><div class="sub">Chosen: depth ${d.depth}, learning rate ${d.learning_rate}, ${d.iterations} trees</div>
      <table class="t compact"><thead><tr><th>Depth</th><th>Learning rate</th><th>CV macro F1</th><th>± std</th><th>Trees</th></tr></thead><tbody>
      ${rows.map((r) => `<tr><td>${r[ix("depth")]}</td><td>${r[ix("learning_rate")]}</td><td class="${+r[ix("cv_macro_f1")] === bestF1 ? "best" : ""}">${(+r[ix("cv_macro_f1")]).toFixed(4)}</td><td>${(+r[ix("cv_std")]).toFixed(4)}</td><td>${r[ix("iterations")]}</td></tr>`).join("")}
      </tbody></table></div>`;
  }));
  box.innerHTML = parts.filter(Boolean).length ? `<div class="grid-3">${parts.join("")}</div>` : `<div class="card empty"><p>No grid-search results found.</p></div>`;
}

async function cData(ds) {
  const box = $("#cData"), f = Lab.file("Step_03", "range_report.csv"), img = Lab.file("Step_03", "range_check.png");
  let table = `<div class="card empty"><p>Run Step 3 to see the range check.</p></div>`;
  if (f) {
    const { head, rows } = parseCSV(await fileText(f.key));
    const ix = (k) => head.indexOf(k), mx = Math.max(...rows.map((r) => +r[ix("pct_abnormal")]));
    table = `<div class="card table-wrap" style="border-radius:var(--r-lg)"><table class="t"><thead><tr><th class="l">Biomarker</th><th>Healthy range</th><th>Below</th><th>Above</th><th>Impossible</th><th class="l">Outside the healthy range</th></tr></thead><tbody>
      ${rows.map((r) => `<tr><td class="l"><b>${esc(r[ix("feature")])}</b></td><td>${esc(r[ix("normal_range")])}</td><td>${(+r[ix("below_normal")]).toLocaleString()}</td><td>${(+r[ix("above_normal")]).toLocaleString()}</td><td>${r[ix("impossible")]}</td>
        <td class="l"><div style="display:flex;align-items:center;gap:10px"><div class="bar" style="width:140px"><span style="width:${(+r[ix("pct_abnormal")] / mx) * 100}%;background:var(--warn)"></span></div>${r[ix("pct_abnormal")]}%</div></td></tr>`).join("")}
      </tbody></table></div>`;
  }
  let dist = "";
  if (ds) {
    const t = ds.target, n = ds.rows, cls = ["good", "warn", "crit"];
    dist = `<div class="card card-pad"><div class="card-head"><div><h2>Risk classes in the dataset</h2><p>The test set keeps the same proportions (stratified split).</p></div></div>
      <div class="dist">${[0, 1, 2].map((k) => `<span style="width:${(t[k] / n) * 100}%;background:var(--${cls[k]})" data-tip="${RISK[k]}: ${t[k].toLocaleString()} patients">${pct(t[k] / n)}</span>`).join("")}</div>
      <div class="dist-legend">${[0, 1, 2].map((k) => `<span><i style="background:var(--${cls[k]})"></i>${RISK[k]} <b>${t[k].toLocaleString()}</b></span>`).join("")}</div></div>`;
  }
  box.innerHTML = `<div class="grid-2" style="align-items:start">${table}<div class="stack-lg">${dist}${img ? `<div class="card img-card"><img class="zoom" src="/api/files/${img.key}" alt="Biomarkers outside reference ranges"><div class="cap"><b>Step 3</b> range check</div></div>` : ""}</div></div>`;
}

Views.compare = {
  show() {
    const sig = JSON.stringify(Lab.steps.map((s) => s.last_run && [s.last_run.id, s.last_run.status]));
    if (!C.built || sig !== C.sig || !Lab.steps.length) renderCompare().then(() => { C.sig = JSON.stringify(Lab.steps.map((s) => s.last_run && [s.last_run.id, s.last_run.status])); }).catch((e) => {
      $("#cWrap").innerHTML = `<div class="card empty">${icon("info")}<h3>Could not load results</h3><p>${esc(e.message)}</p></div>`;
    });
  },
};
