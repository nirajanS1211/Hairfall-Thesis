import { useEffect, useRef, useState } from "react";
import { fetchSiteSettings } from "./api";
import AnalysisTab from "./components/AnalysisTab";
import PredictTab from "./components/PredictTab";
import SettingsModal from "./components/SettingsModal";
import { ChartIcon, FormIcon, GraduationCapIcon } from "./icons";
import "./App.css";

const DEFAULT_SETTINGS = {
  university_line: "Tribhuvan University · Central Department of CSIT · M.Sc. CSIT Dissertation",
  submitted_by: "Nirajan Shahi · Roll No. 49/079",
  supervised_by: "Asst. Prof. Jagadish Bhatta",
};

const LONG_PRESS_MS = 700;

export default function App() {
  const [tab, setTab] = useState("predict");
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [token, setToken] = useState(() => localStorage.getItem("hf_token"));
  const [email, setEmail] = useState(() => localStorage.getItem("hf_email"));
  const [modalOpen, setModalOpen] = useState(false);
  const pressTimer = useRef(null);

  useEffect(() => {
    fetchSiteSettings()
      .then((s) => setSettings(s))
      .catch(() => {
        /* keep defaults if the API isn't reachable yet */
      });
  }, []);

  function startPress() {
    pressTimer.current = setTimeout(() => setModalOpen(true), LONG_PRESS_MS);
  }

  function cancelPress() {
    if (pressTimer.current) {
      clearTimeout(pressTimer.current);
      pressTimer.current = null;
    }
  }

  function handleAuthed(newToken, newEmail) {
    localStorage.setItem("hf_token", newToken);
    localStorage.setItem("hf_email", newEmail);
    setToken(newToken);
    setEmail(newEmail);
  }

  function handleLogout() {
    localStorage.removeItem("hf_token");
    localStorage.removeItem("hf_email");
    setToken(null);
    setEmail(null);
    setModalOpen(false);
  }

  return (
    <div className="shell">
      <header className="hero">
        <div className="hero-kicker">
          <GraduationCapIcon />
          {settings.university_line}
        </div>
        <div
          className="hero-title-row"
          onMouseDown={startPress}
          onMouseUp={cancelPress}
          onMouseLeave={cancelPress}
          onTouchStart={startPress}
          onTouchEnd={cancelPress}
        >
          <h1>
            Comparative Benchmarking of CatBoost, TabPFN, and TabFM for Explainable Multi-Tier
            Hair Fall Risk Stratification
          </h1>
          <p className="hero-sub">
            A live, three-way comparison of CatBoost, TabPFN, and Google Research's TabFM for
            multi-tier hair fall risk classification (Low / Moderate / High), with SHAP-based
            explainability on structured clinical and lifestyle data.
          </p>
        </div>
        <div className="hero-meta">
          <div className="hero-meta-item">
            <span className="hero-meta-label">Submitted by</span>
            <span className="hero-meta-value">{settings.submitted_by}</span>
          </div>
          <div className="hero-meta-item">
            <span className="hero-meta-label">Supervised by</span>
            <span className="hero-meta-value">{settings.supervised_by}</span>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={tab === "predict" ? "active" : ""} onClick={() => setTab("predict")}>
          <FormIcon />
          Predict
        </button>
        <button className={tab === "analysis" ? "active" : ""} onClick={() => setTab("analysis")}>
          <ChartIcon />
          Analysis
        </button>
      </nav>

      {tab === "predict" ? <PredictTab /> : <AnalysisTab />}

      {modalOpen && (
        <SettingsModal
          open={modalOpen}
          onClose={() => setModalOpen(false)}
          token={token}
          email={email}
          settings={settings}
          onAuthed={handleAuthed}
          onSaved={setSettings}
          onLogout={handleLogout}
        />
      )}
    </div>
  );
}
