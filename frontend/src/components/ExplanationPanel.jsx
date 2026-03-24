import React from "react";

export default function ExplanationPanel({ data, onClose }) {
  if (!data) return null;

  const explanation = data?.explanation || {};

  return (
    <div className="explain-panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3>
          AI Analysis — {data?.resource_id}
        </h3>
        <button className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="explain-field">
        <div className="field-label">Root Cause</div>
        <div className="field-value">{explanation?.root_cause}</div>
      </div>

      <div className="explain-field">
        <div className="field-label">Business Impact</div>
        <div className="field-value">{explanation?.business_impact}</div>
      </div>

      <div className="explain-field">
        <div className="field-label">Remediation Steps</div>
        <div className="field-value">{explanation?.remediation_steps}</div>
      </div>

      <div className="explain-field">
        <div className="field-label">Executive Summary</div>
        <div className="field-value">{explanation?.executive_summary}</div>
      </div>
    </div>
  );
}
