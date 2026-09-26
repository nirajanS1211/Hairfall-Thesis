/* Notebook: the thesis pipeline steps, each with editable code, run history and outputs. */
const NB = {
  selected: store.get("step"), viewRun: null, drafts: {}, loadedKey: "", outKey: "", histKey: "", sideKey: "",
  status: { running: null, queued: 0, kernel: false }, outTab: "output",
  shut: JSON.parse(store.get("nbShut", "{}")), codeHidden: store.get("nbCodeHidden") === "1",
};
const curStep = () => Lab.steps.find((s) => s.id === NB.selected);
const isBusy = (r) => !!r && (r.status === "running" || r.status === "queued");
const STATUS_TEXT = { ok: "Completed", error: "Failed", running: "Running", queued: "Queued", cancelled: "Cancelled", interrupted: "Interrupted", skipped: "Skipped" };

/* ---------------- Python syntax highlighting ---------------- */
const PY_KW = new Set("False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield".split(" "));
const PY_BI = new Set("print len range enumerate zip list dict set tuple int float str bool open sorted min max sum abs round isinstance type super map filter any all display".split(" "));
const PY_RE = /(#[^\n]*)|([rbfRBF]{0,2}(?:"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(@[\w.]+)|(\b\d[\d_]*\.?\d*(?:e[+-]?\d+)?\b)|(\b[A-Za-z_]\w*\b)/g;
function highlight(code) {
  let out = "", last = 0, prev = "";
  code.replace(PY_RE, (m, com, str, dec, numb, word, i) => {
    out += esc(code.slice(last, i)); last = i + m.length;
    if (com) out += `<span class="tk-c">${esc(m)}</span>`;
    else if (str) out += `<span class="tk-s">${esc(m)}</span>`;
    else if (dec) out += `<span class="tk-d">${esc(m)}</span>`;
    else if (numb) out += `<span class="tk-n">${esc(m)}</span>`;
    else if (PY_KW.has(m)) out += `<span class="tk-k">${m}</span>`;
    else if (prev === "def" || prev === "class") out += `<span class="tk-f">${m}</span>`;
    else if (PY_BI.has(m)) out += `<span class="tk-b">${m}</span>`;
    else out += m;
    if (word) prev = m;
    return m;
  });
  return out + esc(code.slice(last)) + "\n";
}

/* ---------------- sidebar ---------------- */
function paintSide() {
  const key = JSON.stringify([Lab.steps.map((s) => [s.id, s.last_run?.status, s.last_run?.seconds]), NB.selected, NB.shut]);
  if (key === NB.sideKey) return;
  NB.sideKey = key;
  const groups = {};
  Lab.steps.forEach((s) => (groups[s.group] ||= []).push(s));
  const done = Lab.steps.filter((s) => s.last_run?.status === "ok").length;
  $("#nbDone").innerHTML = `<b>${done}</b> of ${Lab.steps.length} steps complete`;
  $("#nbTotal").textContent = Lab.steps.length ? pct(done / Lab.steps.length) : "";
  $("#nbBar").style.width = Lab.steps.length ? (done / Lab.steps.length) * 100 + "%" : 0;
  const list = $("#nbList"), top = list.scrollTop;
  list.innerHTML = Object.entries(groups).map(([g, items]) => `
    <div class="nb-group ${NB.shut[g] ? "shut" : ""}">
      <div class="nb-ghead" data-g="${esc(g)}">${icon("chev", "chev")}<span class="gname">${esc(g)}</span>
        <span class="gc">${items.filter((s) => s.last_run?.status === "ok").length}/${items.length}</span>
        <button class="gbtn" data-from="${items[0].id}" data-to="${items[items.length - 1].id}" title="Run this group in order">${icon("play")}</button></div>
      ${items.map((s) => `<div class="nb-item ${s.id === NB.selected ? "active" : ""}" data-id="${s.id}" title="${esc(s.label + " · " + s.title)}">
        <span class="sdot ${s.last_run?.status || ""}"></span><span class="lbl">${esc(s.label)}</span><span class="ttl">${esc(s.title)}</span>
        <span class="tm">${s.last_run?.seconds != null ? fmtTime(s.last_run.seconds) : ""}</span></div>`).join("")}
    </div>`).join("");
  list.scrollTop = top;
  $$(".nb-item", list).forEach((el) => el.onclick = () => go("notebook", el.dataset.id));
  $$(".nb-ghead", list).forEach((h) => h.onclick = (e) => {
    if (e.target.closest(".gbtn")) return;
    NB.shut[h.dataset.g] = !NB.shut[h.dataset.g];
    store.set("nbShut", JSON.stringify(NB.shut));
    h.parentElement.classList.toggle("shut", NB.shut[h.dataset.g]);
  });
  $$(".gbtn", list).forEach((b) => b.onclick = async () => {
    if (!confirm("Run this whole group in order?")) return;
    await api(`/api/run-all?from_step=${b.dataset.from}&to_step=${b.dataset.to}`, { method: "POST" });
    nbRefresh();
  });
}

function paintKernel() {
  const st = NB.status, running = st.running ? Lab.steps.find((s) => s.last_run?.id === st.running) : null;
  const k = $("#kernel");
  k.className = "kernel " + (st.running || st.queued ? "busy" : st.kernel ? "idle" : "");
  $("span", k).textContent = running ? `Running step ${running.label}${st.queued ? ` · ${st.queued} queued` : ""}` : st.queued ? `${st.queued} queued` : st.kernel ? "Kernel ready" : "Kernel not started";
  $("#stopAll").classList.toggle("hidden", !(st.running || st.queued));
  $("#runAll").classList.toggle("hidden", !!(st.running || st.queued));
}

/* ---------------- editor ---------------- */
const ed = $("#nbEditor");
function paintCode() {
  $("#nbHl").innerHTML = highlight(ed.value);
  $("#nbGutter").textContent = Array.from({ length: ed.value.split("\n").length }, (_, i) => i + 1).join("\n");
  syncScroll();
  const s = curStep();
  $("#nbMod").classList.toggle("hidden", !s || ed.value === s.default_code);
  $("#nbReset").disabled = !s || ed.value === s.default_code;
}
function syncScroll() { $("#nbHl").scrollTop = ed.scrollTop; $("#nbHl").scrollLeft = ed.scrollLeft; $("#nbGutter").scrollTop = ed.scrollTop; }
ed.addEventListener("scroll", syncScroll);
ed.addEventListener("input", () => { NB.drafts[NB.selected] = ed.value; paintCode(); });
ed.addEventListener("keydown", (e) => {
  if (e.key === "Tab") { e.preventDefault(); ed.setRangeText("    ", ed.selectionStart, ed.selectionEnd, "end"); NB.drafts[NB.selected] = ed.value; paintCode(); }
});
$("#nbReset").onclick = () => {
  const s = curStep();
  if (s && confirm("Replace the editor with the original step code?")) { ed.value = s.default_code; NB.drafts[s.id] = ed.value; paintCode(); }
};
function applyCodeHidden() {
  $("#nbBody").classList.toggle("code-hidden", NB.codeHidden);
  $("#nbToggleCode").title = NB.codeHidden ? "Show code" : "Hide code";
}
$("#nbToggleCode").onclick = () => { NB.codeHidden = !NB.codeHidden; store.set("nbCodeHidden", NB.codeHidden ? "1" : "0"); applyCodeHidden(); };
(() => {   // draggable divider between code and output
  const body = $("#nbBody"), dv = $("#nbDivider");
  const set = (p) => body.style.setProperty("--code-w", p + "%");
  set(parseFloat(store.get("nbCodeW")) || 44);
  dv.addEventListener("pointerdown", (e) => { dv.setPointerCapture(e.pointerId); dv.classList.add("drag"); document.body.style.userSelect = "none"; });
  dv.addEventListener("pointermove", (e) => {
    if (!dv.classList.contains("drag")) return;
    const r = body.getBoundingClientRect(), p = Math.min(70, Math.max(22, ((e.clientX - r.left) / r.width) * 100));
    set(p); dv.dataset.p = p;
  });
  dv.addEventListener("pointerup", () => { dv.classList.remove("drag"); document.body.style.userSelect = ""; if (dv.dataset.p) store.set("nbCodeW", dv.dataset.p); });
  dv.addEventListener("dblclick", () => { set(44); store.set("nbCodeW", "44"); });
})();

/* ---------------- run / stop ---------------- */
async function nbRun() {
  const s = curStep();
  if (!s) return;
  NB.drafts[s.id] = ed.value;
  await api(`/api/steps/${s.id}/run`, { method: "POST", body: JSON.stringify({ code: ed.value }) });
  NB.viewRun = null; NB.outKey = ""; NB.histKey = ""; NB.outTab = "output";
  nbRefresh();
}
const nbStop = async () => { await api("/api/stop", { method: "POST" }); nbRefresh(); };
$("#nbRun").onclick = () => (isBusy(curStep()?.last_run) ? nbStop() : nbRun());
$("#stopAll").onclick = nbStop;
$("#runAll").onclick = async () => {
  if (!confirm("Run all steps in order?\n\nThe Full-size TabPFN / TabFM steps and their SHAP steps can take many hours on a laptop. The run stops at the first error.")) return;
  await api("/api/run-all", { method: "POST" }); nbRefresh();
};
$("#restart").onclick = async () => {
  if (!confirm("Restart the Python kernel?\n\nVariables in memory are cleared. Saved results are kept.")) return;
  await api("/api/restart", { method: "POST" }); nbRefresh();
};

/* ---------------- step view ---------------- */
function paintStep() {
  const s = curStep();
  if (!s) return;
  const run = NB.viewRun || s.last_run;
  const key = s.id + "|" + (NB.viewRun ? NB.viewRun.id : "");
  if (NB.loadedKey !== key) {   // the editor is only (re)loaded when the step or picked run changes, never by polling
    NB.loadedKey = key;
    ed.value = NB.viewRun ? NB.viewRun.code : (NB.drafts[s.id] ?? s.code);
    ed.scrollTop = 0;
    paintCode();
  }
  $("#nbCrumb").textContent = `${s.group} · Step ${s.label}`;
  $("#nbTitle").textContent = s.title;
  const meta = [];
  meta.push(run ? `<span class="pill ${run.status}"><i></i>${STATUS_TEXT[run.status] || run.status}</span>` : `<span class="pill">Not run yet</span>`);
  if (run) {
    if (run.seconds != null) meta.push(`<span>${icon("history")} ${fmtTime(run.seconds)}</span>`);
    meta.push(`<span>Run #${run.id}${run.started_at && run.source !== "kaggle" ? " · " + new Date(run.started_at).toLocaleString() : ""}</span>`);
    meta.push(`<span class="pill src">${run.source === "kaggle" ? "Ran on Kaggle · Tesla T4 GPU" : "Ran on this Mac"}</span>`);
  }
  $("#nbMeta").innerHTML = meta.join('<span class="sep"></span>');
  const busy = isBusy(s.last_run), b = $("#nbRun");
  b.className = "btn " + (busy ? "danger" : "primary");
  b.innerHTML = busy ? `<span class="spin"></span>Stop` : `${icon("play")}Run step`;
  b.title = busy ? "Stop the running step" : "Run this step (⌘/Ctrl + Enter)";
  $("#nbSaved").innerHTML = s.saved ? `Saved to <code>thesis_project/${esc(s.id)}/</code>` : "";
  paintOutput(run);
  const hk = s.id + "|" + (s.last_run ? s.last_run.id + s.last_run.status : "") + "|" + (NB.viewRun ? NB.viewRun.id : "");
  if (hk !== NB.histKey) { NB.histKey = hk; loadRunHistory(s.id); }
}

async function loadRunHistory(stepId) {
  const runs = await api(`/api/steps/${stepId}/history`).catch(() => []);
  if (stepId !== NB.selected) return;
  const h = $("#nbHistory");
  h.innerHTML = `<option value="">Latest run</option>` + runs.map((r) =>
    `<option value="${r.id}" ${NB.viewRun?.id === r.id ? "selected" : ""}>Run #${r.id} · ${STATUS_TEXT[r.status] || r.status} · ${fmtTime(r.seconds)} · ${new Date(r.created_at).toLocaleDateString()}</option>`).join("");
  h.onchange = async () => {
    if (NB.loadedKey) NB.drafts[NB.selected] = ed.value;
    NB.viewRun = h.value ? await api(`/api/runs/${h.value}`) : null;
    NB.loadedKey = ""; NB.outKey = "";
    paintStep();
  };
}

/* ---------------- output ---------------- */
function cleanLog(text) {
  // dim library noise; every progress line ("predicted x/y rows | elapsed | ETA") is kept as printed
  // the metrics / SHAP summary JSON is shown as cards above the log, so fold it to one line here
  text = stripAnsi(text).replace(/^\{\n(?:[ \t]+"[^\n]*\n)+?[ \t]*"(?:accuracy|top_5)"[\s\S]*?^\}$/m, "\u0000");
  const lines = text.split("\n"), out = [];
  lines.forEach((l) => {
    if (l === "\u0000") { out.push(`<span class="dim">{ summary shown in the cards above }</span>`); return; }
    if (/^(Loading weights from|Fetching \d+ files|Download complete|WARNING: Skipping)/.test(l)) out.push(`<span class="dim">${esc(l)}</span>`);
    else out.push(esc(l));
  });
  return out.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

/* Kaggle runs print pandas tables as wrapped plain text; swap each one for the CSV file holding the same table. */
function splitFrames(text, csvFiles) {
  // a pandas print is a header line + index rows; wide frames wrap into several such blocks whose header ends in "\"
  const L = text.split("\n"), parts = [], isRow = (l) => /^\s*\d+\s/.test(l || "");
  let buf = [], i = 0;
  const flush = () => { if (buf.length) { parts.push({ text: buf.join("\n") }); buf = []; } };
  while (i < L.length) {
    const start = i, cols = [];
    let frame = false;
    while (i < L.length && L[i].trim() && !isRow(L[i]) && isRow(L[i + 1])) {
      frame = true;
      const cont = /\\\s*$/.test(L[i]);
      cols.push(...L[i].replace(/\\\s*$/, "").trim().split(/\s+/));
      i++;
      while (isRow(L[i])) i++;
      if (!cont) break;
      while (i < L.length && !L[i].trim()) i++;
    }
    if (!frame) { buf.push(L[i]); i++; continue; }
    const f = csvFiles.find((c) => cols.filter((col) => c.head.includes(col)).length >= Math.min(3, cols.length));
    if (f) { flush(); parts.push({ csv: f }); } else buf.push(...L.slice(start, i));
  }
  flush();
  return parts;
}
function csvTable({ head, rows }) {
  const num = head.map((_, i) => rows.every((r) => r[i] === "" || !isNaN(+r[i])));
  const fmt = (v, i) => (v === "" ? `<span class="muted">–</span>` : num[i] && String(v).includes(".") ? (+v).toLocaleString(undefined, { maximumFractionDigits: 4 }) : esc(v));
  return `<div class="table-wrap" style="margin-bottom:16px"><table class="t compact"><thead><tr>${head.map((h, i) => `<th class="${num[i] ? "" : "l"}">${esc(h.replace(/_/g, " "))}</th>`).join("")}</tr></thead>
    <tbody>${rows.slice(0, 60).map((r) => `<tr>${r.map((v, i) => `<td class="${num[i] ? "" : "l"}">${fmt(v, i)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
async function logHtml(o, run) {
  const t = cleanLog(o.text);
  if (!t) return "";
  const csvs = run.source === "kaggle" ? run.files.filter((f) => f.name.endsWith(".csv") && !/^(predictions|train|test|hairfall_clean)\.csv$/.test(f.name)) : [];
  if (!csvs.length) return `<pre class="log ${o.name === "stderr" ? "stderr" : ""}">${t}</pre>`;
  const tables = await Promise.all(csvs.map(async (f) => ({ ...parseCSV(await fileText(f.key)), name: f.name })));
  const parts = splitFrames(t, tables.filter((x) => x.rows.length <= 60));
  return parts.map((p) => (p.csv ? csvTable(p.csv) : p.text.trim() ? `<pre class="log">${p.text.trim()}</pre>` : "")).join("");
}
function kpisHtml(d) {
  if (!d) return "";
  const k = (label, v, cls = "") => `<div class="kpi ${cls}"><span>${label}</span><b>${esc(v)}</b></div>`;
  if (d._kind === "metrics") {
    return `<div class="kpis">${k("Accuracy", d.accuracy)}${k("Macro F1", d.macro_f1)}${k("Weighted F1", d.weighted_f1)}${k("ROC-AUC", d.roc_auc_ovr)}
      ${k("Training rows", (d.context_rows ?? 0).toLocaleString())}${k("Test rows", (d.test_rows ?? 0).toLocaleString())}</div>`;
  }
  return `<div class="kpis">${k("Rows explained", d.rows_explained)}${k("Explainer", d.explainer || "–")}
    <div class="kpi wide"><span>Top 5 features</span><b>${(d.top_5 || []).map(esc).join(", ")}</b></div></div>`;
}
function timingHtml(run, d) {   // one compact line instead of a grid of cards
  const bits = [];
  if (d?._kind === "metrics") {
    bits.push(`fit <b>${fmtTime(d.fit_seconds)}</b>`);
    if (d.predict_seconds === 0 && /TabPFN|TabFM/.test(d.model || "")) bits.push(`prediction time not measured (saved predictions were reused)`);
    else {
      const per = d.predict_seconds > 0 && d.test_rows ? (d.predict_seconds / d.test_rows) * 1000 : null;
      bits.push(`predicting ${(d.test_rows ?? 0).toLocaleString()} test patients <b>${d.predict_seconds < 0.05 ? "< 0.1 s" : fmtTime(d.predict_seconds)}</b>${per != null ? ` (${per < 10 ? per.toFixed(1) : Math.round(per)} ms each)` : ""}`);
    }
  } else if (d?._kind === "shap") {
    bits.push(`explaining ${d.rows_explained} rows <b>${fmtTime(d.seconds)}</b>${d.rows_explained ? ` (${fmtTime(d.seconds / d.rows_explained)} per row)` : ""}`);
  }
  if (run.seconds != null) bits.push(`step total <b>${fmtTime(run.seconds)}</b>`);
  bits.push(run.source === "kaggle" ? "on a Kaggle Tesla T4 GPU" : "on this Mac");
  return `<div class="timeline">${icon("history")}<span>${bits.join(" · ")}</span></div>`;
}
function paintOutput(run) {
  const out = $("#nbOut");
  if (!run) { $("#nbTabs").innerHTML = `<button class="on">Output</button>`; out.innerHTML = `<div class="empty">${icon("play")}<h3>Not run yet</h3><p>Press <b>Run step</b> to execute this step.</p></div>`; NB.outKey = ""; return; }
  const size = run.outputs.reduce((n, o) => n + (o.text ? o.text.length : 0), 0);
  const k = JSON.stringify([run.id, run.status, run.outputs.length, size, run.files.length, NB.outTab]);
  if (k === NB.outKey) return;
  const first = !NB.outKey.startsWith(`[${run.id},`);
  NB.outKey = k;
  const nFiles = run.files.length;
  if (NB.outTab === "files" && !nFiles) NB.outTab = "output";
  $("#nbTabs").innerHTML = `<button data-t="output" class="${NB.outTab === "output" ? "on" : ""}">Output</button>
    <button data-t="files" class="${NB.outTab === "files" ? "on" : ""}" ${nFiles ? "" : "disabled"}>Files<span class="count">${nFiles}</span></button>`;
  $$("#nbTabs button").forEach((b) => b.onclick = () => { NB.outTab = b.dataset.t; NB.outKey = ""; paintOutput(run); });

  const pinned = first || out.scrollHeight - out.scrollTop - out.clientHeight < 60, prevTop = out.scrollTop;
  if (NB.outTab === "files") { out.innerHTML = filesHtml(run); wireFiles(out); out.scrollTop = 0; return; }

  const imgs = run.outputs.filter((o) => o.type === "image");
  const pngNames = run.source === "kaggle" ? run.files.filter((f) => f.name.endsWith(".png")).map((f) => f.name) : [];
  let html = `<div id="nbKpis">${isBusy(run) ? "" : timingHtml(run, null)}</div>`;
  run.outputs.forEach((o) => {
    if (o.type === "stream") html += `<div class="log-slot" data-i="${run.outputs.indexOf(o)}"></div>`;
    else if (o.type === "error") html += `<pre class="log err">${esc(stripAnsi(o.text))}</pre>`;
    else if (o.type === "result" && o.html) html += `<div class="out-html">${o.html}</div>`;
    else if (o.type === "result" && o.text && o.text !== "{}") html += `<pre class="log">${esc(o.text)}</pre>`;
  });
  if (imgs.length) html += `<div class="gallery">${imgs.map((o, i) => `<figure><img class="zoom" src="/api/files/${o.key}" loading="lazy" alt="${esc(pngNames[i] || "figure " + (i + 1))}"><figcaption>${esc(pngNames[i] || "Figure " + (i + 1))}</figcaption></figure>`).join("")}</div>`;
  if (isBusy(run)) html += `<div class="jump hidden" id="nbJump"><button class="btn sm primary">↓ Jump to latest</button></div>`;
  if (!run.outputs.length && isBusy(run)) html = `<div class="empty"><span class="spin" style="margin:0 auto 10px;width:28px;height:28px"></span><h3>${run.status === "queued" ? "Waiting in the queue…" : "Running…"}</h3></div>`;
  out.innerHTML = html;
  if (isBusy(run) && pinned) out.scrollTop = out.scrollHeight;
  else if (first) out.scrollTop = run.status === "ok" ? 0 : out.scrollHeight;
  else out.scrollTop = prevTop;
  $("#nbJump")?.querySelector("button")?.addEventListener("click", () => { out.scrollTop = out.scrollHeight; });
  $$(".log-slot", out).forEach((slot) => {   // fill synchronously when possible so live logs never flicker
    const o = run.outputs[+slot.dataset.i];
    if (run.source !== "kaggle") { const t = cleanLog(o.text); slot.outerHTML = t ? `<pre class="log ${o.name === "stderr" ? "stderr" : ""}">${t}</pre>` : ""; }
    else logHtml(o, run).then((h) => { if (NB.outKey === k && slot.isConnected) slot.outerHTML = h; });
  });
  if (isBusy(run) && pinned) out.scrollTop = out.scrollHeight;
  if (run.status === "ok") Lab.summary(run).then((d) => { const box = $("#nbKpis"); if (box && NB.outKey === k) box.innerHTML = (d ? kpisHtml(d) : "") + timingHtml(run, d); });
}
$("#nbOut").addEventListener("scroll", () => {
  const o = $("#nbOut"), j = $("#nbJump");
  if (j) j.classList.toggle("hidden", o.scrollHeight - o.scrollTop - o.clientHeight < 60);
});

function filesHtml(run) {
  return `<div class="files">${run.files.map((f, i) => {
    const ext = f.name.split(".").pop().toLowerCase(), previewable = ["csv", "json", "txt"].includes(ext);
    return `<div class="file" data-i="${i}"><div class="file-head"><span class="fi">${esc(ext)}</span>
      <span class="fn">${esc(f.name)}<small>${previewable ? "Click Preview to see the contents" : ext === "png" ? "Figure" : "Binary file"}</small></span>
      ${previewable || ext === "png" ? `<button class="btn sm pv">Preview</button>` : ""}
      <a class="btn sm icon" href="/api/files/${f.key}?download=true" title="Download">${icon("download")}</a></div><div class="preview hidden"></div></div>`;
  }).join("")}</div>`;
}
function wireFiles(root) {
  const run = NB.viewRun || curStep().last_run;
  $$(".file", root).forEach((el) => {
    const btn = $(".pv", el); if (!btn) return;
    btn.onclick = async () => {
      const box = $(".preview", el), f = run.files[+el.dataset.i], ext = f.name.split(".").pop().toLowerCase();
      if (!box.classList.contains("hidden")) { box.classList.add("hidden"); btn.textContent = "Preview"; return; }
      btn.textContent = "Hide";
      box.classList.remove("hidden");
      if (box.dataset.done) return;
      box.dataset.done = 1;
      if (ext === "png") { box.innerHTML = `<img class="zoom" src="/api/files/${f.key}" alt="${esc(f.name)}" style="display:block;max-width:100%;margin:0 auto;padding:10px">`; return; }
      const text = await fileText(f.key);
      if (ext === "csv") {
        const { head, rows } = parseCSV(text), shown = rows.slice(0, 200);
        box.innerHTML = `<div class="table-wrap"><table class="t compact"><thead><tr>${head.map((h) => `<th class="l">${esc(h)}</th>`).join("")}</tr></thead>
          <tbody>${shown.map((r) => `<tr>${r.map((c) => `<td class="l">${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
          ${rows.length > shown.length ? `<div class="muted" style="padding:8px 14px;font-size:13px">Showing ${shown.length} of ${rows.length.toLocaleString()} rows — download for all.</div>` : ""}`;
      } else {
        let t = text; try { t = JSON.stringify(JSON.parse(text), null, 2); } catch { /* not JSON */ }
        box.innerHTML = `<pre>${esc(t.slice(0, 20000))}</pre>`;
      }
    };
  });
}

/* ---------------- polling ---------------- */
async function nbRefresh() {
  try {
    const [st] = await Promise.all([api("/api/status"), Lab.loadSteps()]);
    NB.status = st; setConn(true);
    if (!NB.selected || !curStep()) NB.selected = Lab.steps[0]?.id;
    paintSide(); paintKernel(); paintStep();
  } catch { setConn(false); }
}
let nbTimer = null;
Views.notebook = {
  lastSub: () => NB.selected,
  show(sub) {
    if (sub && sub !== NB.selected) {
      if (NB.loadedKey) NB.drafts[NB.selected] = ed.value;
      NB.selected = sub; NB.viewRun = null; NB.loadedKey = ""; NB.outKey = ""; NB.histKey = ""; NB.outTab = "output";
      store.set("step", sub);
    }
    applyCodeHidden();
    nbRefresh();
    clearInterval(nbTimer);
    nbTimer = setInterval(() => { if (currentTab === "notebook") nbRefresh(); else clearInterval(nbTimer); }, 2000);
  },
};
document.addEventListener("keydown", (e) => {
  if (currentTab !== "notebook") return;
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); if (!isBusy(curStep()?.last_run)) nbRun(); }
  else if (e.altKey && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
    e.preventDefault();
    const i = Lab.steps.findIndex((s) => s.id === NB.selected), n = Lab.steps[i + (e.key === "ArrowDown" ? 1 : -1)];
    if (n) { go("notebook", n.id); requestAnimationFrame(() => $(".nb-item.active")?.scrollIntoView({ block: "nearest" })); }
  }
});
