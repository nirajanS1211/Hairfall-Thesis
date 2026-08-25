import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { API_URL, fetchDatasetSummary, fetchMeta, fetchResults } from "../api";
import { CODE_SNIPPETS } from "../codeSnippets";
import { DatabaseIcon, GridIcon, ImageIcon, ScaleIcon } from "../icons";
import { CodeBlock, ErrorBanner, Spinner } from "./shared";

const RISK_COLOR = { Low: "#0ca30c", Moderate: "#fab219", High: "#d03b3b" };
const MODEL_COLOR = { CatBoost: "#2a78d6", TabPFN: "#eb6834", TabFM: "#1baf7a" };
const MODEL_DOT_CLASS = { CatBoost: "catboost", TabPFN: "tabpfn", TabFM: "tabfm" };

const METRIC_LABELS = {
  accuracy: "Accuracy",
  macro_precision: "Macro Precision",
  macro_recall: "Macro Recall",
  macro_f1: "Macro F1",
  roc_auc: "ROC-AUC",
};

function pct(x) {
  return x === null || x === undefined ? "—" : `${(x * 100).toFixed(1)}%`;
}

function corrColor(v) {
  if (v === null || v === undefined) return "transparent";
  const a = Math.min(Math.abs(v), 1);
  return v >= 0 ? `rgba(42, 120, 214, ${a * 0.8})` : `rgba(227, 73, 72, ${a * 0.8})`;
}

function SectionHead({ icon: Icon, title }) {
  return (
    <div className="card-title-row" style={{ marginBottom: 16 }}>
      <span className="section-icon">
        <Icon />
      </span>
      <h2>{title}</h2>
    </div>
  );
}

function DatasetOverview({ summary }) {
  const data = Object.entries(summary.class_distribution).map(([name, count]) => ({ name, count }));
  return (
    <div className="card">
      <SectionHead icon={DatabaseIcon} title="Dataset Overview" />
      <div className="stat-grid" style={{ marginBottom: 20 }}>
        <div className="stat-tile">
          <div className="stat-tile-label">Records</div>
          <div className="stat-tile-value">{summary.row_count.toLocaleString()}</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile-label">Risk Tiers</div>
          <div className="stat-tile-value">3</div>
        </div>
        <div className="stat-tile">
          <div className="stat-tile-label">Input Features</div>
          <div className="stat-tile-value">20</div>
        </div>
      </div>
      <div style={{ width: "100%", height: 220 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 20, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#52514e", fontSize: 13 }} axisLine={{ stroke: "#c3c2b7" }} tickLine={false} />
            <YAxis tick={{ fill: "#898781", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              cursor={{ fill: "#f3f2ef" }}
              contentStyle={{ borderRadius: 8, border: "1px solid #e1e0d9", fontSize: 13 }}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={90}>
              <LabelList dataKey="count" position="top" style={{ fill: "#0b0b0b", fontSize: 12, fontWeight: 600 }} />
              {data.map((d) => (
                <Cell key={d.name} fill={RISK_COLOR[d.name]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {summary.source && <p className="hint" style={{ marginTop: 10 }}>source: {summary.source}</p>}
      <CodeBlock code={CODE_SNIPPETS.data_cleaning} />
    </div>
  );
}

function CorrelationHeatmap({ summary }) {
  const fields = summary.correlation_fields;
  if (!fields) return null;
  return (
    <div className="card">
      <SectionHead icon={GridIcon} title="Feature Correlation" />
      <div className="corr-scroll">
        <table className="corr-table">
          <thead>
            <tr>
              <th></th>
              {fields.map((f) => (
                <th key={f}>{f}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {fields.map((row) => (
              <tr key={row}>
                <th>{row}</th>
                {fields.map((col) => {
                  const v = summary.correlation[row]?.[col];
                  return (
                    <td key={col} style={{ background: corrColor(v) }} title={`${row} vs ${col}: ${v}`}>
                      {v?.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="corr-legend">
        <span>-1</span>
        <span className="corr-legend-bar" />
        <span>+1</span>
        <span style={{ marginLeft: 6 }}>Pearson correlation across the full dataset</span>
      </div>
    </div>
  );
}

function ModelComparisonChart({ models }) {
  const data = Object.keys(METRIC_LABELS).map((key) => {
    const row = { metric: METRIC_LABELS[key] };
    models.forEach((m) => {
      row[m.name] = m[key];
    });
    return row;
  });

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 20, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
          <XAxis dataKey="metric" tick={{ fill: "#52514e", fontSize: 12 }} axisLine={{ stroke: "#c3c2b7" }} tickLine={false} />
          <YAxis domain={[0, 1]} tick={{ fill: "#898781", fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            cursor={{ fill: "#f3f2ef" }}
            contentStyle={{ borderRadius: 8, border: "1px solid #e1e0d9", fontSize: 13 }}
            formatter={(v) => v.toFixed(3)}
          />
          <Legend wrapperStyle={{ fontSize: 13 }} />
          {models.map((m) => (
            <Bar key={m.name} dataKey={m.name} fill={MODEL_COLOR[m.name]} radius={[5, 5, 0, 0]} maxBarSize={36}>
              <LabelList
                dataKey={m.name}
                position="top"
                formatter={(v) => v.toFixed(3)}
                style={{ fill: "#0b0b0b", fontSize: 10, fontWeight: 600 }}
              />
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ResultsSection({ results }) {
  const sigs = results.significance_tests;
  return (
    <div className="card">
      <SectionHead icon={ScaleIcon} title={`Model Comparison — ${results.split}`} />

      <div className="table-scroll" style={{ marginBottom: 20 }}>
        <table className="compare-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Context</th>
              <th>Accuracy</th>
              <th>Macro-Precision</th>
              <th>Macro-Recall</th>
              <th>Macro-F1</th>
              <th>ROC-AUC</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {results.models.map((m) => (
              <tr key={m.name}>
                <td>
                  <span className="model-name-cell">
                    <span className={`model-dot ${MODEL_DOT_CLASS[m.name]}`} />
                    {m.name}
                  </span>
                </td>
                <td>{m.training_context?.toLocaleString()}</td>
                <td>{pct(m.accuracy)}</td>
                <td>{pct(m.macro_precision)}</td>
                <td>{pct(m.macro_recall)}</td>
                <td>{m.macro_f1?.toFixed(3)}</td>
                <td>{m.roc_auc?.toFixed(3)}</td>
                <td className="hint">{m.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ModelComparisonChart models={results.models} />
      <CodeBlock code={CODE_SNIPPETS.model_comparison} />

      <div className="stat-card" style={{ marginTop: 20 }}>
        <h3>Computational Latency</h3>
        <div className="table-scroll">
          <table className="compare-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Fit / Training Time</th>
                <th>Inference (per sample)</th>
              </tr>
            </thead>
            <tbody>
              {results.models.map((m) => (
                <tr key={m.name}>
                  <td>
                    <span className="model-name-cell">
                      <span className={`model-dot ${MODEL_DOT_CLASS[m.name]}`} />
                      {m.name}
                    </span>
                  </td>
                  <td>{m.fit_time_seconds != null ? `${m.fit_time_seconds}s` : "—"}</td>
                  <td>{m.inference_ms_per_sample != null ? `${m.inference_ms_per_sample}ms` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="hint" style={{ marginTop: 10 }}>
          Measured on a Colab T4 GPU. TabFM's per-sample figure is amortized over a single large
          batched forward pass across the full 4,322-row test set (8.1 min total) — a single
          unbatched request (as in the Predict tab) doesn't get that batching benefit and is much
          slower per call, especially without a GPU.
        </p>
      </div>

      <div className="stat-card" style={{ marginTop: 20 }}>
        <h3>Pairwise Significance (McNemar's test)</h3>
        <div className="stat-grid" style={{ marginTop: 10, marginBottom: 10 }}>
          {sigs.map((sig) => (
            <div className="stat-tile" key={sig.comparison}>
              <div className="stat-tile-label">{sig.comparison}</div>
              <div className="stat-tile-value" style={{ fontSize: "1.05rem" }}>
                p = {sig.p_value.toFixed(4)}
              </div>
              <span className="sig-outcome" style={{ marginLeft: 0, marginTop: 6 }}>
                {sig.significant ? "Significant" : "Not Significant"}
              </span>
            </div>
          ))}
        </div>
        {sigs.map((sig) => (
          <p key={sig.comparison} style={{ marginTop: 6 }}>
            <strong>{sig.comparison}:</strong> {sig.interpretation}
          </p>
        ))}
        <CodeBlock code={CODE_SNIPPETS.mcnemar} />
      </div>

      {results.best_params && (
        <div className="stat-card">
          <h3>Best CatBoost Hyperparameters (grid search)</h3>
          <p className="hint">
            depth = {results.best_params.depth} &middot; learning_rate = {results.best_params.learning_rate}{" "}
            &middot; best CV macro-F1 = {results.best_params.best_cv_macro_f1.toFixed(3)}
          </p>
          <CodeBlock code={CODE_SNIPPETS.catboost_training} />
        </div>
      )}
    </div>
  );
}

function ContextScaling({ contextScaling, matched2000, shapImages, shapImagesAvailable }) {
  if (!contextScaling?.length) return null;

  const bySize = {};
  contextScaling.forEach((row) => {
    const key = row.context_size;
    bySize[key] = bySize[key] || { context_size: key };
    bySize[key][row.model] = row.accuracy;
  });
  const data = Object.values(bySize).sort((a, b) => a.context_size - b.context_size);
  const models = ["CatBoost", "TabPFN", "TabFM"];

  return (
    <div className="card">
      <SectionHead icon={ScaleIcon} title="Context-Size Scaling" />
      <p className="hint" style={{ marginBottom: 16 }}>
        Accuracy as in-context training data shrinks from the full 17,284-row training set down
        to 500 and 100 rows — TabFM was designed for small contexts and holds up far better than
        CatBoost or TabPFN as context shrinks.
      </p>
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e1e0d9" vertical={false} />
            <XAxis
              dataKey="context_size"
              scale="log"
              domain={["auto", "auto"]}
              tick={{ fill: "#52514e", fontSize: 12 }}
              axisLine={{ stroke: "#c3c2b7" }}
              tickLine={false}
              tickFormatter={(v) => v.toLocaleString()}
            />
            <YAxis domain={[0.5, 0.85]} tick={{ fill: "#898781", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e1e0d9", fontSize: 13 }} />
            <Legend wrapperStyle={{ fontSize: 13 }} />
            {models.map((m) => (
              <Line
                key={m}
                type="monotone"
                dataKey={m}
                stroke={MODEL_COLOR[m]}
                strokeWidth={2}
                dot={{ r: 4 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <CodeBlock code={CODE_SNIPPETS.context_scaling} />

      {matched2000?.length > 0 && (
        <div className="stat-card" style={{ marginTop: 20 }}>
          <h3>Matched 2,000-Row Context (apples-to-apples)</h3>
          <div className="table-scroll">
            <table className="compare-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Macro-F1</th>
                  <th>ROC-AUC</th>
                </tr>
              </thead>
              <tbody>
                {matched2000.map((m) => (
                  <tr key={m.model}>
                    <td>
                      <span className="model-name-cell">
                        <span className={`model-dot ${MODEL_DOT_CLASS[m.model]}`} />
                        {m.model}
                      </span>
                    </td>
                    <td>{pct(m.accuracy)}</td>
                    <td>{m.macro_f1?.toFixed(3)}</td>
                    <td>{m.roc_auc?.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <CodeBlock code={CODE_SNIPPETS.matched_2000_context} />

          {(shapImagesAvailable?.catboost_confusion_matrix_2000ctx ||
            shapImagesAvailable?.tabpfn_confusion_matrix_2000ctx ||
            shapImagesAvailable?.tabfm_confusion_matrix_2000ctx ||
            shapImagesAvailable?.matched_2000ctx_chart) && (
            <div className="shap-static-grid" style={{ marginTop: 16 }}>
              {shapImagesAvailable.matched_2000ctx_chart && (
                <figure>
                  <img src={`${API_URL}${shapImages.matched_2000ctx_chart}`} alt="Matched 2,000-row context comparison chart" />
                  <figcaption>Accuracy / Macro-F1 / ROC-AUC at 2,000-row context</figcaption>
                </figure>
              )}
              {shapImagesAvailable.catboost_confusion_matrix_2000ctx && (
                <figure>
                  <img src={`${API_URL}${shapImages.catboost_confusion_matrix_2000ctx}`} alt="CatBoost confusion matrix at 2000-row context" />
                  <figcaption>CatBoost — confusion matrix (2,000-row context)</figcaption>
                </figure>
              )}
              {shapImagesAvailable.tabpfn_confusion_matrix_2000ctx && (
                <figure>
                  <img src={`${API_URL}${shapImages.tabpfn_confusion_matrix_2000ctx}`} alt="TabPFN confusion matrix at 2000-row context" />
                  <figcaption>TabPFN — confusion matrix (2,000-row context)</figcaption>
                </figure>
              )}
              {shapImagesAvailable.tabfm_confusion_matrix_2000ctx && (
                <figure>
                  <img src={`${API_URL}${shapImages.tabfm_confusion_matrix_2000ctx}`} alt="TabFM confusion matrix at 2000-row context" />
                  <figcaption>TabFM — confusion matrix (2,000-row context)</figcaption>
                </figure>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ImageGallery({ shapImages, shapImagesAvailable }) {
  const [showCode, setShowCode] = useState(false);
  const labels = {
    catboost_shap_global: "SHAP global importance",
    catboost_shap_beeswarm: "SHAP beeswarm (High risk)",
    catboost_shap_waterfall: "SHAP waterfall (example patient)",
    catboost_confusion_matrix: "Confusion matrix",
    catboost_training_curve: "Training vs validation loss",
    tabpfn_shap_global: "SHAP global importance",
    tabpfn_shap_beeswarm: "SHAP beeswarm (High risk)",
    tabpfn_shap_waterfall: "SHAP waterfall (example patient)",
    tabpfn_confusion_matrix: "Confusion matrix",
    tabfm_shap_global: "SHAP global importance",
    tabfm_shap_beeswarm: "SHAP beeswarm (High risk)",
    tabfm_shap_waterfall: "SHAP waterfall (example patient)",
    tabfm_confusion_matrix: "Confusion matrix",
  };

  const snippetFor = {
    catboost_shap_global: "catboost_shap",
    catboost_shap_beeswarm: "catboost_shap",
    catboost_shap_waterfall: "catboost_shap",
    catboost_confusion_matrix: "catboost_confusion_matrix",
    catboost_training_curve: "catboost_training_curve",
    tabpfn_shap_global: "tabpfn_shap",
    tabpfn_shap_beeswarm: "tabpfn_shap",
    tabpfn_shap_waterfall: "tabpfn_shap",
    tabpfn_confusion_matrix: "tabpfn_training",
    tabfm_shap_global: "tabfm_shap",
    tabfm_shap_beeswarm: "tabfm_shap",
    tabfm_shap_waterfall: "tabfm_shap",
    tabfm_confusion_matrix: "tabfm_training",
  };

  const groups = [
    { title: "CatBoost", dot: "catboost", keys: ["catboost_shap_global", "catboost_shap_beeswarm", "catboost_shap_waterfall", "catboost_confusion_matrix", "catboost_training_curve"] },
    { title: "TabPFN", dot: "tabpfn", keys: ["tabpfn_shap_global", "tabpfn_shap_beeswarm", "tabpfn_shap_waterfall", "tabpfn_confusion_matrix"] },
    { title: "TabFM", dot: "tabfm", keys: ["tabfm_shap_global", "tabfm_shap_beeswarm", "tabfm_shap_waterfall", "tabfm_confusion_matrix"] },
  ];

  const anyAvailable = Object.values(shapImagesAvailable || {}).some(Boolean);
  if (!anyAvailable) {
    return (
      <div className="card">
        <SectionHead icon={ImageIcon} title="Reference Charts" />
        <p className="placeholder-note">
          No reference charts uploaded yet — drop the PNGs exported from Colab into
          backend/static/shap_reference/ and they'll appear here automatically.
        </p>
      </div>
    );
  }

  const renderFigure = (key, groupLabel) => {
    const snippet = CODE_SNIPPETS[snippetFor[key]];
    const img = <img src={`${API_URL}${shapImages[key]}`} alt={`${groupLabel} ${labels[key]}`} />;
    const caption = <figcaption>{labels[key]}</figcaption>;

    if (!showCode || !snippet) {
      return (
        <figure key={key}>
          {img}
          {caption}
        </figure>
      );
    }
    return (
      <div className="gallery-row" key={key}>
        <figure>
          {img}
          {caption}
        </figure>
        <pre className="code-block gallery-row-code">
          <code>{snippet}</code>
        </pre>
      </div>
    );
  };

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-title-row">
          <span className="section-icon">
            <ImageIcon />
          </span>
          <h2>Reference Charts (from Colab)</h2>
        </div>
        <button type="button" className="code-toggle" onClick={() => setShowCode((v) => !v)}>
          {showCode ? "Hide all code" : "Show code for all charts"}
        </button>
      </div>

      {groups.map((group) => {
        const available = group.keys.filter((k) => shapImagesAvailable[k]);
        if (available.length === 0) return null;
        return (
          <div className="gallery-group" key={group.title}>
            <div className="gallery-group-title">
              <span className={`model-dot ${group.dot}`} />
              {group.title}
            </div>
            <div className={showCode ? "gallery-code-list" : "shap-static-grid"}>
              {available.map((key) => renderFigure(key, group.title))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalysisTab() {
  const [summary, setSummary] = useState(null);
  const [results, setResults] = useState(null);
  const [meta, setMeta] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([fetchDatasetSummary(), fetchResults(), fetchMeta()])
      .then(([s, r, m]) => {
        setSummary(s);
        setResults(r);
        setMeta(m);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <ErrorBanner message={`Could not load analysis data: ${error}`} />;
  if (!summary || !results || !meta) {
    return (
      <div className="card">
        <Spinner label="Loading analysis…" />
      </div>
    );
  }

  return (
    <>
      <DatasetOverview summary={summary} />
      <CorrelationHeatmap summary={summary} />
      <ResultsSection results={results} />
      <ContextScaling
        contextScaling={results.context_scaling}
        matched2000={results.matched_2000_context}
        shapImages={meta.shap_images}
        shapImagesAvailable={meta.shap_images_available}
      />
      <ImageGallery shapImages={meta.shap_images} shapImagesAvailable={meta.shap_images_available} />
    </>
  );
}
