import axios from "axios";

const API = axios.create({ baseURL: "/api" });

export async function fetchAnalysis() {
  const { data } = await API.get("/analysis");
  return data;
}

export async function fetchRecommendations() {
  const { data } = await API.get("/recommendations");
  return data;
}

export async function fetchExplanation(resourceId) {
  const { data } = await API.get(`/explain/${encodeURIComponent(resourceId)}`);
  return data;
}

export async function fetchStats() {
  const { data } = await API.get("/stats");
  return data;
}

export async function fetchHeatmap() {
  const { data } = await API.get("/heatmap");
  return data;
}

export async function fetchExecutiveSummary() {
  const { data } = await API.get("/executive-summary");
  return data;
}

export async function fetchHealth() {
  const { data } = await API.get("/health");
  return data;
}

export async function fetchCopilotQuery(query) {
  const { data } = await API.post("/copilot/query", { query });
  return data;
}

export async function fetchRoadmap(limit = 10) {
  const { data } = await API.get("/roadmap", { params: { limit, include_remediation: true } });
  return data;
}

export async function runIngestionNormalize(payload) {
  const { data } = await API.post("/ingestion/normalize", payload);
  return data;
}
