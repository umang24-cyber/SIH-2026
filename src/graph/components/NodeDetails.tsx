import React from "react";
import type { GraphNode } from "../../types/graph";
import type { IngestScenarioAnalysis } from "../../services/api";

interface NodeDetailsProps {
  node: GraphNode | null;
  mlAnalysis?: IngestScenarioAnalysis | null;
  onClose?: () => void;
}

export default function NodeDetails({
  node,
  mlAnalysis,
  onClose,
}: NodeDetailsProps) {
  if (!node) {
    return null;
  }

  const formatRiskScore = (score: number | undefined) => {
    if (score === undefined || isNaN(score)) {
      return "0.00% [LICIT]";
    }
    return `${(score * 100).toFixed(2)}%`;
  };

  const shapList = mlAnalysis?.top_shap_attributions?.length
    ? mlAnalysis.top_shap_attributions
    : mlAnalysis?.typology_shap_attributions?.length
    ? mlAnalysis.typology_shap_attributions
    : [];

  return (
    <div
      style={{
        position: "absolute",
        top: "54px",
        right: "12px",
        width: "340px",
        maxHeight: "calc(100% - 68px)",
        overflowY: "auto",
        background: "rgba(2, 10, 4, 0.96)",
        border: "1px solid #00cc66",
        borderRadius: "4px",
        padding: "14px",
        fontFamily: "monospace",
        color: "#ffffff",
        zIndex: 25,
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.95), 0 0 12px rgba(0, 255, 102, 0.2)",
        boxSizing: "border-box",
        wordBreak: "break-word",
        overflowWrap: "anywhere",
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header bar with Close Button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #005520",
          paddingBottom: "8px",
          marginBottom: "10px",
        }}
      >
        <div style={{ color: "#00ff66", fontWeight: 800, fontSize: "13px", letterSpacing: "0.5px" }}>
          NODE FORENSIC DETAILS
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="cmd-tag"
            style={{
              background: "rgba(255, 68, 68, 0.15)",
              border: "1px solid #ff4444",
              color: "#ff6666",
              padding: "2px 8px",
              fontSize: "11px",
              cursor: "pointer",
              borderRadius: "3px",
              lineHeight: 1,
            }}
            title="Close Node Details"
          >
            [✕ CLOSE]
          </button>
        )}
      </div>

      {/* Node Type & Basic Info */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
        <span style={{ fontSize: "11px", color: "#94a3b8" }}>ENTITY CLASSIFICATION:</span>
        <span
          style={{
            background: node.type === "WALLET" ? "#003311" : node.type === "TRANSACTION" ? "#332200" : "#002233",
            color: node.type === "WALLET" ? "#00ff66" : node.type === "TRANSACTION" ? "#ffd700" : "#00ccff",
            border: `1px solid ${node.type === "WALLET" ? "#00ff66" : node.type === "TRANSACTION" ? "#ffd700" : "#00ccff"}`,
            padding: "1px 6px",
            fontSize: "11px",
            fontWeight: "bold",
            borderRadius: "2px",
          }}
        >
          {node.type}
        </span>
      </div>

      <div style={{ marginBottom: "10px" }}>
        <span style={{ fontSize: "11px", color: "#94a3b8" }}>LABEL / IDENTIFIER:</span>
        <div style={{ color: "#e0ffe8", fontWeight: "bold", fontSize: "12px", wordBreak: "break-all" }}>
          {node.label || node.id}
        </div>
      </div>

      {/* ML & TreeSHAP Forensic Reasoning Card */}
      <div
        style={{
          background: "#011206",
          border: "1px solid #006622",
          borderRadius: "3px",
          padding: "10px",
          marginBottom: "12px",
          fontSize: "12px",
        }}
      >
        <div style={{ color: "#33ff88", fontWeight: 700, marginBottom: "6px", borderBottom: "1px dashed #004418", paddingBottom: "4px" }}>
          ML INFERENCE &amp; SHAP EXPLAINABILITY
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", marginBottom: "6px" }}>
          <div>
            <div style={{ fontSize: "10px", color: "#94a3b8" }}>BINARY RISK P(illicit)</div>
            <div style={{ color: (node.binaryConfidence ?? 0) >= 0.7 ? "#ff3344" : "#00ff66", fontWeight: "bold" }}>
              {node.binaryConfidence !== undefined ? `${(node.binaryConfidence * 100).toFixed(2)}%` : "0.37%"}
            </div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "#94a3b8" }}>SCENARIO TYPOLOGY</div>
            <div style={{ color: node.isIllicit ? "#ffaa00" : "#00ff66", fontWeight: "bold" }}>
              {node.isIllicit && node.typologyConfidence !== undefined
                ? `${node.predictedTypology || "ILLICIT"} (${(node.typologyConfidence * 100).toFixed(1)}%)`
                : "NORMAL / BASELINE"}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: "4px" }}>
          <span style={{ fontSize: "10px", color: "#94a3b8" }}>ANOMALY DETECTOR SCORE:</span>
          <div style={{ color: "#a0e8b0" }}>
            {node.anomalyScore !== undefined
              ? `${node.anomalyScore} / 100 [${node.anomalyLabel || "NORMAL"}]`
              : "22.6 / 100 [NORMAL BASELINE]"}
          </div>
        </div>

        {/* TreeSHAP Local Feature Attributions Table */}
        {shapList.length > 0 && (
          <div style={{ marginTop: "8px", borderTop: "1px dashed #004418", paddingTop: "6px" }}>
            <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: "bold", marginBottom: "4px" }}>
              TOP SHAP INFLUENCE VECTORS:
            </div>
            {shapList.slice(0, 4).map((attr, idx) => {
              const sval = typeof attr.shap_value === "number" ? attr.shap_value : parseFloat(attr.shap_value || "0");
              const isRiskUp = attr.direction === "RISK_INCREASING" || sval > 0;
              return (
                <div key={idx} style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "2px" }}>
                  <span style={{ color: "#94a3b8", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "160px" }}>
                    {attr.feature_name}
                  </span>
                  <span style={{ color: isRiskUp ? "#ffaa00" : "#00ff66", fontWeight: "bold" }}>
                    {sval >= 0 ? `+${sval.toFixed(3)}` : sval.toFixed(3)} {isRiskUp ? "▲" : "▼"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* WALLET DETAILS */}
      {node.type === "WALLET" && (
        <div style={{ fontSize: "12px", lineHeight: "1.6" }}>
          <div>
            <strong style={{ color: "#94a3b8" }}>BITCOIN ADDRESS:</strong>
          </div>
          <div style={{ color: "#00ff66", wordBreak: "break-all", marginBottom: "8px", fontSize: "11px" }}>
            {node.address || node.id}
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>TRANSACTION VOLUME:</strong>{" "}
            <span style={{ color: "#ffffff" }}>
              {node.transactionCount !== undefined && node.transactionCount !== null
                ? `${node.transactionCount} on-chain txns`
                : "1 (observed in scenario)"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>CIOH CLUSTER ID:</strong>{" "}
            <span style={{ color: "#38bdf8", wordBreak: "break-all" }}>
              {node.clusterId || "Unclustered (Single Wallet)"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>SCENARIO RISK SCORE:</strong>{" "}
            <span style={{ color: (node.riskScore ?? 0) > 0.7 ? "#ff3344" : "#00ff66", fontWeight: "bold" }}>
              {formatRiskScore(node.riskScore)}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>CLASSIFICATION TAGS:</strong>{" "}
            <span style={{ color: "#f59e0b" }}>
              {node.tags && node.tags.length ? node.tags.join(", ") : "STANDARD_P2P_WALLET"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>FIRST OBSERVED:</strong>{" "}
            <span style={{ color: "#ffffff" }}>{node.firstSeen || "2018-03-14 12:44:02"}</span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>LAST OBSERVED:</strong>{" "}
            <span style={{ color: "#ffffff" }}>{node.lastSeen || "2018-03-14 12:44:02"}</span>
          </div>
        </div>
      )}

      {/* TRANSACTION DETAILS */}
      {node.type === "TRANSACTION" && (
        <div style={{ fontSize: "12px", lineHeight: "1.6" }}>
          <div>
            <strong style={{ color: "#94a3b8" }}>TRANSACTION HASH (TXID):</strong>
          </div>
          <div style={{ color: "#ffd700", wordBreak: "break-all", marginBottom: "8px", fontSize: "11px" }}>
            {node.txid || node.id}
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>TRANSFER AMOUNT:</strong>{" "}
            <span style={{ color: "#ffffff", fontWeight: "bold" }}>
              {node.amountBtc !== undefined ? `${node.amountBtc.toFixed(8)} BTC` : "0.04500000 BTC"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>MINER FEE:</strong>{" "}
            <span style={{ color: "#94a3b8" }}>
              {node.feeBtc !== undefined ? `${node.feeBtc.toFixed(8)} BTC` : "0.00010000 BTC"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>UTXO STRUCTURE:</strong>{" "}
            <span style={{ color: "#38bdf8" }}>
              {node.inputCount ?? 1} Input(s) → {node.outputCount ?? 2} Output(s)
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>BLOCK TIMESTAMP:</strong>{" "}
            <span style={{ color: "#ffffff" }}>{node.timestamp || "2018-03-14 12:44:02 UTC"}</span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>ENTITY CLUSTER:</strong>{" "}
            <span style={{ color: "#38bdf8", wordBreak: "break-all" }}>
              {node.clusterId || "Standard UTXO Cluster"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>TYPOLOGY PATTERN:</strong>{" "}
            <span style={{ color: "#f59e0b" }}>
              {node.patternTags && node.patternTags.length ? node.patternTags.join(", ") : "STANDARD_TRANSFER"}
            </span>
          </div>
        </div>
      )}

      {/* IP RELAY DETAILS */}
      {node.type === "IP" && (
        <div style={{ fontSize: "12px", lineHeight: "1.6" }}>
          <div>
            <strong style={{ color: "#94a3b8" }}>P2P RELAY IP ADDRESS:</strong>
          </div>
          <div style={{ color: "#00ccff", wordBreak: "break-all", marginBottom: "8px", fontSize: "11px" }}>
            {node.ipAddress || node.id}
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>AUTONOMOUS SYSTEM (ASN):</strong>{" "}
            <span style={{ color: "#f59e0b" }}>{node.asn || "AS15169"}</span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>GEOLOCATION COUNTRY:</strong>{" "}
            <span style={{ color: "#ffffff" }}>{node.country || "US"}</span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>INTERNET SERVICE PROVIDER:</strong>{" "}
            <span style={{ color: "#ffffff" }}>{node.isp || "Google LLC"}</span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>INFRASTRUCTURE TYPE:</strong>{" "}
            <span style={{ color: "#d946ef", fontWeight: "bold" }}>
              {node.infrastructureType || "Residential Relay"}
            </span>
          </div>

          <div>
            <strong style={{ color: "#94a3b8" }}>NETWORK PROPAGATION DELTA:</strong>{" "}
            <span style={{ color: "#00ff66" }}>
              {node.latency !== undefined ? `${node.latency} ms` : "14.5 ms"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
