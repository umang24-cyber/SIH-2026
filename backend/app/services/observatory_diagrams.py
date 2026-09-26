"""Presentation metadata for flowcharts; contains no simulated telemetry."""


def diagram(identifier, title, kind, description, nodes, edges):
    return dict(
        id=identifier, label=title, kind=kind, description=description,
        nodes=[dict(id=key, label=name, description=detail) for key, name, detail in nodes],
        edges=[dict(id=f"{source}--{target}", source=source, target=target, label=text)
               for source, target, text in edges],
    )


def pipeline():
    return diagram("scenario_pipeline", "From data to explainable alerts", "architecture",
                   "Complete scenarios are scored; structural subgraphs localize evidence rather than receiving independent risk scores.", [
        ("ledger", "Blockchain transactions", "Multi-input/output ledger, BTC amounts, fees and timestamps."),
        ("telemetry", "Network telemetry", "Observed relay metadata, infrastructure and propagation timing."),
        ("ingestion", "Join & validate", "Correlate ledger and network records by transaction ID."),
        ("graph", "Scenario graph", "Construct wallet, transaction and observed relay relationships."),
        ("features", "46 scenario features", "Financial, structural, graph, timing, network and script features; target labels excluded."),
        ("binary", "Binary risk model", "Scenario-level illicit probability estimate; the primary alert-ranking signal."),
        ("typology", "Typology model", "Supporting pattern attribution; confidence does not change binary risk or queue ranking."),
        ("anomaly", "Anomaly context", "Isolation Forest unusualness, not a probability; breaks equal-risk ranking ties."),
        ("gate", "Risk threshold: 0.50", "Emit primary alerts only for scenarios at or above the binary risk threshold."),
        ("below", "Below alert threshold", "No primary alert; this is not proof that a scenario is licit."),
        ("evidence", "Localize structural evidence", "Find relevant chains and subgraphs inside a flagged parent scenario."),
        ("shap", "SHAP explanation", "Risk and typology feature contributions explain the parent scenario prediction."),
        ("alert", "Ranked alert & dossier", "Risk descending, anomaly descending, scenario ID ascending; human investigation follows."),
    ], [
        ("ledger", "ingestion", "On-chain records"), ("telemetry", "ingestion", "Relay records"),
        ("ingestion", "graph", "Validated scenario"), ("graph", "features", "Scenario structure"),
        ("features", "binary", "Feature vector"), ("features", "typology", "Feature vector"),
        ("features", "anomaly", "Context features"), ("binary", "gate", "Risk score"),
        ("gate", "below", "Risk < 0.50"), ("gate", "evidence", "Risk >= 0.50"),
        ("binary", "shap", "Binary contributions"), ("typology", "shap", "Typology contributions"),
        ("evidence", "alert", "Evidence regions"), ("shap", "alert", "Explanation"),
        ("typology", "alert", "Supporting attribution"), ("anomaly", "alert", "Tie-break context only"),
    ])


def patterns():
    return {"patterns": [
        diagram("peeling_chain", "Peeling chain", "illustration",
                "A continuing balance passes through successive wallets while smaller outputs branch off.", [
            ("source", "Source", "Conceptual starting wallet."),
            ("carry_1", "Carry wallet 1", "Carries the remaining balance."),
            ("carry_2", "Carry wallet 2", "Continues the chain."),
            ("carry_3", "Carry wallet 3", "Further continuation."),
            ("payout_1", "Small output 1", "Illustrative side output."),
            ("payout_2", "Small output 2", "Illustrative side output."),
            ("payout_3", "Small output 3", "Illustrative side output."),
        ], [("source", "carry_1", "Remainder"), ("source", "payout_1", "Side output"),
            ("carry_1", "carry_2", "Remainder"), ("carry_1", "payout_2", "Side output"),
            ("carry_2", "carry_3", "Remainder"), ("carry_2", "payout_3", "Side output")]),
        diagram("layering", "Layering", "illustration",
                "Funds fan out across intermediaries and reconverge at a consolidation wallet.", [
            ("source", "Source", "Conceptual source wallet."),
            ("branch_a", "Intermediary A", "One branch of the transfer graph."),
            ("branch_b", "Intermediary B", "Another branch of the transfer graph."),
            ("branch_c", "Intermediary C", "Another branch of the transfer graph."),
            ("destination", "Consolidation", "Reconvergence of branches."),
        ], [("source", "branch_a", "Fan out"), ("source", "branch_b", "Fan out"),
            ("source", "branch_c", "Fan out"), ("branch_a", "destination", "Fan in"),
            ("branch_b", "destination", "Fan in"), ("branch_c", "destination", "Fan in")]),
        diagram("mixing", "Mixing / CoinJoin-like structure", "illustration",
                "Multiple inputs meet in a transaction with similar-denomination outputs. The structure alone does not establish illicit activity.", [
            ("input_a", "Input A", "Conceptual participant."),
            ("input_b", "Input B", "Conceptual participant."),
            ("input_c", "Input C", "Conceptual participant."),
            ("transaction", "Multi-party transaction", "Joint input/output structure."),
            ("output_a", "Output A", "Similar-denomination output."),
            ("output_b", "Output B", "Similar-denomination output."),
            ("output_c", "Output C", "Similar-denomination output."),
        ], [("input_a", "transaction", "Input"), ("input_b", "transaction", "Input"),
            ("input_c", "transaction", "Input"), ("transaction", "output_a", "Output"),
            ("transaction", "output_b", "Output"), ("transaction", "output_c", "Output")]),
        diagram("ransomware", "Ransomware-like collection", "illustration",
                "A conceptual collection-and-consolidation motif; timing and other evidence are needed for interpretation.", [
            ("payer_a", "Payment source A", "Illustrative source, not an identified victim."),
            ("payer_b", "Payment source B", "Illustrative source, not an identified victim."),
            ("payer_c", "Payment source C", "Illustrative source, not an identified victim."),
            ("collector", "Collection wallet", "Receives clustered payments."),
            ("destination", "Consolidation wallet", "Receives collected funds."),
        ], [("payer_a", "collector", "Payment"), ("payer_b", "collector", "Payment"),
            ("payer_c", "collector", "Payment"), ("collector", "destination", "Consolidation")]),
    ]}
