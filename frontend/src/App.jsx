import { useState } from "react";
import AnalysisTab from "./components/AnalysisTab";
import PredictTab from "./components/PredictTab";
import { ChartIcon, FormIcon, GraduationCapIcon } from "./icons";
import "./App.css";

export default function App() {
  const [tab, setTab] = useState("predict");

  return (
    <div className="shell">
      <header className="hero">
        <div className="hero-kicker">
          <GraduationCapIcon />
          Tribhuvan University &middot; Central Department of CSIT &middot; M.Sc. CSIT Dissertation
        </div>
        <h1>
          Comparative Benchmarking of CatBoost, TabPFN, and TabFM for Explainable Multi-Tier
          Hair Fall Risk Stratification
        </h1>
        <p className="hero-sub">
          A live, three-way comparison of CatBoost, TabPFN, and Google Research's TabFM for
          multi-tier hair fall risk classification (Low / Moderate / High), with SHAP-based
          explainability on structured clinical and lifestyle data.
        </p>
        <div className="hero-meta">
          <div className="hero-meta-item">
            <span className="hero-meta-label">Submitted by</span>
            <span className="hero-meta-value">Nirajan Shahi &middot; Roll No. 49/079</span>
          </div>
          <div className="hero-meta-item">
            <span className="hero-meta-label">Supervised by</span>
            <span className="hero-meta-value">Asst. Prof. Jagadish Bhatta</span>
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
    </div>
  );
}
