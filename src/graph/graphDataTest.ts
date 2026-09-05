import { FORENSIC_SCENARIOS } from "../data/forensicScenarios";
import { adaptScenarioToGraphData } from "../adapters/forensicGraphAdapter";

const scenario = FORENSIC_SCENARIOS.peel_001;

export const testGraphData = adaptScenarioToGraphData(
  scenario.nodes,
  scenario.edges
);