/* Shared helpers, routing, tooltip, lightbox and small SVG charts. */
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];

async function api(path, opts = {}) {
  const r = await fetch(path, { headers: { "content-type": "application/json" }, ...opts });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(typeof body.detail === "string" ? body.detail : r.statusText); e.detail = body.detail; throw e; }
  return body;
}
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (name, cls = "") => `<svg class="ic ${cls}"><use href="#i-${name}"/></svg>`;
const fmtNum = (v, d = 2) => Number(v).toLocaleString(undefined, { maximumFractionDigits: d });
const fmtTime = (s) => (s == null ? "–" : s === 0 ? "< 0.1 s" : s < 1 ? `${Math.round(s * 1000)} ms` : s < 60 ? `${s.toFixed(1)} s`
  : s < 3600 ? `${Math.floor(s / 60)}m ${Math.round(s % 60)}s` : `${Math.floor(s / 3600)}h ${Math.round((s % 3600) / 60)}m`);
const pct = (x, d = 0) => (x * 100).toFixed(d) + "%";
const stripAnsi = (s) => String(s).replace(/\x1b\[[0-9;]*m/g, "");
const store = {
  get(k, d = null) { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};
const RISK = ["Low", "Moderate", "High"];
const MODELS = { CatBoost: "catboost", TabPFN: "tabpfn", TabFM: "tabfm" };
const MODEL_LABEL = { catboost: "CatBoost", tabpfn: "TabPFN", tabfm: "TabFM" };
const modelKey = (name) => MODELS[name] || String(name).toLowerCase();
const SIZES = ["500", "2000", "Full"];

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
  const [head = [], ...body] = rows.filter((r) => r.length > 1 || r[0] !== "");
  return { head, rows: body };
}
const fileText = async (key) => (await fetch(`/api/files/${key}`)).text();
const fileJSON = async (key) => (await fetch(`/api/files/${key}`)).json();

/* ---------------- routing: #tab/sub ---------------- */
const Views = {};
let currentTab = null;
function go(tab, sub) { location.hash = sub ? `${tab}/${sub}` : tab; }
function route() {
  const [tab0, ...rest] = location.hash.slice(1).split("/");
  const tab = Views[tab0] ? tab0 : "predict";
  const sub = rest.join("/") || null;
  $$("#nav button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  Object.keys(Views).forEach((t) => $("#" + t).classList.toggle("hidden", t !== tab));
  if (currentTab !== tab) store.set("tab", tab);
  currentTab = tab;
  Views[tab].show(sub);
}
$$("#nav button").forEach((b) => b.onclick = () => {
  const t = b.dataset.tab;
  go(t, t === currentTab ? null : Views[t].lastSub?.());
});
window.addEventListener("hashchange", route);

/* ---------------- connection indicator ---------------- */
function setConn(ok) {
  $("#conn").classList.toggle("off", !ok);
  $("#conn span").textContent = ok ? "Connected" : "Server offline";
}

/* ---------------- tooltip: any element with data-tip ---------------- */
const tip = document.createElement("div");
tip.className = "tip hidden";
document.body.appendChild(tip);
document.addEventListener("mouseover", (e) => {
  const t = e.target.closest("[data-tip]");
  if (!t) { tip.classList.add("hidden"); return; }
  tip.innerHTML = t.dataset.tip;
  tip.classList.remove("hidden");
});
document.addEventListener("mousemove", (e) => {
  if (tip.classList.contains("hidden")) return;
  const w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX + 14, y = e.clientY + 14;
  if (x + w > innerWidth - 8) x = e.clientX - w - 14;
  if (y + h > innerHeight - 8) y = e.clientY - h - 14;
  tip.style.left = x + "px"; tip.style.top = y + "px";
});

/* ---------------- lightbox: click any .zoom image ---------------- */
document.addEventListener("click", (e) => {
  const img = e.target.closest("img.zoom");
  if (!img) return;
  const box = document.createElement("div");
  box.className = "lightbox";
  box.innerHTML = `<img src="${img.src}" alt=""><div class="cap">${esc(img.alt || "")}</div>`;
  box.onclick = () => box.remove();
  document.body.appendChild(box);
});
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $(".lightbox")?.remove(); });

/* ---------------- charts ---------------- */
/* Line chart over the three training sizes; one series per model. */
function lineChart({ series, fmt = (v) => v.toFixed(3), height = 280, log = false, unit = "" }) {
  const W = 600, H = height, m = { l: 56, r: 80, t: 14, b: 30 };
  const vals = series.flatMap((s) => s.values.filter((v) => v != null));
  let lo = Math.min(...vals), hi = Math.max(...vals);
  if (log) { lo = Math.log10(Math.max(lo, 0.01)); hi = Math.log10(Math.max(hi, 0.01)); }
  const pad = (hi - lo) * 0.12 || 0.01; lo -= pad; hi += pad;
  const tr = (v) => (log ? Math.log10(Math.max(v, 0.01)) : v);
  const x = (i) => m.l + (i * (W - m.l - m.r)) / (SIZES.length - 1);
  const y = (v) => m.t + (1 - (tr(v) - lo) / (hi - lo)) * (H - m.t - m.b);
  const ticks = 4, grid = [];
  for (let i = 0; i <= ticks; i++) {
    const tv = lo + ((hi - lo) * i) / ticks, real = log ? 10 ** tv : tv;
    grid.push(`<line x1="${m.l}" x2="${W - m.r}" y1="${y(real)}" y2="${y(real)}"/><text x="${m.l - 8}" y="${y(real) + 4}" text-anchor="end">${log ? fmtTime(real) : fmt(real)}</text>`);
  }
  const labels = []; // direct labels at the line ends, nudged apart so they never overlap
  series.forEach((s) => { const i = s.values.length - 1; if (s.values[i] != null) labels.push({ s, y: y(s.values[i]) }); });
  labels.sort((a, b) => a.y - b.y);
  for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img">
    <g class="grid">${grid.join("")}</g>
    ${SIZES.map((sz, i) => `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${sz === "Full" ? "Full (17,284)" : sz + " rows"}</text>`).join("")}
    ${series.map((s) => {
      const pts = s.values.map((v, i) => (v == null ? null : [x(i), y(v)])).filter(Boolean);
      return `<polyline points="${pts.map((p) => p.join(",")).join(" ")}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round"/>
        ${s.values.map((v, i) => (v == null ? "" : `<circle cx="${x(i)}" cy="${y(v)}" r="4.5" fill="${s.color}" stroke="#fff" stroke-width="2"/>
        <circle cx="${x(i)}" cy="${y(v)}" r="13" fill="transparent" data-tip="<b>${esc(s.name)}</b> · ${SIZES[i]} rows<br>${esc(log ? fmtTime(v) : fmt(v))}${unit}"/>`)).join("")}`;
    }).join("")}
    ${labels.map((l) => `<text class="lbl" x="${W - m.r + 8}" y="${l.y + 4}">${esc(l.s.name)}</text>`).join("")}
  </svg>`;
}

/* Semicircle gauge 0-100 with Low / Moderate / High zones. */
function gauge(score) {
  const R = 80, cx = 100, cy = 96, pt = (v, r = R) => { const a = Math.PI * (1 - v / 100); return [cx + r * Math.cos(a), cy - r * Math.sin(a)]; };
  const arc = (a, b, col) => { const [x1, y1] = pt(a), [x2, y2] = pt(b); return `<path d="M${x1} ${y1} A${R} ${R} 0 0 1 ${x2} ${y2}" stroke="${col}" stroke-width="16" fill="none"/>`; };
  const [nx, ny] = pt(score, R - 22);
  const c = score < 33.4 ? 0 : score < 66.7 ? 1 : 2;
  return `<svg class="gauge" viewBox="0 0 200 116" role="img" aria-label="Risk score ${score} of 100">
    ${arc(0.5, 32.8, "var(--good)")}${arc(34, 65.8, "var(--warn)")}${arc(67, 99.5, "var(--crit)")}
    <line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="var(--ink)" stroke-width="3.5" stroke-linecap="round"/>
    <circle cx="${cx}" cy="${cy}" r="7" fill="var(--ink)"/><circle cx="${cx}" cy="${cy}" r="2.5" fill="#fff"/>
    <text x="${cx}" y="${cy - 30}" text-anchor="middle" font-size="30" font-weight="800" fill="var(--${["good", "warn", "crit"][c]}-ink)">${score}</text>
  </svg>`;
}

/* Blue sequential fill for heatmap cells (confusion matrices, SHAP ranks). */
function seqFill(t) {
  const a = [238, 244, 252], b = [26, 86, 170];
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * Math.min(1, Math.max(0, t))));
  return { bg: `rgb(${c.join(",")})`, fg: t > 0.5 ? "#fff" : "var(--ink)" };
}

/* ---------------- shared step data ---------------- */
const Lab = {
  steps: [],
  summaries: new Map(),
  async loadSteps() { this.steps = await api("/api/steps"); return this.steps; },
  async summary(run) {   // metrics.json / shap_summary.json of a finished run
    if (!run) return null;
    if (this.summaries.has(run.id)) return this.summaries.get(run.id);
    const f = (run.files || []).find((x) => x.name === "metrics.json" || x.name === "shap_summary.json");
    if (!f) { if (run.status === "ok") this.summaries.set(run.id, null); return null; }
    try {
      const d = await fileJSON(f.key);
      d._kind = f.name === "metrics.json" ? "metrics" : "shap";
      this.summaries.set(run.id, d);
      return d;
    } catch { return null; }
  },
  file(stepPrefix, name) {
    const s = this.steps.find((x) => x.id.startsWith(stepPrefix));
    const r = s && s.last_run;
    return r && r.status === "ok" ? (r.files || []).find((f) => f.name === name) || null : null;
  },
};

document.addEventListener("DOMContentLoaded", () => {
  if (!location.hash) history.replaceState(null, "", "#" + store.get("tab", "predict"));
  route();
});
