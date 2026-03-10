import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const RISK_COLORS = {
  Critical: "#ef4444",
  High: "#f97316",
  Medium: "#eab308",
  Low: "#22c55e",
};

export default function Charts({ stats }) {
  if (!stats) return null;

  const riskData = Object.entries(stats.risk_distribution || {}).map(([name, value]) => ({
    name,
    value,
  }));

  const typeData = Object.entries(stats.resource_type_counts || {}).map(([name, value]) => ({
    name,
    count: value,
  }));

  const providerData = Object.entries(stats.provider_counts || {}).map(([name, value]) => ({
    name,
    count: value,
  }));

  return (
    <div className="dashboard-grid">
      {/* Risk Distribution Pie */}
      <div className="section">
        <h2 className="section-title">Risk Distribution</h2>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={riskData}
              cx="50%"
              cy="50%"
              outerRadius={90}
              dataKey="value"
              label={({ name, value }) => `${name}: ${value}`}
            >
              {riskData.map((entry) => (
                <Cell key={entry.name} fill={RISK_COLORS[entry.name] || "#888"} />
              ))}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Resource Type Bar */}
      <div className="section">
        <h2 className="section-title">Resources by Type</h2>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={typeData}>
            <XAxis dataKey="name" tick={{ fill: "#8b8fa3", fontSize: 12 }} />
            <YAxis tick={{ fill: "#8b8fa3", fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: "#1a1d27", border: "1px solid #2e3347", borderRadius: 8 }}
            />
            <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Cloud Provider Pie */}
      {providerData.length > 0 && (
        <div className="section">
          <h2 className="section-title">Cloud Provider Distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={providerData}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="count"
                label={({ name, count }) => `${name}: ${count}`}
              >
                <Cell fill="#6366f1" />
                <Cell fill="#06b6d4" />
                <Cell fill="#f97316" />
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
