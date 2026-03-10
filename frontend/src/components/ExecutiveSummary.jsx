import React from "react";

export default function ExecutiveSummary({ summary }) {
  if (!summary) return null;

  const {
    total_resources_analysed,
    critical_risks,
    high_risks,
    total_monthly_cost,
    estimated_monthly_waste,
    waste_percentage,
    top_security_issue,
    issue_breakdown,
    top_risk_resource,
    providers_analysed,
    scoring_methodology,
  } = summary;

  return (
    <div className="executive-summary">
      <h2 className="section-title">Executive Summary</h2>
      <p className="exec-subtitle">
        High-level overview for leadership and compliance reporting
      </p>

      <div className="exec-grid">
        {/* Key metrics */}
        <div className="exec-card">
          <div className="exec-label">Resources Analysed</div>
          <div className="exec-value accent">{total_resources_analysed}</div>
        </div>
        <div className="exec-card">
          <div className="exec-label">Critical Risks</div>
          <div className="exec-value critical">{critical_risks}</div>
        </div>
        <div className="exec-card">
          <div className="exec-label">High Risks</div>
          <div className="exec-value high">{high_risks}</div>
        </div>
        <div className="exec-card">
          <div className="exec-label">Monthly Spend</div>
          <div className="exec-value accent">
            ${total_monthly_cost?.toLocaleString()}
          </div>
        </div>
        <div className="exec-card">
          <div className="exec-label">Estimated Waste</div>
          <div className="exec-value critical">
            ${estimated_monthly_waste?.toLocaleString()}
          </div>
        </div>
        <div className="exec-card">
          <div className="exec-label">Waste %</div>
          <div className="exec-value high">{waste_percentage}%</div>
        </div>
      </div>

      {/* Issue breakdown */}
      <div className="exec-details">
        <div className="exec-detail-block">
          <h4>Top Security Issue</h4>
          <span className="badge critical">{top_security_issue}</span>
          {issue_breakdown && Object.keys(issue_breakdown).length > 0 && (
            <ul className="exec-issue-list">
              {Object.entries(issue_breakdown).map(([issue, count]) => (
                <li key={issue}>
                  <span className="exec-issue-name">{issue}</span>
                  <span className="exec-issue-count">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="exec-detail-block">
          <h4>Highest-Risk Resource</h4>
          <div className="exec-top-resource">
            <div className="exec-resource-id">{top_risk_resource?.resource_id}</div>
            <div className="exec-resource-meta">
              {top_risk_resource?.resource_type} ({top_risk_resource?.cloud_provider})
            </div>
            <div className="exec-resource-score">
              UPS: <strong>{top_risk_resource?.unified_priority_score}</strong>
            </div>
          </div>
        </div>

        <div className="exec-detail-block">
          <h4>Scoring Methodology</h4>
          <div className="exec-methodology">
            <code>{scoring_methodology?.formula}</code>
            <div className="exec-weights">
              Security: {(scoring_methodology?.security_weight * 100)}% | Cost:{" "}
              {(scoring_methodology?.cost_weight * 100)}%
            </div>
          </div>
        </div>
      </div>

      {/* Providers */}
      {providers_analysed?.length > 0 && (
        <div className="exec-providers">
          {providers_analysed.map((p) => (
            <span key={p} className="exec-provider-tag">
              {p}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
