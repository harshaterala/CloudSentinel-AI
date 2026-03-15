import React, { useEffect, useState, useCallback } from "react";
import {
  fetchAnalysis,
  fetchRecommendations,
  fetchStats,
  fetchHeatmap,
  fetchExplanation,
  fetchExecutiveSummary,
  fetchRoadmap,
} from "./api/client";
import RiskHeatmap from "./components/RiskHeatmap";
import ResourceTable from "./components/ResourceTable";
import CostSummary from "./components/CostSummary";
import TopPriorities from "./components/TopPriorities";
import ExplanationPanel from "./components/ExplanationPanel";
import Charts from "./components/Charts";
import ExecutiveSummary from "./components/ExecutiveSummary";
import CopilotChat from "./components/CopilotChat";
import RoadmapTable from "./components/RoadmapTable";
import IngestionPanel from "./components/IngestionPanel";

export default function App() {
  const [resources, setResources] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [stats, setStats] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [execSummary, setExecSummary] = useState(null);
  const [roadmap, setRoadmap] = useState([]);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");

  const loadDashboard = useCallback(async () => {
    const [analysisRes, recsRes, statsRes, heatmapRes, execRes, roadmapRes] = await Promise.all([
      fetchAnalysis(),
      fetchRecommendations(),
      fetchStats(),
      fetchHeatmap(),
      fetchExecutiveSummary(),
      fetchRoadmap(10),
    ]);
    setResources(analysisRes.resources || []);
    setRecommendations(recsRes.recommendations || []);
    setStats(statsRes);
    setHeatmap(heatmapRes.heatmap || []);
    setExecSummary(execRes);
    setRoadmap(roadmapRes.roadmap || []);
  }, []);

  useEffect(() => {
    async function load() {
      try {
        await loadDashboard();
      } catch (err) {
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [loadDashboard]);

  const handleSelectResource = useCallback(async (resourceId) => {
    setExplaining(true);
    setExplanation(null);
    try {
      const data = await fetchExplanation(resourceId);
      setExplanation(data);
    } catch (err) {
      setExplanation({
        resource: { resource_id: resourceId },
        explanation: {
          risk: "Failed to load explanation",
          impact: err.message,
          recommendation: "Please try again",
          business_impact: "N/A",
        },
      });
    } finally {
      setExplaining(false);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Analyzing cloud infrastructure...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: 8 }}>
          Make sure the backend is running on http://127.0.0.1:8000
        </p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>
            <span className="header-icon">🛡️</span> Cloud Security Copilot
          </h1>
          <span className="header-subtitle">
            GenAI-Powered Multi-Cloud Security & Cost Intelligence Platform
          </span>
        </div>
        <div className="header-right">
          <span className="header-badge">{stats?.total_resources} resources</span>
          <span className="header-badge">
            {execSummary?.providers_analysed?.join(" · ")}
          </span>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setActiveTab("dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`tab-btn ${activeTab === "executive" ? "active" : ""}`}
          onClick={() => setActiveTab("executive")}
        >
          Executive Summary
        </button>
        <button
          className={`tab-btn ${activeTab === "resources" ? "active" : ""}`}
          onClick={() => setActiveTab("resources")}
        >
          Resources
        </button>
        <button
          className={`tab-btn ${activeTab === "copilot" ? "active" : ""}`}
          onClick={() => setActiveTab("copilot")}
        >
          AI Copilot
        </button>
      </nav>

      {/* Explanation Panel (always visible when triggered) */}
      {explaining && (
        <div className="loading" style={{ padding: 24 }}>
          <div className="spinner" />
          <p>Generating AI explanation...</p>
        </div>
      )}
      {explanation && !explaining && (
        <ExplanationPanel data={explanation} onClose={() => setExplanation(null)} />
      )}

      {/* Tab: Dashboard */}
      {activeTab === "dashboard" && (
        <>
          {/* Stats Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="label">Critical Risks</div>
              <div className="value critical">{stats?.critical_count}</div>
            </div>
            <div className="stat-card">
              <div className="label">High Risks</div>
              <div className="value high">{stats?.high_count}</div>
            </div>
            <div className="stat-card">
              <div className="label">Avg Priority Score</div>
              <div className="value accent">{stats?.avg_priority_score}</div>
            </div>
            <div className="stat-card">
              <div className="label">Publicly Exposed</div>
              <div className="value critical">{stats?.publicly_exposed_count}</div>
            </div>
            <div className="stat-card">
              <div className="label">Monthly Spend</div>
              <div className="value accent">${stats?.total_monthly_cost?.toLocaleString()}</div>
            </div>
            <div className="stat-card">
              <div className="label">Est. Waste</div>
              <div className="value high">${stats?.estimated_monthly_waste?.toLocaleString()}</div>
            </div>
          </div>

          {/* Risk Heatmap */}
          <RiskHeatmap data={heatmap} onSelect={handleSelectResource} />

          {/* Charts */}
          <Charts stats={stats} />

          {/* Top Priorities + Cost Summary side by side */}
          <div className="dashboard-grid">
            <TopPriorities recommendations={recommendations} onSelect={handleSelectResource} />
            <CostSummary stats={stats} />
          </div>

          <RoadmapTable roadmap={roadmap} onSelect={handleSelectResource} />
        </>
      )}

      {/* Tab: Executive Summary */}
      {activeTab === "executive" && (
        <ExecutiveSummary summary={execSummary} />
      )}

      {/* Tab: Resources */}
      {activeTab === "resources" && (
        <ResourceTable resources={resources} onSelect={handleSelectResource} />
      )}

      {/* Tab: AI Copilot */}
      {activeTab === "copilot" && (
        <>
          <CopilotChat onSelectResource={handleSelectResource} />
          <IngestionPanel onApplied={loadDashboard} />
        </>
      )}
    </div>
  );
}
