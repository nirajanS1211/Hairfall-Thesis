const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const path = require("path");

const T = "/Users/midas/Desktop/Hairfall-Thesis/thesis";
const OUT = T + "/final/Hairfall_Thesis_Presentation.pptx";
const IMG = {
  logo: T + "/final_src/assets/lincoln_logo.jpeg",
  cmPFN: T + "/Colab Work/Step_06_TabPFN/tabpfn_confusion_matrix.png",
  shapCB: T + "/Colab Work/Step_08a_CatBoost_SHAP/catboost_shap_global_importance.png",
  beeCB: T + "/Colab Work/Step_08a_CatBoost_SHAP/catboost_shap_beeswarm_high.png",
};

// ---------- palette & type ----------
const DARK = "1B1F2A", RED = "C8102E", INK = "1B1F2A", MUTED = "5B6170", SOFT = "F2F3F5", WHITE = "FFFFFF";
const CB = "1F4E9C", PFN = "C05A00", FM = "2A7F3F";
const HF = "Cambria", BF = "Calibri";
const W = 13.333, H = 7.5, M = 0.6;

async function icon(Comp, color = "FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Comparative Benchmarking of CatBoost, TabPFN and TabFM for Explainable Multi-Tier Hair Fall Risk Stratification";
  pres.author = "Krishna Gautam";

  const ic = {};
  const need = {
    flask: fa.FaFlask, db: fa.FaDatabase, brain: fa.FaBrain, chart: fa.FaChartLine, search: fa.FaSearch,
    balance: fa.FaBalanceScale, clock: fa.FaClock, bug: fa.FaBug, check: fa.FaCheck, warn: fa.FaExclamationTriangle,
    tree: fa.FaTree, bolt: fa.FaBolt, layer: fa.FaLayerGroup, eye: fa.FaEye, question: fa.FaQuestion,
    list: fa.FaListOl, user: fa.FaUserMd, book: fa.FaBookOpen, road: fa.FaRoad, cogs: fa.FaCogs,
  };
  for (const [k, C] of Object.entries(need)) ic[k] = await icon(C);

  // ---------- helpers ----------
  let n = 0;
  function base(dark = false) {
    const s = pres.addSlide();
    n += 1;
    s.background = { color: dark ? DARK : WHITE };
    if (n > 1) s.slideNumber = { x: W - 0.9, y: H - 0.45, w: 0.5, h: 0.3, fontFace: BF, fontSize: 10, color: dark ? "B8BCC6" : MUTED, align: "right" };
    return s;
  }
  function title(s, t, sub) {
    s.addText(t, { x: M, y: 0.4, w: W - 2 * M, h: 0.75, fontFace: HF, fontSize: 32, bold: true, color: INK, margin: 0, isTextBox: true });
    if (sub) s.addText(sub, { x: M, y: 1.12, w: W - 2 * M, h: 0.4, fontFace: BF, fontSize: 15, color: MUTED, italic: true, margin: 0, isTextBox: true });
  }
  function dot(s, key, x, y, d = 0.62, fill = RED) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
    const p = d * 0.26;
    s.addImage({ data: ic[key], x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
  }
  function card(s, x, y, w, h, fill = SOFT) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
  }
  function text(s, t, o) {
    s.addText(t, Object.assign({ fontFace: BF, fontSize: 15, color: INK, margin: 0, valign: "top", isTextBox: true }, o));
  }
  function bullets(s, items, o) {
    const arr = items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }));
    s.addText(arr, Object.assign({ fontFace: BF, fontSize: 16, color: INK, margin: 0, valign: "top", isTextBox: true }, o));
  }

  // ================= 1. Title =================
  let s = base(true);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 0.55, w: 3.1, h: 1.27, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.06 });
  s.addImage({ path: IMG.logo, x: M + 0.1, y: 0.63, w: 2.9, h: 1.11 });
  text(s, "MCS Thesis Defence", { x: M, y: 2.05, w: 8, h: 0.4, fontSize: 16, color: "F2A0AB", bold: true });
  s.addText("Comparative Benchmarking of CatBoost, TabPFN and TabFM for Explainable Multi-Tier Hair Fall Risk Stratification",
    { x: M, y: 2.5, w: 11.4, h: 1.9, fontFace: HF, fontSize: 36, bold: true, color: WHITE, margin: 0, valign: "top", isTextBox: true });
  text(s, [
    { text: "Krishna Gautam", options: { bold: true, fontSize: 20, color: WHITE, breakLine: true } },
    { text: "Supervisor: Rabin Shrestha", options: { fontSize: 16, color: "D5D8DF", breakLine: true } },
    { text: "Master of Computer Science (MCS)", options: { fontSize: 16, color: "D5D8DF", breakLine: true } },
    { text: "Lincoln International College of Management & IT  ·  Lincoln University College", options: { fontSize: 16, color: "D5D8DF" } },
  ], { x: M, y: 4.75, w: 11.5, h: 1.8, paraSpaceAfter: 4 });
  s.addNotes("Good morning. My thesis compares three machine learning models for predicting hair fall risk in three levels, Low, Moderate and High, and explains their predictions with SHAP. One model is a tuned gradient-boosted tree, CatBoost; the other two, TabPFN and TabFM, are new tabular foundation models that need no training.");

  // ================= 2. Outline =================
  s = base();
  title(s, "Outline");
  const outline = ["Background & problem", "Research questions & objectives", "Literature gap", "Methodology & data",
    "Results", "Explainability (SHAP)", "Practical costs", "Conclusion & future work"];
  outline.forEach((t, i) => {
    const col = i < 4 ? 0 : 1, row = i % 4;
    const x = M + col * 6.2, y = 1.6 + row * 1.3;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.75, h: 0.75, fill: { color: i === 0 ? RED : DARK }, line: { color: i === 0 ? RED : DARK } });
    text(s, String(i + 1), { x, y, w: 0.75, h: 0.75, fontFace: HF, fontSize: 22, bold: true, color: WHITE, align: "center", valign: "middle" });
    text(s, t, { x: x + 1.0, y, w: 4.9, h: 0.75, fontSize: 20, valign: "middle" });
  });
  s.addNotes("The talk follows the thesis chapters: problem, questions, related work, method, results, explanations, costs, and conclusions.");

  // ================= 3. Background =================
  s = base();
  title(s, "Why hair fall risk?", "Many small factors add up — no single test predicts it");
  const factors = [["Nutrition", "iron · protein · vitamin D · calcium"], ["Stress & sleep", "stress level · late sleep · disturbance"],
    ["Health & heredity", "liver enzyme ALT · anaemia · family history"], ["Lifestyle", "chemical treatments · hard water"]];
  factors.forEach(([h, d], i) => {
    const y = 1.8 + i * 1.18;
    dot(s, ["flask", "brain", "user", "layer"][i], M, y, 0.7);
    text(s, h, { x: M + 0.95, y: y - 0.02, w: 5.2, h: 0.38, fontSize: 18, bold: true });
    text(s, d, { x: M + 0.95, y: y + 0.36, w: 5.2, h: 0.35, fontSize: 14, color: MUTED });
  });
  card(s, 7.3, 1.8, 5.4, 4.6, DARK);
  text(s, "Today", { x: 7.7, y: 2.1, w: 4.6, h: 0.4, fontSize: 16, bold: true, color: "F2A0AB" });
  bullets(s, ["Self-reported history, late clinical check", "Subjective and hard to access", "Data are tabular — ideal for machine learning"],
    { x: 7.7, y: 2.6, w: 4.7, h: 1.9, fontSize: 17, color: WHITE });
  text(s, "Goal: an accurate and explainable risk tier — Low, Moderate or High", { x: 7.7, y: 4.75, w: 4.7, h: 1.3, fontSize: 18, bold: true, color: WHITE });
  s.addNotes("Hair fall comes from many interacting factors: nutrition, stress and sleep, health and heredity, and lifestyle. Assessment today relies on self-report and late examination. These factors are recorded as tabular data, which is where machine learning works well.");

  // ================= 4. Problem =================
  s = base();
  title(s, "Problem statement", "Three gaps in existing work");
  const gaps = [
    ["balance", "Conflicting evidence", "Ensembles best in one study, Random Forest beats CatBoost in another — no clear model choice."],
    ["brain", "Foundation models untested", "TabPFN and TabFM predict without training, but were never tested on hair fall data."],
    ["eye", "Black-box predictions", "Accurate models are hard to explain — clinicians cannot check the reason."],
  ];
  gaps.forEach(([k, h, d], i) => {
    const x = M + i * 4.1, w = 3.8;
    card(s, x, 1.85, w, 3.55);
    dot(s, k, x + 0.35, 2.15, 0.8);
    text(s, h, { x: x + 0.35, y: 3.15, w: w - 0.7, h: 0.8, fontFace: HF, fontSize: 20, bold: true });
    text(s, d, { x: x + 0.35, y: 3.95, w: w - 0.7, h: 1.3, fontSize: 15, color: MUTED });
  });
  card(s, M, 5.7, W - 2 * M, 0.95, DARK);
  text(s, [{ text: "This study:  ", options: { bold: true, color: "F2A0AB" } },
    { text: "a fair benchmark of CatBoost, TabPFN and TabFM on the same data — with SHAP for every model.", options: { color: WHITE } }],
    { x: M + 0.35, y: 5.7, w: W - 2 * M - 0.7, h: 0.95, fontSize: 17, valign: "middle" });
  s.addNotes("First, earlier studies disagree on which model is best. Second, the new zero-shot tabular foundation models have not been tested on this problem. Third, accurate models are opaque, which limits their use in health.");

  // ================= 5. RQ & objectives =================
  s = base();
  title(s, "Research questions → objectives", "General objective: benchmark CatBoost, TabPFN and TabFM for explainable hair fall risk stratification");
  const rq = [["Performance", "Can zero-shot models match a tuned CatBoost?", "Compare accuracy, macro-F1, ROC-AUC + McNemar test"],
    ["Data efficiency", "How does training size change results?", "Retrain with 100, 500, 2,000 rows"],
    ["Explainability", "Which features drive predictions?", "SHAP for all three models"],
    ["Practicality", "What do the models cost to run?", "Runtime and implementation issues"]];
  text(s, "Question", { x: 3.5, y: 1.75, w: 4.4, h: 0.35, fontSize: 13, bold: true, color: MUTED });
  text(s, "Specific objective", { x: 8.2, y: 1.75, w: 4.4, h: 0.35, fontSize: 13, bold: true, color: MUTED });
  rq.forEach(([k, q, o], i) => {
    const y = 2.2 + i * 1.18;
    card(s, M, y, W - 2 * M, 1.0);
    s.addShape(pres.shapes.OVAL, { x: M + 0.2, y: y + 0.2, w: 0.6, h: 0.6, fill: { color: RED }, line: { color: RED } });
    text(s, String(i + 1), { x: M + 0.2, y: y + 0.2, w: 0.6, h: 0.6, fontFace: HF, fontSize: 18, bold: true, color: WHITE, align: "center", valign: "middle" });
    text(s, k, { x: M + 1.0, y, w: 1.8, h: 1.0, fontSize: 16, bold: true, valign: "middle" });
    text(s, q, { x: 3.5, y, w: 4.4, h: 1.0, fontSize: 15, valign: "middle" });
    text(s, o, { x: 8.2, y, w: 4.4, h: 1.0, fontSize: 15, color: MUTED, valign: "middle" });
  });
  s.addNotes("Four research questions, each with one specific objective: performance, data efficiency, explainability and practical cost.");

  // ================= 6. Literature =================
  s = base();
  title(s, "What the literature says", "32 sources reviewed");
  const lit = [["tree", "Tuned trees", "Gradient boosting (XGBoost, LightGBM, CatBoost) is still the strong baseline on tabular data."],
    ["bolt", "Tabular foundation models", "TabPFN (2023, 2025) and TabFM (2026) predict in one forward pass — no tuning."],
    ["eye", "SHAP", "Shapley values explain any model, so different models can be compared."],
    ["search", "Hair loss studies", "Classical models, conflicting results, few explanations."]];
  lit.forEach(([k, h, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.15, y = 1.85 + row * 1.75;
    dot(s, k, x, y + 0.05, 0.7);
    text(s, h, { x: x + 0.95, y, w: 4.9, h: 0.4, fontSize: 18, bold: true });
    text(s, d, { x: x + 0.95, y: y + 0.42, w: 4.9, h: 1.1, fontSize: 15, color: MUTED });
  });
  card(s, M, 5.55, W - 2 * M, 1.05, DARK);
  text(s, [{ text: "Gap:  ", options: { bold: true, color: "F2A0AB" } },
    { text: "no study compares two tabular foundation models with a tuned CatBoost on hair fall data, with SHAP for all.", options: { color: WHITE } }],
    { x: M + 0.35, y: 5.55, w: W - 2 * M - 0.7, h: 1.05, fontSize: 17, valign: "middle" });
  s.addNotes("Tuned boosted trees are still the reference on tabular data. Tabular foundation models are the new alternative. SHAP lets us explain any model. Hair loss studies used classical models and disagree. The gap is a fair comparison with explanations.");

  // ================= 7. Methodology =================
  s = base();
  title(s, "Methodology", "Quantitative, experimental benchmark — same data, split and metrics for every model");
  const steps = [["db", "Data", "21,606 records\n20 features"], ["cogs", "Preprocess", "drop IDs\nencode gender"],
    ["layer", "Split", "80 / 20 stratified\nseed 42"], ["brain", "Models", "CatBoost · TabPFN\n· TabFM"],
    ["chart", "Evaluate", "metrics · McNemar\ncontext sizes"], ["eye", "Explain", "SHAP\nfor all models"]];
  const sw = 1.85, gap = (W - 2 * M - 6 * sw) / 5;
  steps.forEach(([k, h, d], i) => {
    const x = M + i * (sw + gap), y = 2.05;
    card(s, x, y, sw, 3.5, i === 3 ? DARK : SOFT);
    dot(s, k, x + (sw - 0.8) / 2, y + 0.35, 0.8);
    text(s, h, { x: x + 0.1, y: y + 1.45, w: sw - 0.2, h: 0.45, fontSize: 19, bold: true, align: "center", color: i === 3 ? WHITE : INK });
    text(s, d, { x: x + 0.1, y: y + 2.05, w: sw - 0.2, h: 1.2, fontSize: 15, align: "center", color: i === 3 ? "D5D8DF" : MUTED });
    if (i < 5) s.addText("›", { x: x + sw, y: y + 1.2, w: gap, h: 0.6, fontFace: BF, fontSize: 30, bold: true, color: RED, align: "center", valign: "middle", margin: 0, isTextBox: true });
  });
  text(s, "Tools: Python · scikit-learn · catboost · tabpfn · tabfm · shap · statsmodels  |  Kaggle & Google Colab, NVIDIA T4 GPU",
    { x: M, y: 6.0, w: W - 2 * M, h: 0.4, fontSize: 14, color: MUTED, align: "center" });
  s.addNotes("The data were split once into training and test sets. CatBoost was tuned; TabPFN and TabFM received the training rows as context. All models were evaluated on the same test set, compared with McNemar's test, retrained with smaller contexts, and explained with SHAP.");

  // ================= 8. Dataset =================
  s = base();
  title(s, "Dataset", "Assembled from two public datasets (Kaggle, Mendeley) and adjusted with domain knowledge");
  const stats = [["21,606", "records"], ["20", "predictors"], ["3", "risk tiers"]];
  stats.forEach(([v, l], i) => {
    const y = 1.85 + i * 1.45;
    text(s, v, { x: M, y, w: 3.2, h: 0.85, fontFace: HF, fontSize: 48, bold: true, color: RED });
    text(s, l, { x: M, y: y + 0.82, w: 3.2, h: 0.4, fontSize: 16, color: MUTED });
  });
  s.addChart(pres.charts.BAR, [{ name: "Records", labels: ["Low", "Moderate", "High"], values: [9723, 7562, 4321] }], {
    x: 4.1, y: 1.75, w: 4.6, h: 4.6, barDir: "col", chartColors: ["2E7D32", "E0A100", RED], varyColors: true,
    showTitle: true, title: "Records per risk tier", titleFontFace: BF, titleFontSize: 14, titleColor: INK,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: INK, dataLabelFormatCode: "#,##0",
    catAxisLabelFontSize: 13, catAxisLabelColor: INK, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  });
  const groups = [["Biomarkers", "iron, protein, vitamin D, calcium, manganese, ALT, body water, stress score"],
    ["Clinical & lifestyle flags", "anaemia, chronic illness, stress, sleep, chemicals, hard water"],
    ["Demographics", "age, gender, family history"]];
  groups.forEach(([h, d], i) => {
    const y = 1.85 + i * 1.5;
    card(s, 9.05, y, 3.7, 1.3);
    text(s, h, { x: 9.25, y: y + 0.15, w: 3.3, h: 0.35, fontSize: 15, bold: true });
    text(s, d, { x: 9.25, y: y + 0.52, w: 3.3, h: 0.75, fontSize: 12.5, color: MUTED });
  });
  s.addNotes("21,606 records, 20 predictors, three tiers. The classes are unequal: 45% Low, 35% Moderate, 20% High, so macro-averaged metrics were used. Important: the dataset is constructed, not a clinical registry, so results are a benchmark of models, not a diagnostic tool.");

  // ================= 9. Models =================
  s = base();
  title(s, "Three models, two philosophies", "Tuned training vs. zero-shot prediction");
  const models = [[CB, "CatBoost", "Gradient-boosted trees", ["Grid search: depth × learning rate", "5-fold stratified CV", "Best: depth 4, lr 0.1", "17,284 training rows"]],
    [PFN, "TabPFN", "Pretrained transformer", ["No training, no tuning", "Training rows given as context", "One forward pass", "17,284 context rows"]],
    [FM, "TabFM", "Google, 2026 · row + column attention", ["No training, no tuning", "Single ensemble member", "Slow at large context", "500 context rows"]]];
  models.forEach(([c, h, sub, pts], i) => {
    const x = M + i * 4.1, w = 3.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.85, w, h: 1.1, fill: { color: c }, line: { color: c }, rectRadius: 0.08 });
    text(s, h, { x: x + 0.3, y: 1.9, w: w - 0.6, h: 0.55, fontFace: HF, fontSize: 24, bold: true, color: WHITE });
    text(s, sub, { x: x + 0.3, y: 2.45, w: w - 0.6, h: 0.4, fontSize: 13, color: WHITE });
    card(s, x, 3.1, w, 3.3);
    bullets(s, pts, { x: x + 0.3, y: 3.4, w: w - 0.6, h: 2.9, fontSize: 18 });
  });
  s.addNotes("CatBoost was tuned by grid search with cross-validation. TabPFN and TabFM were not tuned at all — that asymmetry is the point of the study. TabFM used 500 context rows because it became too slow with more.");

  // ================= 10. Overall results =================
  s = base();
  title(s, "Result 1 — performance is almost identical", "Held-out test set: 4,322 records");
  const acc = [[CB, "CatBoost", "78.51%", "Macro-F1 0.776 · AUC 0.919"], [PFN, "TabPFN", "78.57%", "Macro-F1 0.779 · AUC 0.923"],
    [FM, "TabFM", "77.88%", "Macro-F1 0.772 · AUC 0.918"]];
  acc.forEach(([c, h, v, d], i) => {
    const x = M + i * 4.1, w = 3.8;
    card(s, x, 1.85, w, 2.7);
    s.addShape(pres.shapes.OVAL, { x: x + 0.35, y: 2.15, w: 0.3, h: 0.3, fill: { color: c }, line: { color: c } });
    text(s, h, { x: x + 0.8, y: 2.1, w: w - 1.1, h: 0.4, fontSize: 18, bold: true });
    text(s, v, { x: x + 0.35, y: 2.6, w: w - 0.7, h: 1.0, fontFace: HF, fontSize: 54, bold: true, color: c });
    text(s, d, { x: x + 0.35, y: 3.75, w: w - 0.7, h: 0.4, fontSize: 14, color: MUTED });
  });
  card(s, M, 4.85, W - 2 * M, 1.55, DARK);
  dot(s, "balance", M + 0.35, 5.3, 0.7);
  text(s, [{ text: "McNemar test: no significant difference ", options: { bold: true, color: WHITE, breakLine: true } },
    { text: "p = 0.90 · 0.20 · 0.11  —  TabPFN matched tuned CatBoost with zero tuning; TabFM used < 3% of the data.", options: { color: "D5D8DF", fontSize: 15 } }],
    { x: M + 1.3, y: 4.85, w: W - 2 * M - 1.6, h: 1.55, fontSize: 18, valign: "middle" });
  s.addNotes("All three reach about 78% accuracy, far above the 45% of always predicting Low. McNemar's test found no significant difference for any pair. Careful wording: no difference was detected — that is not proof of equivalence.");

  // ================= 11. Errors =================
  s = base();
  title(s, "Where the models make mistakes", "Errors stay between neighbouring tiers");
  s.addImage({ path: IMG.cmPFN, x: M, y: 1.6, w: 5.6, h: 4.67 });
  text(s, "TabPFN confusion matrix (others look the same)", { x: M, y: 6.35, w: 5.6, h: 0.3, fontSize: 11, color: MUTED, italic: true });
  const errs = [["check", "Low ↔ High almost never", "only 1–3 of ~930 errors"], ["warn", "Moderate is hardest", "F1 = 0.71 for every model"],
    ["warn", "High often under-rated", "27–31% of High predicted as Moderate"], ["check", "Ordinal agreement", "Quadratic weighted kappa ≈ 0.81"]];
  errs.forEach(([k, h, d], i) => {
    const y = 1.85 + i * 1.12;
    dot(s, k, 6.9, y, 0.62, k === "warn" ? "B7791F" : "2E7D32");
    text(s, h, { x: 7.75, y: y - 0.05, w: 5.0, h: 0.4, fontSize: 18, bold: true });
    text(s, d, { x: 7.75, y: y + 0.35, w: 5.0, h: 0.4, fontSize: 15, color: MUTED });
  });
  s.addNotes("Almost every error is to a neighbouring tier. Moderate is hardest because it borders both others. High-risk records are often under-rated as Moderate, so a Moderate prediction should not exclude high risk.");

  // ================= 12. Context scaling =================
  s = base();
  title(s, "Result 2 — foundation models need far less data", "Accuracy (%) when models get only part of the training data");
  s.addChart(pres.charts.LINE, [
    { name: "CatBoost", labels: ["100", "500", "2,000*", "17,284"], values: [60.53, 69.64, 74.40, 78.51] },
    { name: "TabPFN", labels: ["100", "500", "2,000*", "17,284"], values: [71.54, 77.65, 76.20, 78.57] },
    { name: "TabFM", labels: ["100", "500", "2,000*", "17,284"], values: [74.41, 77.88, 77.40, null] },
  ], {
    x: M, y: 1.65, w: 7.6, h: 4.9, chartColors: [CB, PFN, FM], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
    showLegend: true, legendPos: "b", legendFontSize: 13, legendColor: INK,
    showValue: false,
    valAxisMinVal: 55, valAxisMaxVal: 82, valAxisLabelFontSize: 12, valAxisLabelColor: MUTED, catAxisLabelFontSize: 13, catAxisLabelColor: INK,
    valGridLine: { color: "E3E5E9", size: 0.5 }, catGridLine: { style: "none" }, showCatAxisTitle: true, catAxisTitle: "Training rows", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED,
  });
  text(s, "* 2,000-row run tested on a 500-record subset. TabFM not run at full size.", { x: M, y: 6.6, w: 7.6, h: 0.3, fontSize: 11, color: MUTED, italic: true });
  card(s, 8.7, 1.8, 4.05, 2.2, DARK);
  text(s, "+11 to +14", { x: 9.0, y: 2.0, w: 3.5, h: 0.9, fontFace: HF, fontSize: 40, bold: true, color: WHITE });
  text(s, "points over CatBoost with only 100 rows", { x: 9.0, y: 2.95, w: 3.5, h: 0.8, fontSize: 15, color: "D5D8DF" });
  card(s, 8.7, 4.25, 4.05, 2.2);
  text(s, "≥ 5× less data", { x: 9.0, y: 4.45, w: 3.5, h: 0.8, fontFace: HF, fontSize: 32, bold: true, color: RED });
  text(s, "to pass 70% accuracy; the gap closes at full data", { x: 9.0, y: 5.3, w: 3.5, h: 0.9, fontSize: 15, color: MUTED });
  s.addNotes("With 100 rows CatBoost reaches 61%, TabPFN 72% and TabFM 74%. The gap narrows as data grows and closes at full size. So the benefit of foundation models is greatest when labelled data is scarce. TabFM versus TabPFN ordering is not reliable.");

  // ================= 13. SHAP =================
  s = base();
  title(s, "Result 3 — the same features drive every model", "SHAP explanations agree across all three models");
  s.addImage({ path: IMG.shapCB, x: M, y: 1.55, w: 4.2, h: 4.99 });
  text(s, "CatBoost global SHAP importance", { x: M, y: 6.6, w: 4.4, h: 0.3, fontSize: 11, color: MUTED, italic: true });
  text(s, "Top 7 in all three models", { x: 5.4, y: 1.75, w: 3.6, h: 0.4, fontSize: 17, bold: true });
  const top = ["Iron", "Stress level", "Total protein", "Vitamin D", "ALT (liver)", "Calcium", "Manganese"];
  top.forEach((t, i) => {
    const y = 2.3 + i * 0.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.4, y, w: 3.4, h: 0.48, fill: { color: SOFT }, line: { color: SOFT }, rectRadius: 0.06 });
    text(s, t, { x: 5.6, y, w: 3.0, h: 0.48, fontSize: 15, valign: "middle" });
  });
  card(s, 9.15, 1.75, 3.6, 2.25, "FBE9EC");
  text(s, "▲ Raise risk", { x: 9.4, y: 1.95, w: 3.2, h: 0.4, fontSize: 17, bold: true, color: RED });
  text(s, "high stress level, high ALT, every risk flag", { x: 9.4, y: 2.4, w: 3.1, h: 1.4, fontSize: 15 });
  card(s, 9.15, 4.2, 3.6, 2.25, "E8F3EA");
  text(s, "▼ Lower risk", { x: 9.4, y: 4.4, w: 3.2, h: 0.4, fontSize: 17, bold: true, color: "2E7D32" });
  text(s, "high iron, protein, vitamin D, calcium, manganese", { x: 9.4, y: 4.85, w: 3.1, h: 1.4, fontSize: 15 });
  s.addNotes("The same seven biomarkers lead in all models, and they are the ones most correlated with risk in the data. Directions agree too. Because the dataset was constructed, this shows the models recovered the built-in relationships — not a new clinical discovery. The foundation-model SHAP used only 20–30 records.");

  // ================= 14. Costs =================
  s = base();
  title(s, "Result 4 — no tuning ≠ cheap to run", "TabFM prediction time grows steeply with context size");
  const rt = [["0.11 s", "per record", "500-row context"], ["1.8 s", "per record", "2,000-row context"], ["did not finish", "", "17,284-row context"]];
  rt.forEach(([v, u, l], i) => {
    const x = M + i * 2.75, w = 2.5;
    card(s, x, 2.0, w, 2.5, i === 2 ? DARK : SOFT);
    text(s, v, { x: x + 0.2, y: 2.25, w: w - 0.4, h: 0.8, fontFace: HF, fontSize: i === 2 ? 24 : 36, bold: true, color: i === 2 ? WHITE : RED, valign: "middle" });
    text(s, u, { x: x + 0.2, y: 3.1, w: w - 0.4, h: 0.35, fontSize: 14, color: MUTED });
    text(s, l, { x: x + 0.2, y: 3.65, w: w - 0.4, h: 0.5, fontSize: 14, bold: true, color: i === 2 ? "D5D8DF" : INK });
  });
  text(s, "4× more context → ~16× slower per record", { x: M, y: 4.8, w: 8.0, h: 0.45, fontSize: 17, bold: true, color: RED });
  text(s, "Software problems solved", { x: 9.2, y: 2.0, w: 3.6, h: 0.4, fontSize: 17, bold: true });
  const probs = [["bug", "SHAP Permutation → numba error; used KernelExplainer"], ["bug", "TabFM crashed on 1-row input; padded to 2 rows"],
    ["bug", "TabPFN checkpoint load; patched torch.load"]];
  probs.forEach(([k, t], i) => {
    const y = 2.6 + i * 1.35;
    dot(s, k, 9.2, y, 0.55, DARK);
    text(s, t, { x: 9.95, y: y - 0.05, w: 2.85, h: 1.1, fontSize: 15 });
  });
  card(s, M, 5.45, 8.0, 1.3);
  text(s, "Choice depends on data size and number of predictions: CatBoost is cheap to run once trained; foundation models need no training but pay at every prediction.",
    { x: M + 0.3, y: 5.45, w: 7.4, h: 1.3, fontSize: 16, color: MUTED, valign: "middle" });
  s.addNotes("Zero tuning does not mean cheap. TabFM became about sixteen times slower per record when the context grew four times, and the full-context run did not finish. Three software problems needed workarounds, which I document for other users of these new packages.");

  // ================= 15. Conclusion =================
  s = base(true);
  s.addText("Conclusion", { x: M, y: 0.45, w: 10, h: 0.8, fontFace: HF, fontSize: 34, bold: true, color: WHITE, margin: 0, isTextBox: true });
  const concl = [["Performance", "No significant difference: tuned CatBoost ≈ zero-shot TabPFN ≈ TabFM (~78%)."],
    ["Data efficiency", "Foundation models far better with little data; gap closes at full size."],
    ["Explainability", "Same 7 biomarkers and directions in all models — SHAP works for all."],
    ["Practicality", "TabFM is slow at large context; new tools need testing before use."]];
  concl.forEach(([h, d], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.15, y = 1.65 + row * 2.35, w = 5.9;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 2.05, fill: { color: "2A2F3D" }, line: { color: "2A2F3D" }, rectRadius: 0.08 });
    dot(s, "check", x + 0.3, y + 0.3, 0.6);
    text(s, `RQ${i + 1} · ${h}`, { x: x + 1.1, y: y + 0.32, w: w - 1.4, h: 0.5, fontSize: 19, bold: true, color: WHITE });
    text(s, d, { x: x + 1.1, y: y + 0.9, w: w - 1.4, h: 1.0, fontSize: 15, color: "D5D8DF" });
  });
  text(s, "When labelled data is scarce, start with a tabular foundation model — and always explain the predictions.",
    { x: M, y: 6.45, w: W - 2 * M - 1.0, h: 0.5, fontSize: 16, italic: true, color: "F2A0AB" });
  s.addNotes("Each research question is answered. The main message: foundation models match a tuned baseline without tuning and are much better with little data, and all three models can be explained.");

  // ================= 16. Limitations & future =================
  s = base();
  title(s, "Limitations & future work");
  card(s, M, 1.6, 5.9, 4.6);
  dot(s, "warn", M + 0.3, 1.85, 0.6, "B7791F");
  text(s, "Limitations", { x: M + 1.1, y: 1.9, w: 4.5, h: 0.5, fontSize: 20, bold: true });
  bullets(s, ["Constructed dataset — not clinical validation", "TabFM used 500 rows, not full data", "SHAP for foundation models on 20–30 records",
    "One split, one seed; early stopping used test set"], { x: M + 0.35, y: 2.7, w: 5.3, h: 3.3, fontSize: 18 });
  card(s, 6.83, 1.6, 5.9, 4.6, DARK);
  dot(s, "road", 7.13, 1.85, 0.6);
  text(s, "Future work", { x: 7.93, y: 1.9, w: 4.5, h: 0.5, fontSize: 20, bold: true, color: WHITE });
  bullets(s, ["Validate on real clinical data", "Full-context TabFM, several seeds and splits", "Larger SHAP samples",
    "Ordinal models for the Moderate tier", "Ensembles and lightweight distilled models"], { x: 7.18, y: 2.7, w: 5.3, h: 3.3, fontSize: 18, color: WHITE });
  s.addNotes("The main limitation is the constructed dataset, so this is a benchmark, not a clinical tool. Future work: real clinical data, full-context TabFM, repeated splits, larger SHAP samples and ordinal models.");

  // ================= 17. Thank you =================
  s = base(true);
  s.addText("Thank you", { x: M, y: 2.2, w: W - 2 * M, h: 1.2, fontFace: HF, fontSize: 60, bold: true, color: WHITE, align: "center", margin: 0, isTextBox: true });
  s.addText("Questions & discussion", { x: M, y: 3.45, w: W - 2 * M, h: 0.6, fontFace: BF, fontSize: 24, color: "F2A0AB", align: "center", margin: 0, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: (W - 3.1) / 2, y: 4.6, w: 3.1, h: 1.27, fill: { color: WHITE }, line: { color: WHITE }, rectRadius: 0.06 });
  s.addImage({ path: IMG.logo, x: (W - 2.9) / 2, y: 4.68, w: 2.9, h: 1.11 });
  s.addText("Krishna Gautam  ·  Supervisor: Rabin Shrestha", { x: M, y: 6.2, w: W - 2 * M, h: 0.4, fontFace: BF, fontSize: 15, color: "D5D8DF", align: "center", margin: 0, isTextBox: true });
  s.addNotes("Thank you. I am happy to answer questions.");

  await pres.writeFile({ fileName: OUT });
  console.log("saved", OUT, n, "slides");
})();
