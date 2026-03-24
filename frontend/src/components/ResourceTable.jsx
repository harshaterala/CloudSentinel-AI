import React, { useState, useMemo } from "react";

function ScoreBar({ score, max = 100 }) {
  const pct = Math.min((score / max) * 100, 100);
  let color = "#22c55e";
  if (score >= 70) color = "#ef4444";
  else if (score >= 40) color = "#f97316";
  else if (score >= 20) color = "#eab308";
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
      <span className="score-bar">
        <span className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </span>
      <span>{score}</span>
    </span>
  );
}

function Badge({ level }) {
  return <span className={`badge ${level.toLowerCase()}`}>{level}</span>;
}

const COLUMNS = [
  { key: "priority_rank", label: "#", numeric: true },
  { key: "resource_id", label: "Resource" },
  { key: "resource_type", label: "Type" },
  { key: "cloud_provider", label: "Cloud" },
  { key: "unified_priority_score", label: "Priority", numeric: true },
  { key: "security_risk_score", label: "Security", numeric: true },
  { key: "cost_risk_score", label: "Cost", numeric: true },
  { key: "risk_level", label: "Risk Level" },
  { key: "monthly_cost", label: "Cost ($)", numeric: true },
  { key: "estimated_waste", label: "Waste ($)", numeric: true },
];

export default function ResourceTable({ resources, onSelect }) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");
  const [providerFilter, setProviderFilter] = useState("");
  const [sortCol, setSortCol] = useState("unified_priority_score");
  const [sortAsc, setSortAsc] = useState(false);

  const types = useMemo(() => [...new Set(resources.map((r) => r.resource_type))].sort(), [resources]);
  const providers = useMemo(() => [...new Set(resources.map((r) => r.cloud_provider))].sort(), [resources]);
  const riskLevels = ["Critical", "High", "Medium", "Low"];

  const filtered = useMemo(() => {
    let list = resources;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) => r.resource_id.toLowerCase().includes(q) || r.resource_type.toLowerCase().includes(q)
      );
    }
    if (typeFilter) list = list.filter((r) => r.resource_type === typeFilter);
    if (riskFilter) list = list.filter((r) => r.risk_level === riskFilter);
    if (providerFilter) list = list.filter((r) => r.cloud_provider === providerFilter);

    list = [...list].sort((a, b) => {
      const av = a[sortCol] ?? "";
      const bv = b[sortCol] ?? "";
      if (typeof av === "number" && typeof bv === "number") {
        return sortAsc ? av - bv : bv - av;
      }
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
    return list;
  }, [resources, search, typeFilter, riskFilter, providerFilter, sortCol, sortAsc]);

  const handleSort = (col) => {
    if (col === sortCol) setSortAsc(!sortAsc);
    else {
      setSortCol(col);
      setSortAsc(false);
    }
  };

  return (
    <div className="section">
      <h2 className="section-title">Cloud Resources ({filtered.length})</h2>

      <div className="filter-bar">
        <input
          placeholder="Search resources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={providerFilter} onChange={(e) => setProviderFilter(e.target.value)}>
          <option value="">All Providers</option>
          {providers.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All Types</option>
          {types.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
          <option value="">All Risk Levels</option>
          {riskLevels.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th key={col.key} onClick={() => handleSort(col.key)}>
                  {col.label} {sortCol === col.key ? (sortAsc ? "↑" : "↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.slice(0, 100).map((r) => (
              <tr key={r.resource_id} className="clickable" onClick={() => onSelect(r.resource_id)}>
                <td style={{ color: "var(--text-muted)", fontWeight: 600 }}>{r.priority_rank ?? "—"}</td>
                <td style={{ fontWeight: 500 }}>{r.resource_id}</td>
                <td>{r.resource_type}</td>
                <td>{r.cloud_provider}</td>
                <td><ScoreBar score={r.unified_priority_score} /></td>
                <td><ScoreBar score={r.security_risk_score} /></td>
                <td><ScoreBar score={r.cost_risk_score} /></td>
                <td><Badge level={r.risk_level} /></td>
                <td>${r.monthly_cost?.toFixed(2)}</td>
                <td style={{ color: r.estimated_waste > 0 ? "var(--high)" : "var(--text-muted)" }}>
                  {r.estimated_waste > 0 ? `$${r.estimated_waste?.toFixed(2)}` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length > 100 && (
          <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 8 }}>
            Showing first 100 of {filtered.length} resources. Use filters to narrow results.
          </p>
        )}
      </div>
    </div>
  );
}
