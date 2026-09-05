"""
graph_engine — SIH PS 146 Bitcoin AML Graph Engineering Package
================================================================
Builds the entity/transaction graph from blockchain + network metadata CSVs,
detects laundering-typology candidate structures (peeling chains, layering,
mixing clusters), extracts feature vectors for the downstream ML classifier,
and exports a dashboard-ready JSON for the frontend.

Entry point: python -m graph_engine.main
"""
