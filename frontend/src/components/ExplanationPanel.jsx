import React from "react";

export default function ExplanationPanel({ data, onClose }) {
  if (!data) return null;

  const { resource, explanation } = data;
  const riskSummary = explanation?.risk_summary || explanation?.risk;
  const exploitationImpact = explanation?.exploitation_impact || explanation?.impact;
  const remediationSteps = explanation?.remediation_steps || [];
  const recommendationText = explanation?.recommendation;

  return (
    <div className="explain-panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>
          AI Analysis — {resource?.resource_id}
          <span style={{ fontWeight: 400, fontSize: "0.85rem", color: "var(--text-muted)", marginLeft: 8 }}>
            {resource?.resource_type} · {resource?.cloud_provider}
          </span>
        </h3>
        <button className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12, marginBottom: 16, marginTop: 8 }}>
        <div className="cost-item">
          <div className="label">Security Risk</div>
          <div className="value" style={{ color: "var(--critical)" }}>{resource?.security_risk_score}</div>
        </div>
        <div className="cost-item">
          <div className="label">Cost Risk</div>
          <div className="value" style={{ color: "var(--high)" }}>{resource?.cost_risk_score}</div>
        </div>
        <div className="cost-item">
          <div className="label">Priority Score</div>
          <div className="value" style={{ color: "var(--accent-light)" }}>{resource?.unified_priority_score}</div>
        </div>
        <div className="cost-item">
          <div className="label">Risk Level</div>
          <div className="value">
            <span className={`badge ${resource?.risk_level?.toLowerCase()}`}>{resource?.risk_level}</span>
          </div>
        </div>
        {resource?.priority_rank != null && (
          <div className="cost-item">
            <div className="label">Priority Rank</div>
            <div className="value" style={{ color: "var(--accent-light)" }}>#{resource?.priority_rank}</div>
          </div>
        )}
        {resource?.estimated_waste > 0 && (
          <div className="cost-item">
            <div className="label">Est. Waste</div>
            <div className="value" style={{ color: "var(--high)" }}>${resource?.estimated_waste?.toFixed(2)}</div>
          </div>
        )}
      </div>

      <div className="explain-field">
        <div className="field-label">Why This Resource Is Risky</div>
        <div className="field-value">{riskSummary}</div>
      </div>

      <div className="explain-field">
        <div className="field-label">What Happens If Exploited</div>
        <div className="field-value">{exploitationImpact}</div>
      </div>

      <div className="explain-field">
        <div className="field-label">Step-by-Step Remediation</div>
        <div className="field-value">
          {Array.isArray(remediationSteps) && remediationSteps.length > 0 ? (
            <ol style={{ paddingLeft: 18 }}>
              {remediationSteps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          ) : (
            recommendationText
          )}
        </div>
      </div>

      <div className="explain-field">
        <div className="field-label">Business Impact</div>
        <div className="field-value">{explanation?.business_impact}</div>
      </div>

      {Array.isArray(explanation?.sources) && explanation.sources.length > 0 && (
        <div className="explain-field">
          <div className="field-label">Sources</div>
          <div className="field-value">{explanation.sources.join(" | ")}</div>
        </div>
      )}

      {explanation?.source && (
        <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: 12 }}>
          Source: {explanation.source === "llm" ? "AI-Generated (LLM + RAG)" : "Template-based with RAG context"}
        </p>
      )}
    </div>
  );
}
