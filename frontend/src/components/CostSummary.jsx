import React from "react";

export default function CostSummary({ stats }) {
  if (!stats) return null;

  const wastePercent =
    stats.total_monthly_cost > 0
      ? ((stats.estimated_monthly_waste / stats.total_monthly_cost) * 100).toFixed(1)
      : 0;

  return (
    <div className="section">
      <h2 className="section-title">Cost Optimization Summary</h2>
      <div className="cost-summary-grid">
        <div className="cost-item">
          <div className="label">Total Monthly Spend</div>
          <div className="value" style={{ color: "var(--accent-light)" }}>
            ${stats.total_monthly_cost?.toLocaleString()}
          </div>
        </div>
        <div className="cost-item">
          <div className="label">Estimated Waste</div>
          <div className="value" style={{ color: "var(--critical)" }}>
            ${stats.estimated_monthly_waste?.toLocaleString()}
            <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginLeft: 6 }}>
              ({wastePercent}%)
            </span>
          </div>
        </div>
        <div className="cost-item">
          <div className="label">Idle Resources</div>
          <div className="value" style={{ color: "var(--high)" }}>{stats.idle_count}</div>
        </div>
        <div className="cost-item">
          <div className="label">Oversized Resources</div>
          <div className="value" style={{ color: "var(--medium)" }}>{stats.oversized_count}</div>
        </div>
        <div className="cost-item">
          <div className="label">Avg Cost Risk Score</div>
          <div className="value">{stats.avg_cost_score}</div>
        </div>
        <div className="cost-item">
          <div className="label">Unencrypted</div>
          <div className="value" style={{ color: "var(--high)" }}>{stats.unencrypted_count}</div>
        </div>
      </div>
    </div>
  );
}
