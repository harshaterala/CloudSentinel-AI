import React from "react";
import RiskHeatmap from "./RiskHeatmap";
import CostSummary from "./CostSummary";
import TopPriorities from "./TopPriorities";
import RoadmapTable from "./RoadmapTable";
import ExplanationPanel from "./ExplanationPanel";
import IngestionPanel from "./IngestionPanel";
import CopilotChat from "./CopilotChat";

export default function Dashboard({
  heatmap,
  stats,
  recommendations,
  roadmap,
  explanation,
  explaining,
  onSelectResource,
  onCloseExplanation,
  onIngestionApplied,
}) {
  return (
    <>
      {explaining && (
        <div className="loading" style={{ padding: 24 }}>
          <div className="spinner" />
          <p>Generating AI explanation...</p>
        </div>
      )}
      {explanation && !explaining && (
        <ExplanationPanel data={explanation} onClose={onCloseExplanation} />
      )}

      <RiskHeatmap data={heatmap} onSelect={onSelectResource} />

      <div className="dashboard-grid">
        <TopPriorities recommendations={recommendations} onSelect={onSelectResource} />
        <CostSummary stats={stats} />
      </div>

      <RoadmapTable roadmap={roadmap} onSelect={onSelectResource} />

      <CopilotChat onSelectResource={onSelectResource} />
      <IngestionPanel onApplied={onIngestionApplied} />
    </>
  );
}
