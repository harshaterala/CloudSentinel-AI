import React, { useState } from "react";
import { fetchCopilotQuery } from "../api/client";

const SUGGESTIONS = [
  "Which resources are the most dangerous?",
  "Where am I wasting the most money?",
  "Show publicly exposed resources",
  "What should I fix first?",
];

function ResultCard({ resource, onSelect }) {
  const r = resource;
  return (
    <div className="copilot-result-card" onClick={() => onSelect?.(r.resource_id)}>
      <div className="copilot-result-header">
        <span className="copilot-result-id">{r.resource_id}</span>
        <span className={`badge ${r.risk_level?.toLowerCase()}`}>{r.risk_level}</span>
      </div>
      <div className="copilot-result-meta">
        {r.resource_type} · {r.cloud_provider}
        {r.unified_priority_score != null && (
          <> · UPS: <strong>{r.unified_priority_score}</strong></>
        )}
        {r.estimated_waste > 0 && (
          <span style={{ color: "var(--high)" }}>
            {" "}· Waste: ${r.estimated_waste?.toFixed(2)}
          </span>
        )}
      </div>
    </div>
  );
}

export default function CopilotChat({ onSelectResource }) {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleSubmit = async (q) => {
    const text = (q || query).trim();
    if (!text) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const data = await fetchCopilotQuery(text);
      setResponse(data);
      setHistory((prev) => [{ query: text }, ...prev.slice(0, 4)]);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Query failed");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="copilot-panel">
      <div className="copilot-header">
        <h2 className="section-title">
          <span style={{ marginRight: 8 }}>🤖</span>AI Security Copilot
        </h2>
        <span className="copilot-hint">Ask about risks, cost waste, remediation, or compliance benchmarks</span>
      </div>

      {/* Suggestion chips */}
      <div className="copilot-suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className="copilot-chip"
            onClick={() => {
              setQuery(s);
              handleSubmit(s);
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div className="copilot-input-row">
        <input
          className="copilot-input"
          placeholder="Ask a question about your cloud security..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="copilot-ask-btn"
          onClick={() => handleSubmit()}
          disabled={loading || !query.trim()}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="copilot-loading">
          <div className="spinner" />
          <span>Analyzing your query...</span>
        </div>
      )}

      {/* Error */}
      {error && <div className="copilot-error">{error}</div>}

      {/* Response */}
      {response && !loading && (
        <div className="copilot-response">
          <div className="copilot-message">
            {response.answer}
          </div>
          <div className="copilot-results">
            {(response.related_resources || []).map((r, i) => (
              <ResultCard
                key={r.resource_id || r.resource?.resource_id || i}
                resource={r}
                onSelect={onSelectResource}
              />
            ))}
          </div>
          {(response.sources || []).length > 0 && (
            <div className="copilot-sources">
              <div className="copilot-history-label">Sources</div>
              {(response.sources || []).map((s, i) => (
                <div key={i} className="copilot-source-item">{s}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* History */}
      {history.length > 0 && !loading && (
        <div className="copilot-history">
          <div className="copilot-history-label">Recent queries</div>
          {history.map((h, i) => (
            <button
              key={i}
              className="copilot-history-item"
              onClick={() => {
                setQuery(h.query);
                handleSubmit(h.query);
              }}
            >
              {h.query}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
