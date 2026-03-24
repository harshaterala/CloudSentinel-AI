import React from "react";

export default function RoadmapTable({ roadmap, onSelect }) {
  if (!roadmap || roadmap.length === 0) return null;

  return (
    <div className="section">
      <h2 className="section-title">Fix-First Roadmap (Top 10)</h2>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Resource</th>
              <th>Type</th>
              <th>Severity</th>
              <th>UPS</th>
              <th>Waste ($)</th>
              <th>Reason</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {roadmap.map((item) => (
              <tr key={item.resource_id} className="clickable" onClick={() => onSelect(item.resource_id)}>
                <td>#{item.rank}</td>
                <td>{item.resource_id}</td>
                <td>{item.resource_type}</td>
                <td>
                  <span className={`badge ${item.severity?.toLowerCase()}`}>{item.severity}</span>
                </td>
                <td>{item.ups}</td>
                <td style={{ color: item.estimated_monthly_waste > 0 ? "var(--high)" : "var(--text-muted)" }}>
                  ${item.estimated_monthly_waste?.toFixed?.(2) ?? item.estimated_monthly_waste}
                </td>
                <td>{item.short_reason}</td>
                <td>{item.recommended_action || "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
