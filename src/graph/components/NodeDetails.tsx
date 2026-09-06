import type { GraphNode } from "../../types/graph";

interface NodeDetailsProps {
  node: GraphNode | null;
}

export default function NodeDetails({
  node,
}: NodeDetailsProps) {
  if (!node) {
    return null;
  }

  const formatRiskScore = (
    score: number | undefined
  ) => {
    if (score === undefined) {
      return "N/A";
    }

    return score.toFixed(2);
  };

  return (
    <div
      style={{
        position: "absolute",
        top: "20px",
        right: "20px",
        width: "300px",
        background: "#050505",
        border: "1px solid #00cc66",
        padding: "16px",
        fontFamily: "monospace",
        color: "#ffffff",
        zIndex: 10,
      }}
    >
      <div
        style={{
          color: "#00cc66",
          fontWeight: "700",
          marginBottom: "12px",
        }}
      >
        NODE DETAILS
      </div>

      <div
        style={{
          marginBottom: "8px",
        }}
      >
        <strong>TYPE:</strong> {node.type}
      </div>

      <div
        style={{
          marginBottom: "12px",
        }}
      >
        <strong>LABEL:</strong> {node.label}
      </div>

      {node.mlAnalysisStatus && (
        <div
          style={{
            color: node.mlAnalysisStatus === "AVAILABLE" ? "#33ff88" : "#ffaa33",
            marginBottom: "12px",
          }}
        >
          <strong>ML ANALYSIS:</strong> {node.mlAnalysisStatus}
          {node.mlAnalysisMessage && (
            <div style={{ fontSize: "11px", marginTop: "4px", lineHeight: 1.35 }}>
              {node.mlAnalysisMessage}
            </div>
          )}
          <div style={{ fontSize: "11px", marginTop: "4px" }}>
            <strong>NODE-LEVEL ML SCORE:</strong> NOT COMPUTED
          </div>
          {node.mlAnalysisStatus === "AVAILABLE" && (
            <div style={{ fontSize: "11px", marginTop: "4px" }}>
              <strong>SCENARIO BINARY P(illicit):</strong> {node.binaryConfidence !== undefined ? `${(node.binaryConfidence * 100).toFixed(2)}%` : "N/A"}
              {" | "}
              <strong>SCENARIO TYPOLOGY:</strong> {node.isIllicit && node.typologyConfidence !== undefined ? `${(node.typologyConfidence * 100).toFixed(2)}%` : "N/A — not applicable"}
            </div>
          )}
          {node.mlAnalysisStatus === "AVAILABLE" && (
            <div style={{ fontSize: "11px", marginTop: "4px" }}>
              <strong>ANOMALY / UNUSUALNESS:</strong> {node.anomalyScore !== undefined ? `${node.anomalyScore} / 100 [${node.anomalyLabel || "UNLABELED"}] — not probability` : "N/A"}
            </div>
          )}
        </div>
      )}

      {/* WALLET DETAILS */}
      {node.type === "WALLET" && (
        <>
          <div>
            <strong>ADDRESS:</strong>
          </div>

          <div
            style={{
              color: "#00cc66",
              wordBreak: "break-all",
              marginBottom: "10px",
            }}
          >
            {node.address}
          </div>

          <div>
            <strong>TRANSACTION COUNT:</strong>{" "}
            {node.transactionCount ?? "N/A"}
          </div>

          <div>
            <strong>SCENARIO RISK SCORE:</strong>{" "}
            {node.mlAnalysisStatus === "AVAILABLE" ? formatRiskScore(node.riskScore) : "N/A — unavailable"}
          </div>

          <div>
            <strong>CLUSTER ID:</strong>{" "}
            {node.clusterId ?? "N/A"}
          </div>

          <div>
            <strong>TAGS:</strong>{" "}
            {node.tags?.length
              ? node.tags.join(", ")
              : "N/A"}
          </div>

          <div>
            <strong>FIRST SEEN:</strong>{" "}
            {node.firstSeen ?? "N/A"}
          </div>

          <div>
            <strong>LAST SEEN:</strong>{" "}
            {node.lastSeen ?? "N/A"}
          </div>
        </>
      )}

      {/* TRANSACTION DETAILS */}
      {node.type === "TRANSACTION" && (
        <>
          <div>
            <strong>TXID:</strong>
          </div>

          <div
            style={{
              color: "#ff9900",
              wordBreak: "break-all",
              marginBottom: "10px",
            }}
          >
            {node.txid}
          </div>

          <div>
            <strong>AMOUNT (BTC):</strong>{" "}
            {node.amountBtc ?? "N/A"}
          </div>

          <div>
            <strong>FEE (BTC):</strong>{" "}
            {node.feeBtc ?? "N/A"}
          </div>

          <div>
            <strong>TIMESTAMP:</strong>{" "}
            {node.timestamp ?? "N/A"}
          </div>

          <div>
            <strong>INPUT COUNT:</strong>{" "}
            {node.inputCount ?? "N/A"}
          </div>

          <div>
            <strong>OUTPUT COUNT:</strong>{" "}
            {node.outputCount ?? "N/A"}
          </div>

          <div>
            <strong>SCENARIO RISK SCORE:</strong>{" "}
            {node.mlAnalysisStatus === "AVAILABLE" ? formatRiskScore(node.riskScore) : "N/A — unavailable"}
          </div>

          <div>
            <strong>NODE-LEVEL CONFIDENCE:</strong> NOT COMPUTED
          </div>

          <div>
            <strong>CLUSTER ID:</strong>{" "}
            {node.clusterId ?? "N/A"}
          </div>

          <div>
            <strong>PATTERN TAGS:</strong>{" "}
            {node.patternTags?.length
              ? node.patternTags.join(", ")
              : "N/A"}
          </div>
        </>
      )}

      {/* IP DETAILS */}
      {node.type === "IP" && (
        <>
          <div>
            <strong>IP ADDRESS:</strong>{" "}
            {node.ipAddress}
          </div>

          <div>
            <strong>ASN:</strong>{" "}
            {node.asn ?? "N/A"}
          </div>

          <div>
            <strong>COUNTRY:</strong>{" "}
            {node.country ?? "N/A"}
          </div>

          <div>
            <strong>ISP:</strong>{" "}
            {node.isp ?? "N/A"}
          </div>

          <div>
            <strong>INFRASTRUCTURE:</strong>{" "}
            {node.infrastructureType ?? "N/A"}
          </div>

          <div>
            <strong>SCENARIO RISK SCORE:</strong>{" "}
            {formatRiskScore(node.riskScore)}
          </div>

          <div>
            <strong>CLUSTER ID:</strong>{" "}
            {node.clusterId ?? "N/A"}
          </div>

          <div>
            <strong>LATENCY:</strong>{" "}
            {node.latency !== undefined
              ? `${node.latency} ms`
              : "N/A"}
          </div>
        </>
      )}
    </div>
  );
}
