export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function handleResponse(res) {
  const body = await res.json();
  if (!res.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((d) => d.msg).join("; ")
      : body.detail || "Request failed.";
    throw new Error(detail);
  }
  return body;
}

async function getJson(path) {
  const res = await fetch(`${API_URL}${path}`);
  return handleResponse(res);
}

async function postJson(path, payload, { timeoutMs = 20000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    return await handleResponse(res);
  } catch (err) {
    if (err.name === "AbortError") throw new Error("Request timed out.");
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export const fetchMeta = () => getJson("/api/meta");
export const fetchHealth = () => getJson("/health");
export const fetchDatasetSummary = () => getJson("/api/analysis/dataset-summary");
export const fetchResults = () => getJson("/api/analysis/results");
export const fetchHistory = (limit = 10, skip = 0) =>
  getJson(`/api/predictions/history?limit=${limit}&skip=${skip}`);

export const predictCatboost = (payload) =>
  postJson("/api/predict/catboost", payload, { timeoutMs: 15000 });
export const predictTabpfn = (payload) =>
  postJson("/api/predict/tabpfn", payload, { timeoutMs: 30000 });
export const predictTabfm = (payload) =>
  postJson("/api/predict/tabfm", payload, { timeoutMs: 60000 });
export const logPrediction = (payload) => postJson("/api/predictions/log", payload, { timeoutMs: 10000 });
