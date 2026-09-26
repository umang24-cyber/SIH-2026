export type Metric = { id: string; label: string; value: number; unit: 'ratio' };
export type Item = { id: string; label: string; count: number };
export type Meta = {
  sources: string[]; scope: string; dataset_version: string | null;
  model_version: string | null; synthetic: boolean; generated_at: string; notes: string[];
};
export type Envelope<T> = {
  schema_version: '1.0'; status: 'available' | 'unavailable'; meta: Meta;
  data: T | null; message: string | null;
};
export type Overview = {
  title: string; model_role: string; evaluation_date: string;
  transactions: number; scenarios: number; train_scenarios: number; test_scenarios: number;
  features: number; binary_model: string; typology_model: string;
  headline_metrics: Metric[]; formal_decision: string | null; sections: string[];
};
export type Dataset = {
  totals: { transactions: number; scenarios: number; unique_wallets: number; first_timestamp: string; last_timestamp: string };
  splits: { id: string; label: string; transactions: number; scenarios: number }[];
  bucket: 'day' | 'week' | 'month'; timezone: 'UTC';
  timeline: { timestamp: string; transactions: number; output_volume_btc: number }[];
  scenario_class_distribution: Item[]; scenario_binary_distribution: Item[];
  transaction_class_distribution: Item[]; infrastructure_distribution: Item[];
  country_distribution: Item[]; script_distribution: Item[];
};
export type Confusion = { labels: string[]; values: number[][]; row_axis: 'actual'; column_axis: 'predicted' };
export type ModelPerformance = {
  sample_count: number; metrics: Metric[]; confusion_matrix: Confusion | null;
  per_class: { id: string; label: string; precision: number; recall: number; f1: number; support: number; predicted_count: number }[];
};
export type Performance = {
  evaluation_date: string; evaluation_type: string; scoring_unit: string; threshold: number;
  binary: ModelPerformance; typology: ModelPerformance;
  diagnostics: { id: string; label: string; metrics: Metric[]; note: string }[];
  formal_decision: string | null; limitations: string[];
  curves_available: boolean; curves_unavailable_reason: string;
};
export type Feature = { id: string; label: string; group: string; importance: number };
export type Features = {
  model: 'binary' | 'typology'; method: string; description: string; feature_count: number;
  features: Feature[]; groups: Feature[]; local_shap_available: boolean; local_shap_unavailable_reason: string;
};
export type Diagram = {
  id: string; label: string; kind: 'architecture' | 'illustration'; description: string;
  nodes: { id: string; label: string; description: string }[];
  edges: { id: string; source: string; target: string; label: string }[];
};
export type Patterns = { patterns: Diagram[] };
