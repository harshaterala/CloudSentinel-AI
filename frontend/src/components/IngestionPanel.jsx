import React, { useState } from "react";
import { runIngestionNormalize } from "../api/client";

const FILE_KEY_MAP = {
  "iam_logs.json": "iam_logs",
  "storage_access_logs.json": "storage_access_logs",
  "security_groups.json": "security_groups",
  "usage_metrics.json": "usage_metrics",
};

export default function IngestionPanel({ onApplied }) {
  const [payload, setPayload] = useState({
    iam_logs: [],
    storage_access_logs: [],
    security_groups: [],
    usage_metrics: [],
    apply_to_runtime: true,
  });
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFiles = async (event) => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;

    const next = { ...payload };
    for (const file of files) {
      const key = FILE_KEY_MAP[file.name];
      if (!key) continue;
      try {
        const text = await file.text();
        const json = JSON.parse(text);
        next[key] = Array.isArray(json) ? json : [];
      } catch {
        setStatus(`Failed to parse ${file.name}. Ensure it is valid JSON array.`);
      }
    }
    setPayload(next);
    setStatus("Loaded selected log files. Click Apply Telemetry.");
  };

  const applyTelemetry = async () => {
    setLoading(true);
    setStatus("");
    try {
      const res = await runIngestionNormalize(payload);
      setStatus(`Applied telemetry. ${res.normalized_records} resources normalized.`);
      onApplied?.();
    } catch (err) {
      setStatus(err.response?.data?.detail || err.message || "Failed to apply telemetry.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section" style={{ marginTop: 16 }}>
      <h2 className="section-title">Simulated Cloud Telemetry Upload (Optional)</h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", marginBottom: 10 }}>
        Upload custom simulated JSON logs for demo scenarios (IAM, storage access, security groups, usage).
      </p>
      <input type="file" accept=".json" multiple onChange={handleFiles} />
      <div style={{ marginTop: 10 }}>
        <button className="copilot-ask-btn" onClick={applyTelemetry} disabled={loading}>
          {loading ? "Applying..." : "Apply Telemetry"}
        </button>
      </div>
      {status && <div style={{ marginTop: 8, color: "var(--text-muted)", fontSize: "0.82rem" }}>{status}</div>}
    </div>
  );
}
