import { useEffect, useState } from "react";
import {
  fetchHistory,
  fetchMeta,
  logPrediction,
  predictCatboost,
  predictTabfm,
  predictTabpfn,
} from "../api";
import { FlaskIcon, HistoryIcon, ListIcon, ScissorsIcon, UserIcon } from "../icons";
import { ConfidenceBars, ErrorBanner, RiskBadge, Spinner, TimedSpinner, WarnBanner } from "./shared";

const GROUP_ICONS = {
  Demographics: UserIcon,
  "Blood & Lab Values": FlaskIcon,
  "Hair & Stress Indices": ScissorsIcon,
  "Lifestyle & History": ListIcon,
};

function defaultValues(featureMeta) {
  const values = {};
  for (const [name, meta] of Object.entries(featureMeta)) {
    values[name] = meta.type === "bool" ? "0" : "";
  }
  return values;
}

function CatboostCard({ state }) {
  if (state.status === "idle") {
    return <p className="placeholder-note">Submit the form to see a prediction.</p>;
  }
  if (state.status === "loading") return <Spinner label="Running CatBoost…" />;
  if (state.status === "error") return <ErrorBanner message={state.error} />;

  const { data } = state;
  return (
    <>
      <RiskBadge prediction={data.prediction} />
      <ConfidenceBars confidence={data.confidence} />
      <div className="shap-list">
        <h3>Top factors for this prediction</h3>
        {data.top_features.map((f) => (
          <div className="shap-item" key={f.feature}>
            <span className="shap-name">{f.label}</span>
            <span className={`shap-dir ${f.direction}`}>
              {f.direction === "increases" ? "raises risk" : "lowers risk"}
            </span>
            <span className="shap-val">
              {f.shap > 0 ? "+" : ""}
              {f.shap}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}

function FoundationModelCard({
  state,
  available,
  unavailableMessage,
  loadingLabel,
  expectedSeconds,
  loadingExplainer,
  note,
  unavailableExtra,
}) {
  if (!available && state.status === "idle") {
    return (
      <p className="placeholder-note">
        Not configured on this server yet ({unavailableMessage}). CatBoost predictions still
        work fully.
        {unavailableExtra}
      </p>
    );
  }
  if (state.status === "idle") {
    return <p className="placeholder-note">Submit the form to see a prediction.</p>;
  }
  if (state.status === "unavailable") {
    return (
      <p className="placeholder-note">
        Not configured on this server yet ({state.message}). CatBoost predictions still work
        fully.
        {unavailableExtra}
      </p>
    );
  }
  if (state.status === "loading") {
    return <TimedSpinner label={loadingLabel} expectedSeconds={expectedSeconds} explainer={loadingExplainer} />;
  }
  if (state.status === "error") return <ErrorBanner message={state.error} />;

  const { data } = state;
  return (
    <>
      <RiskBadge prediction={data.prediction} />
      <ConfidenceBars confidence={data.confidence} />
      {note && (
        <p className="placeholder-note" style={{ marginTop: 16 }}>
          {note}
        </p>
      )}
    </>
  );
}

export default function PredictTab() {
  const [meta, setMeta] = useState(null);
  const [metaError, setMetaError] = useState(null);
  const [values, setValues] = useState({});
  const [formError, setFormError] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [cbState, setCbState] = useState({ status: "idle" });
  const [tpState, setTpState] = useState({ status: "idle" });
  const [tfState, setTfState] = useState({ status: "idle" });
  const [submitting, setSubmitting] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState({ status: "idle", items: [], total: 0, error: null });

  useEffect(() => {
    fetchMeta()
      .then((m) => {
        setMeta(m);
        setValues(defaultValues(m.feature_meta));
      })
      .catch((err) => setMetaError(err.message));
  }, []);

  function updateField(name, val) {
    setValues((prev) => ({ ...prev, [name]: val }));
  }

  function buildPayload() {
    const payload = {};
    for (const [name, fmeta] of Object.entries(meta.feature_meta)) {
      const raw = values[name];
      if (raw === "" || raw === undefined || raw === null) {
        throw new Error(`${fmeta.label} is required.`);
      }
      if (fmeta.type === "text") {
        payload[name] = String(raw).trim();
        continue;
      }
      const num = fmeta.type === "number" ? parseFloat(raw) : parseInt(raw, 10);
      if (Number.isNaN(num)) throw new Error(`${fmeta.label} has an invalid value.`);
      payload[name] = num;
    }
    return payload;
  }

  function fillFromHistory(input) {
    const next = {};
    for (const [name, fmeta] of Object.entries(meta.feature_meta)) {
      const v = input?.[name];
      next[name] = v === undefined || v === null ? (fmeta.type === "bool" ? "0" : "") : String(v);
    }
    setValues(next);
    setCbState({ status: "idle" });
    setTpState({ status: "idle" });
    setTfState({ status: "idle" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const HISTORY_PAGE_SIZE = 20;

  async function loadHistory() {
    setHistory((h) => ({ ...h, status: "loading" }));
    try {
      const data = await fetchHistory(HISTORY_PAGE_SIZE, 0);
      setHistory({ status: "done", items: data.items, total: data.total, error: null });
    } catch (err) {
      setHistory({ status: "error", items: [], total: 0, error: err.message });
    }
  }

  async function loadMoreHistory() {
    setHistory((h) => ({ ...h, status: "loading-more" }));
    try {
      const data = await fetchHistory(HISTORY_PAGE_SIZE, history.items.length);
      setHistory((h) => ({
        status: "done",
        items: [...h.items, ...data.items],
        total: data.total,
        error: null,
      }));
    } catch (err) {
      setHistory((h) => ({ ...h, status: "done", error: err.message }));
    }
  }

  function toggleHistory() {
    const next = !historyOpen;
    setHistoryOpen(next);
    if (next && history.status === "idle") loadHistory();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError(null);
    setWarnings([]);

    let payload;
    try {
      payload = buildPayload();
    } catch (err) {
      setFormError(err.message);
      return;
    }

    setSubmitting(true);
    setCbState({ status: "loading" });
    setTpState({ status: "loading" });
    setTfState({ status: "loading" });

    const seenWarnings = new Set();
    const mergeWarnings = (list) => {
      const fresh = (list || []).filter((w) => !seenWarnings.has(w));
      fresh.forEach((w) => seenWarnings.add(w));
      if (fresh.length) setWarnings((prev) => [...prev, ...fresh]);
    };

    let cbResult = null;
    let tpResult = null;
    let tfResult = null;

    const cbTask = predictCatboost(payload)
      .then((data) => {
        cbResult = data;
        setCbState({ status: "done", data });
        mergeWarnings(data.warnings);
      })
      .catch((err) => setCbState({ status: "error", error: err.message }));

    const tpTask = meta.tabpfn_available
      ? predictTabpfn(payload)
          .then((data) => {
            tpResult = data;
            setTpState({ status: "done", data });
            mergeWarnings(data.warnings);
          })
          .catch((err) => setTpState({ status: "error", error: err.message }))
      : Promise.resolve(setTpState({ status: "unavailable", message: meta.tabpfn_error }));

    const tfTask = meta.tabfm_available
      ? predictTabfm(payload)
          .then((data) => {
            tfResult = data;
            setTfState({ status: "done", data });
            mergeWarnings(data.warnings);
          })
          .catch((err) => setTfState({ status: "error", error: err.message }))
      : Promise.resolve(setTfState({ status: "unavailable", message: meta.tabfm_error }));

    await Promise.allSettled([cbTask, tpTask, tfTask]);

    try {
      await logPrediction({
        input: payload,
        catboost_result: cbResult,
        tabpfn_result: tpResult,
        tabfm_result: tfResult,
      });
      if (historyOpen) loadHistory();
    } catch {
      /* empty */
    }

    setSubmitting(false);
  }

  if (metaError) {
    return (
      <div className="card">
        <ErrorBanner
          message={`Could not load form configuration: ${metaError}. Is the backend running at the configured API URL?`}
        />
      </div>
    );
  }
  if (!meta) {
    return (
      <div className="card">
        <Spinner label="Loading form…" />
      </div>
    );
  }

  return (
    <>
      {formError && (
        <div className="banner error">
          <span>{formError}</span>
        </div>
      )}
      <WarnBanner warnings={warnings} />

      <form onSubmit={handleSubmit}>
        {meta.feature_groups.map((group) => {
          const Icon = GROUP_ICONS[group.title];
          return (
            <div className="card" key={group.title}>
              <div className="card-title-row" style={{ marginBottom: 16 }}>
                {Icon && (
                  <span className="section-icon">
                    <Icon />
                  </span>
                )}
                <h2>{group.title}</h2>
              </div>
              <div className="field-grid">
                {group.fields.map((name) => {
                  const fmeta = meta.feature_meta[name];
                  return (
                    <div className="field" key={name}>
                      <label htmlFor={`f_${name}`}>
                        {fmeta.label}
                        {fmeta.unit && <span className="hint"> ({fmeta.unit})</span>}
                      </label>

                      {fmeta.type === "text" && (
                        <input
                          type="text"
                          id={`f_${name}`}
                          required
                          placeholder="e.g. Jane Doe"
                          value={values[name] ?? ""}
                          onChange={(e) => updateField(name, e.target.value)}
                        />
                      )}

                      {fmeta.type === "number" && (
                        <>
                          <input
                            type="number"
                            id={`f_${name}`}
                            required
                            min={fmeta.hard_min}
                            max={fmeta.hard_max}
                            step={fmeta.step}
                            placeholder={`e.g. ${fmeta.train_min}–${fmeta.train_max}`}
                            value={values[name] ?? ""}
                            onChange={(e) => updateField(name, e.target.value)}
                          />
                          <span className="hint">
                            typical range: {fmeta.train_min}–{fmeta.train_max}
                          </span>
                        </>
                      )}

                      {fmeta.type === "select" && (
                        <select
                          id={`f_${name}`}
                          required
                          value={values[name] ?? ""}
                          onChange={(e) => updateField(name, e.target.value)}
                        >
                          <option value="" disabled>
                            Select…
                          </option>
                          {fmeta.options.map(([val, label]) => (
                            <option value={val} key={val}>
                              {label}
                            </option>
                          ))}
                        </select>
                      )}

                      {fmeta.type === "bool" && (
                        <div className="toggle" role="radiogroup" aria-label={fmeta.label}>
                          <input
                            type="radio"
                            id={`f_${name}_no`}
                            name={name}
                            checked={values[name] === "0"}
                            onChange={() => updateField(name, "0")}
                          />
                          <label htmlFor={`f_${name}_no`}>No</label>
                          <input
                            type="radio"
                            id={`f_${name}_yes`}
                            name={name}
                            checked={values[name] === "1"}
                            onChange={() => updateField(name, "1")}
                          />
                          <label htmlFor={`f_${name}_yes`}>Yes</label>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        <div className="submit-row">
          <button type="submit" disabled={submitting}>
            {submitting ? "Predicting…" : "Predict Risk"}
          </button>
          <span className="submit-note">
            CatBoost returns in ~5ms · TabPFN cloud call takes 5–20s · TabFM runs locally on CPU,
            typically 20–45s
          </span>
        </div>
      </form>

      <section className="results-grid results-grid-3">
        <div className="card result-card">
          <div className="card-head">
            <h2>CatBoost</h2>
            <span className="model-sub">local · TreeExplainer SHAP</span>
          </div>
          <CatboostCard state={cbState} />
        </div>
        <div className="card result-card">
          <div className="card-head">
            <h2>TabPFN</h2>
            <span className="model-sub">cloud · zero-shot</span>
          </div>
          <FoundationModelCard
            state={tpState}
            available={meta.tabpfn_available}
            unavailableMessage={meta.tabpfn_error}
            loadingLabel="Calling TabPFN cloud API…"
            expectedSeconds={10}
            loadingExplainer="TabPFN runs on a shared cloud GPU, so timing varies with queue load — this usually lands somewhere between 5 and 20 seconds. Still normal past that; the request will resolve or report a clear error, it will not hang silently."
            note="Live per-request SHAP is not computed for TabPFN (too slow). See the SHAP charts in the Analysis tab."
          />
        </div>
        <div className="card result-card">
          <div className="card-head">
            <h2>TabFM</h2>
            <span className="model-sub">local · 500-row context</span>
          </div>
          <FoundationModelCard
            state={tfState}
            available={meta.tabfm_available}
            unavailableMessage={meta.tabfm_error}
            loadingLabel="Running TabFM…"
            expectedSeconds={35}
            loadingExplainer="TabFM runs locally on this server's CPU — no GPU here, unlike the Colab benchmarks — so it typically takes 20 to 45 seconds. Still normal past that; the request will resolve or report a clear error, it will not hang silently."
            note="Runs locally on this server's CPU (no GPU here, unlike the Colab benchmarks), so it's slower than the other two models. Live per-request SHAP is not computed for TabFM (too slow) — see the SHAP charts in the Analysis tab."
            unavailableExtra={
              <>
                {" "}
                TabFM's PyTorch runtime needs more RAM than this site's free hosting tier
                provides. Clone the repo and run{" "}
                <code>python scripts/predict_tabfm_local.py scripts/sample_patient.json</code>{" "}
                from the <code>backend/</code> folder to get a TabFM prediction on your own
                machine instead.
              </>
            }
          />
        </div>
      </section>

      <div className="card">
        <button type="button" className="link-btn" onClick={toggleHistory}>
          <HistoryIcon />
          Prediction History{history.total ? ` (${history.total})` : ""}
        </button>
        {historyOpen && (
          <div className="history-body">
            {history.status === "loading" && <Spinner label="Loading history…" />}
            {history.status === "error" && (
              <p className="placeholder-note">History unavailable: {history.error}</p>
            )}
            {(history.status === "done" || history.status === "loading-more") &&
              history.items.length === 0 && <p className="placeholder-note">No predictions logged yet.</p>}
            {history.error && <p className="placeholder-note">Could not load more: {history.error}</p>}
            {history.items.length > 0 && (
              <>
                <p className="placeholder-note" style={{ marginBottom: 10 }}>
                  Click any row to refill the form with that submission and predict again.
                </p>
                <div className="table-scroll">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Name</th>
                        <th>Age</th>
                        <th>CatBoost</th>
                        <th>TabPFN</th>
                        <th>TabFM</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.items.map((item, i) => (
                        <tr
                          key={i}
                          className="history-row-clickable"
                          onClick={() => fillFromHistory(item.input)}
                        >
                          <td>{item.timestamp ? new Date(item.timestamp).toLocaleString() : "—"}</td>
                          <td>{item.input?.name ?? "—"}</td>
                          <td>{item.input?.age ?? "—"}</td>
                          <td>
                            {item.catboost_result ? (
                              <span className={`badge-sm ${item.catboost_result.prediction}`}>
                                {item.catboost_result.prediction}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td>
                            {item.tabpfn_result ? (
                              <span className={`badge-sm ${item.tabpfn_result.prediction}`}>
                                {item.tabpfn_result.prediction}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td>
                            {item.tabfm_result ? (
                              <span className={`badge-sm ${item.tabfm_result.prediction}`}>
                                {item.tabfm_result.prediction}
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {history.items.length < history.total && (
                  <button
                    type="button"
                    className="link-btn"
                    style={{ marginTop: 12 }}
                    disabled={history.status === "loading-more"}
                    onClick={loadMoreHistory}
                  >
                    {history.status === "loading-more"
                      ? "Loading…"
                      : `Load more (${history.items.length} of ${history.total})`}
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}
