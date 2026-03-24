import React from "react";

const COLORS = {
  Critical: "#ef4444",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#22c55e",
};

export default function RiskHeatmap({ data, onSelect }) {
  if (!data || data.length === 0) return null;

  return (
    <div className="section">
      <h2 className="section-title">Risk Heatmap</h2>
      <div className="heatmap-grid">
        {data.map((item) => (
          <div
            key={item.resource_id}
            className="heatmap-cell"
            style={{ background: COLORS[item.risk_level] || "#555" }}
            title={`${item.resource_id} [${item.cloud_provider}] — ${item.risk_level} (UPS: ${item.unified_priority_score})`}
            onClick={() => onSelect(item.resource_id)}
          />
        ))}
      </div>
      <div className="heatmap-legend">
        {Object.entries(COLORS).map(([level, color]) => (
          <span key={level}>
            <span className="legend-block" style={{ background: color }} />
            {level}
          </span>
        ))}
      </div>
    </div>
  );
}
