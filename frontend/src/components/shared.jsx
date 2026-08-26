import { useEffect, useState } from "react";
import { AlertCircleIcon, AlertTriangleIcon, CheckCircleIcon } from "../icons";

const CLASS_ORDER = ["Low", "Moderate", "High"];

const RISK_ICON = {
  Low: CheckCircleIcon,
  Moderate: AlertTriangleIcon,
  High: AlertCircleIcon,
};

export function RiskBadge({ prediction }) {
  const Icon = RISK_ICON[prediction];
  return (
    <span className={`risk-badge ${prediction}`}>
      {Icon && <Icon />}
      {prediction} risk
    </span>
  );
}

export function ConfidenceBars({ confidence }) {
  return (
    <div>
      {CLASS_ORDER.map((cls) => {
        const pct = Math.round((confidence?.[cls] ?? 0) * 100);
        return (
          <div className="conf-row" key={cls}>
            <span className="conf-label">{cls}</span>
            <span className="conf-bar-bg">
              <span className={`conf-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
            </span>
            <span className="conf-pct">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}

export function Spinner({ label }) {
  return (
    <div className="loading">
      <span className="spinner" /> {label}
    </div>
  );
}

export function TimedSpinner({ label, expectedSeconds, explainer }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 500);
    return () => clearInterval(id);
  }, []);

  const pct = expectedSeconds ? Math.min(96, (elapsed / expectedSeconds) * 100) : null;

  return (
    <div className="timed-loading">
      <div className="loading">
        <span className="spinner" /> {label}
        <span className="loading-elapsed">{elapsed}s elapsed</span>
      </div>
      {pct !== null && (
        <div className="progress-track">
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
      )}
      {explainer && <p className="placeholder-note">{explainer}</p>}
    </div>
  );
}

export function CodeBlock({ code }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="code-block-wrap">
      <button type="button" className="code-toggle" onClick={() => setOpen(true)}>
        View code
      </button>
      {open && (
        <div className="code-panel-overlay" onClick={() => setOpen(false)}>
          <div className="code-panel" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="modal-close" onClick={() => setOpen(false)} aria-label="Close">
              &times;
            </button>
            <pre className="code-block code-panel-block">
              <code>{code}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

export function ErrorBanner({ message }) {
  return (
    <div className="banner error">
      <AlertCircleIcon />
      <span>{message}</span>
    </div>
  );
}

export function WarnBanner({ warnings }) {
  if (!warnings?.length) return null;
  return (
    <div className="banner warn">
      <AlertTriangleIcon />
      <div>
        <strong>Note</strong>
        <ul>
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
