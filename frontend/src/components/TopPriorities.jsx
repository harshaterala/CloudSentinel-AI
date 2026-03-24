import React from "react";

export default function TopPriorities({ recommendations, onSelect }) {
  if (!recommendations || recommendations.length === 0) return null;

  return (
    <div className="section">
      <h2 className="section-title">Top Priority Remediations</h2>
      {recommendations.map((rec, i) => (
        <div
          key={rec.resource_id}
          className="priority-item"
          onClick={() => onSelect(rec.resource_id)}
        >
          <div className="priority-rank">#{i + 1}</div>
          <div className="priority-details">
            <div className="resource-name">
              {rec.resource_id}{" "}
              <span className={`badge ${rec.risk_level?.toLowerCase()}`}>{rec.risk_level}</span>
            </div>
            <div className="resource-summary">
              {rec.resource_type} — {rec.summary}
            </div>
          </div>
          <div className="priority-score" style={{ color: "var(--critical)" }}>
            {rec.unified_priority_score}
          </div>
        </div>
      ))}
    </div>
  );
}
