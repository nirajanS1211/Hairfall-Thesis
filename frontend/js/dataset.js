/* Dataset: the raw patient table in Postgres, with class balance, search, sorting and column statistics. */
const DS = { offset: 0, limit: 50, sort: null, desc: false, q: "", built: false, total: 0 };

async function dsBuild() {
  const wrap = $("#dWrap");
  wrap.innerHTML = `<div class="card waiting"><span class="spin"></span></div>`;
  const s = await api("/api/dataset/stats");
  const t = s.target, cls = ["good", "warn", "crit"];
  const g = Object.entries(s.gender).sort((a, b) => b[1] - a[1]);
  wrap.innerHTML = `
    <div class="page-head"><div><h1>Dataset</h1><p>The raw patient records from <code>thesis_project/data/data.csv</code>, stored in Postgres. Names are encoded and never used by the models.</p></div></div>
    <div class="stats-row">
      <div class="card stat"><div class="k">${icon("user")}Patients</div><div class="v">${s.rows.toLocaleString()}</div><div class="s">one row per patient</div></div>
      <div class="card stat"><div class="k">${icon("db")}Columns</div><div class="v">${s.columns}</div><div class="s">${s.columns - 3} model features + id, name, target</div></div>
      <div class="card stat"><div class="k">${icon("check")}Missing values</div><div class="v">${s.missing.toLocaleString()}</div><div class="s">${s.missing ? "need attention" : "complete dataset"}</div></div>
      <div class="card stat"><div class="k">${icon("user")}Gender</div><div class="v">${pct(g[0][1] / s.rows)} ${esc(g[0][0].toLowerCase())}</div><div class="s">${g.map(([k, v]) => `${esc(k)} ${v.toLocaleString()}`).join(" · ")}</div></div>
    </div>
    <div class="card card-pad" style="margin-top:20px"><div class="card-head"><div><h2>Hair-fall risk (target)</h2><p>How many patients are in each risk class.</p></div></div>
      <div class="dist">${[0, 1, 2].map((k) => `<span style="width:${(t[k] / s.rows) * 100}%;background:var(--${cls[k]})" data-tip="${RISK[k]} risk: ${t[k].toLocaleString()} patients">${pct(t[k] / s.rows)}</span>`).join("")}</div>
      <div class="dist-legend">${[0, 1, 2].map((k) => `<span><i style="background:var(--${cls[k]})"></i>${RISK[k]} risk <b>${t[k].toLocaleString()}</b></span>`).join("")}</div></div>
    <div class="card" style="margin-top:20px">
      <div class="toolbar"><div class="search">${icon("search")}<input class="input" id="dsSearch" type="search" placeholder="Search any column…"></div>
        <span class="muted" id="dsInfo"></span><span class="spacer"></span>
        <div class="pager"><button class="btn sm" id="dsPrev">← Previous</button><button class="btn sm" id="dsNext">Next →</button></div></div>
      <div class="table-wrap ds-table"><table class="t compact" id="dsTable"></table></div>
    </div>
    <div class="card" style="margin-top:20px"><div class="card-pad" style="padding-bottom:0"><div class="card-head"><div><h2>Column statistics</h2><p>Numeric columns only.</p></div></div></div>
      <div class="table-wrap" style="border:0;border-radius:0 0 var(--r-lg) var(--r-lg);border-top:1px solid var(--line)"><table class="t compact">
      <thead><tr>${Object.keys(s.describe[0] || {}).map((c) => `<th class="${c === "column" ? "l" : ""}">${esc(c)}</th>`).join("")}</tr></thead>
      <tbody>${s.describe.map((r) => `<tr>${Object.entries(r).map(([c, v]) => `<td class="${c === "column" ? "l" : ""}">${c === "column" ? `<b>${esc(v)}</b>` : esc(fmtNum(v, 3))}</td>`).join("")}</tr>`).join("")}</tbody></table></div></div>`;
  let timer;
  $("#dsSearch").oninput = (e) => { clearTimeout(timer); timer = setTimeout(() => { DS.q = e.target.value.trim(); DS.offset = 0; dsRows(); }, 300); };
  $("#dsPrev").onclick = () => { DS.offset = Math.max(0, DS.offset - DS.limit); dsRows(); };
  $("#dsNext").onclick = () => { DS.offset += DS.limit; dsRows(); };
  DS.built = true;
  dsRows();
}

async function dsRows() {
  const p = new URLSearchParams({ offset: DS.offset, limit: DS.limit, desc: DS.desc });
  if (DS.sort) p.set("sort", DS.sort);
  if (DS.q) p.set("q", DS.q);
  const d = await api(`/api/dataset?${p}`);
  DS.total = d.total;
  const iT = d.columns.indexOf("hair_fall");
  $("#dsTable").innerHTML = `<thead><tr>${d.columns.map((c) => `<th class="sortable ${DS.sort === c ? "sorted" : ""} ${c === "full_name" || c === "gender" ? "l" : ""}" data-c="${esc(c)}">${esc(c.replace(/_/g, " "))}${DS.sort === c ? (DS.desc ? " ↓" : " ↑") : ""}</th>`).join("")}</tr></thead>
    <tbody>${d.rows.map((r) => `<tr>${r.map((v, i) => {
      if (i === iT) return `<td><span class="pill risk risk${v}"><i></i>${RISK[v]}</span></td>`;
      const c = d.columns[i];
      return `<td class="${c === "full_name" ? "l name" : c === "gender" ? "l" : ""}" ${c === "full_name" ? `title="${esc(v)}"` : ""}>${esc(v)}</td>`;
    }).join("")}</tr>`).join("")}</tbody>`;
  $$("#dsTable th").forEach((th) => th.onclick = () => { DS.desc = DS.sort === th.dataset.c ? !DS.desc : false; DS.sort = th.dataset.c; DS.offset = 0; dsRows(); });
  $("#dsInfo").textContent = d.total ? `${(DS.offset + 1).toLocaleString()}–${Math.min(DS.offset + DS.limit, d.total).toLocaleString()} of ${d.total.toLocaleString()} rows` : "No rows match";
  $("#dsPrev").disabled = DS.offset === 0;
  $("#dsNext").disabled = DS.offset + DS.limit >= d.total;
}

Views.dataset = {
  show() {
    if (!DS.built) dsBuild().catch((e) => { $("#dWrap").innerHTML = `<div class="card empty">${icon("info")}<h3>Dataset not available</h3><p>${esc(e.message)}</p></div>`; });
  },
};

/* keep the connection indicator honest on every tab */
setInterval(() => { if (currentTab !== "notebook") api("/api/status").then(() => setConn(true), () => setConn(false)); }, 5000);
