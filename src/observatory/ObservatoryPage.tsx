import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, ArrowUpRight } from 'lucide-react';
import { useObservatoryResource } from './useObservatoryResource';
import type { Dataset, Diagram, Features, Item, Metric, ModelPerformance, Overview, Patterns, Performance } from './types';
import { SectionState, date, number, percent } from './components/SectionState';
import { Bars, Timeline } from './components/EditorialChart';
import { DirectedDiagram } from './components/DirectedDiagram';
import './ObservatoryPage.css';
import { ScrambleNumber } from '../motion/ScrambleNumber';
import { useReveal } from '../motion/useReveal';

const sections = [['dataset', 'The dataset'], ['pipeline', 'How it works'], ['performance', 'Performance'], ['features', 'Model signals'], ['patterns', 'Pattern atlas']] as const;
const metricHelp: Record<string, string> = {
  precision: 'Of scenarios flagged as illicit, the fraction correctly identified.',
  recall: 'Of all illicit test scenarios, the fraction the model identified.',
  f1: 'The harmonic mean of precision and recall.',
  roc_auc: 'Separation of licit and illicit scenarios across decision thresholds.',
  pr_auc: 'Area under the precision–recall curve; a saved scalar, not curve coordinates.',
  accuracy: 'The fraction of evaluated scenarios classified correctly.',
  bacc: 'Recall averaged across the binary classes.',
  balanced_accuracy: 'Recall averaged across classes.',
  macro_f1: 'F1 averaged equally across typology classes.',
  weighted_f1: 'F1 averaged across classes, weighted by their support.',
};
const itemBars = (items: Item[]) => items.map(item => ({ ...item, value: item.count }));

function Heading({ index, title, subtitle }: { index: string; title: string; subtitle: string }) {
  const reveal = useReveal<HTMLElement>(index, 600);
  return <header ref={reveal.ref} data-reveal={reveal.phase} className="obs-section-heading"><span className="eyebrow">{index} / The Observatory</span><div><h2>{title}</h2><p>{subtitle}</p></div></header>;
}

function Metrics({ metrics }: { metrics: Metric[] }) {
  return <div className="obs-metrics">{metrics.map(metric => <details className="obs-metric" key={metric.id}><summary><span className="eyebrow">{metric.label.replace(/_/g, ' ')}</span><strong><ScrambleNumber value={metric.id.includes('auc') ? metric.value.toFixed(4) : percent(metric.value)} /></strong><span className="obs-metric-hint">About this measure <span aria-hidden="true">+</span></span></summary><p>{metricHelp[metric.id] || 'Saved evaluation measure for the selected model.'}</p></details>)}</div>;
}

function DatasetSection() {
  const [bucket, setBucket] = useState<'day' | 'week' | 'month'>('month');
  const [volume, setVolume] = useState(false);
  const [distribution, setDistribution] = useState<'infrastructure_distribution' | 'country_distribution' | 'script_distribution'>('infrastructure_distribution');
  const resource = useObservatoryResource<Dataset>(`dataset?bucket=${bucket}`);
  return <section id="dataset" className="obs-section">
    <Heading index="01" title="The shape of the data." subtitle="Every result begins with a dataset. Here is ours, in perspective." />
    <div className="obs-control-line"><span className="eyebrow">Activity across the ledger</span><div className="obs-controls"><label>Period<select aria-label="Timeline period" value={bucket} disabled={resource.loading} onChange={event => setBucket(event.target.value as typeof bucket)}><option value="day">Daily</option><option value="week">Weekly</option><option value="month">Monthly</option></select></label><label>Measure<select aria-label="Timeline measure" disabled={resource.loading} value={volume ? 'volume' : 'transactions'} onChange={event => setVolume(event.target.value === 'volume')}><option value="transactions">Transactions</option><option value="volume">Output volume (BTC)</option></select></label></div></div>
    <SectionState resource={resource} label="Dataset">{data => <>
      <div className="obs-dataset-lead"><div><Timeline key={bucket} dataset={data} volume={volume} /></div><aside className="obs-at-a-glance"><span className="eyebrow">The ledger, at a glance</span><dl><div><dt>Transactions</dt><dd><ScrambleNumber value={number(data.totals.transactions)} /></dd></div><div><dt>Scenarios</dt><dd><ScrambleNumber value={number(data.totals.scenarios)} /></dd></div><div><dt>Unique wallets</dt><dd><ScrambleNumber value={number(data.totals.unique_wallets)} /></dd></div></dl><p>{date(data.totals.first_timestamp)} — {date(data.totals.last_timestamp)}<br />Bundled train + test · UTC</p></aside></div>
      <div className="obs-three-columns"><article><h3>A considered split</h3><p className="obs-caption">Training and held-out testing, by scenario.</p><div className="obs-split-bar" aria-hidden="true">{data.splits.map(split => <span key={split.id} style={{ flex: split.scenarios }} />)}</div><dl className="obs-split-legend">{data.splits.map(split => <div key={split.id}><dt>{split.label}</dt><dd>{number(split.scenarios)} scenarios<br /><small>{number(split.transactions)} transactions</small></dd></div>)}</dl><Bars label="Licit and illicit ground truth" items={itemBars(data.scenario_binary_distribution)} /><p className="obs-caption">Dataset ground truth; not predictions.</p></article>
        <article><h3>A spectrum of scenarios</h3><p className="obs-caption">Scenario class counts, each scenario counted once.</p><Bars label="Scenario class distribution" items={itemBars(data.scenario_class_distribution)} /></article>
        <article><h3>Beyond the ledger</h3><label className="obs-inline-select">Breakdown<select aria-label="Dataset breakdown" value={distribution} onChange={event => setDistribution(event.target.value as typeof distribution)}><option value="infrastructure_distribution">Infrastructure</option><option value="country_distribution">Country codes</option><option value="script_distribution">Script types</option></select></label><Bars label="Dataset secondary distribution" items={itemBars(data[distribution])} /><p className="obs-caption">{distribution === 'script_distribution' ? 'Transaction rows by script type.' : 'Network observations joined to transactions.'}</p></article></div>
    </>}</SectionState>
  </section>;
}

function ModelReport({ model, label, ids }: { model: ModelPerformance; label: string; ids: string[] }) {
  const metrics = ids.flatMap(id => model.metrics.filter(metric => metric.id === id));
  return <article className="obs-model-report"><span className="eyebrow">{number(model.sample_count)} evaluated scenarios</span><h3>{label}</h3><Bars label={`${label} summary metrics`} items={metrics.map(metric => ({ ...metric, label: metric.label.replace(/_/g, ' '), value: metric.value }))} ratio scaleToOne />
    <details className="obs-data-table"><summary>All saved metrics & definitions</summary><dl className="obs-definitions">{model.metrics.map(metric => <div key={metric.id}><dt>{metric.label.replace(/_/g, ' ')} <strong>{metric.id.includes('auc') ? metric.value.toFixed(4) : percent(metric.value)}</strong></dt><dd>{metricHelp[metric.id] || 'Saved evaluation metric.'}</dd></div>)}</dl></details>
    {model.confusion_matrix ? <div className="obs-table-scroll" tabIndex={0}><table className="obs-confusion"><caption>{label} confusion matrix · rows actual / columns predicted</caption><thead><tr><th>Actual ↓ / Predicted →</th>{model.confusion_matrix.labels.map(value => <th key={value}>{value}</th>)}</tr></thead><tbody>{model.confusion_matrix.values.map((row, i) => <tr key={i}><th>{model.confusion_matrix!.labels[i]}</th>{row.map((value, j) => <td key={j} style={{ background: `rgba(70,81,59,${.06 + .3 * value / Math.max(...model.confusion_matrix!.values.flat(), 1)})` }}>{number(value)}</td>)}</tr>)}</tbody></table></div> : <p className="obs-caption obs-missing">Confusion matrix and per-class breakdown are not present in this model’s saved report.</p>}
    {model.per_class.length > 0 && <details className="obs-data-table"><summary>Per-class results</summary><div className="obs-table-scroll" tabIndex={0}><table><thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr></thead><tbody>{model.per_class.map(entry => <tr key={entry.id}><th>{entry.label}</th><td>{percent(entry.precision)}</td><td>{percent(entry.recall)}</td><td>{percent(entry.f1)}</td><td>{number(entry.support)}</td></tr>)}</tbody></table></div></details>}
  </article>;
}

function PerformanceSection() {
  const resource = useObservatoryResource<Performance>('performance');
  return <section id="performance" className="obs-section"><Heading index="03" title="Results, with perspective." subtitle="Two different questions. Two models. One carefully scoped benchmark." />
    <SectionState resource={resource} label="Performance">{(data, meta) => <>
      <div className="obs-edition-line"><span>Model {meta.model_version?.toUpperCase() || 'unavailable'}</span><span>{meta.synthetic ? 'Synthetic-data benchmark' : 'Saved benchmark'}</span><span>Evaluated {date(data.evaluation_date)}</span><span>Risk threshold {data.threshold.toFixed(2)}</span></div>
      <div className="obs-two-columns"><ModelReport model={data.binary} label="Is the scenario illicit?" ids={['precision', 'recall', 'f1']} /><ModelReport model={data.typology} label="Which pattern does it resemble?" ids={['macro_f1', 'accuracy', 'weighted_f1']} /></div>
      <div className="obs-methodology"><div><span className="eyebrow">The small print matters</span><h3>Read the results in context.</h3><p>{data.evaluation_type}. Scoring unit: {data.scoring_unit}. The binary model evaluates all test scenarios; typology evaluates illicit test scenarios.</p><ul>{data.limitations.map(note => <li key={note}>{note}</li>)}</ul>{!data.curves_available && <p>{data.curves_unavailable_reason}</p>}{data.formal_decision && <p>{data.formal_decision}</p>}</div><aside>{data.diagnostics.map(diagnostic => <div key={diagnostic.id}><h4>{diagnostic.label}</h4><dl className="obs-diagnostics">{diagnostic.metrics.map(metric => <div key={metric.id}><dt>{metric.label}</dt><dd>{metric.value.toFixed(5)}</dd></div>)}</dl><p className="obs-caption">{diagnostic.note}</p></div>)}</aside></div>
    </>}</SectionState>
  </section>;
}

function FeaturesSection() {
  const [model, setModel] = useState<'binary' | 'typology'>('binary');
  const [limit, setLimit] = useState(15);
  const resource = useObservatoryResource<Features>(`features?model=${model}&limit=${limit}`);
  return <section id="features" className="obs-section"><Heading index="04" title="What matters to the model." subtitle="An inspection of the learned model, feature by feature." />
    <div className="obs-control-line"><div className="obs-tabs" role="group" aria-label="Feature model">{(['binary', 'typology'] as const).map(value => <button key={value} disabled={resource.loading} aria-pressed={model === value} onClick={() => setModel(value)}>{value === 'binary' ? 'Binary detection' : 'Typology attribution'}</button>)}</div><label className="obs-inline-select">Show<select aria-label="Number of features" value={limit} disabled={resource.loading} onChange={event => setLimit(Number(event.target.value))}><option value={15}>Top 15 features</option><option value={46}>All features</option></select></label></div>
    <SectionState resource={resource} label="Feature importance">{data => <div className="obs-feature-layout"><div><h3>XGBoost gain <em>(global importance)</em></h3><Bars label="Feature importance" items={data.features.map(feature => ({ ...feature, value: feature.importance }))} ratio /><p className="obs-caption">Fig. 03 — {data.features.length} of {data.feature_count} features. Normalized over all features; a shortened list need not sum to 100%.</p></div><aside><span className="eyebrow">The broader signals</span><h3>Importance by family</h3><Bars label="Feature group importance" items={data.groups.map(group => ({ ...group, value: group.importance }))} ratio scaleToOne /><div className="obs-editor-note"><span className="eyebrow">An editor’s note</span><p>{data.description}</p><p>{data.local_shap_unavailable_reason}</p></div><details className="obs-data-table"><summary>Feature families</summary><dl className="obs-definitions">{data.features.map(feature => <div key={feature.id}><dt>{feature.label}</dt><dd>{feature.group} · {percent(feature.importance)}</dd></div>)}</dl></details></aside></div>}</SectionState>
  </section>;
}

export function ObservatoryPage({ entering = false, onEnterCLI }: { entering?: boolean; onEnterCLI: () => void }) {
  const overview = useObservatoryResource<Overview>('overview');
  const pipeline = useObservatoryResource<Diagram>('pipeline');
  const patterns = useObservatoryResource<Patterns>('patterns');
  const shell = useRef<HTMLDivElement>(null);
  const wasEntering = useRef(entering);
  const [activeSection, setActiveSection] = useState('');
  useEffect(() => { document.title = 'The Observatory — BitKaun'; }, []);
  useEffect(() => {
    if (shell.current) {
      shell.current.inert = entering;
      if (wasEntering.current && !entering) shell.current.querySelector<HTMLElement>('.obs-masthead h1')?.focus({ preventScroll: true });
    }
    wasEntering.current = entering;
  }, [entering]);
  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) setActiveSection(entry.target.id); });
    }, { root: shell.current, rootMargin: '-10% 0px -65% 0px' });
    shell.current?.querySelectorAll('.obs-section').forEach(section => observer.observe(section));
    return () => observer.disconnect();
  }, []);
  return <div className="editorial obs-shell" ref={shell} aria-hidden={entering || undefined}>
    <a className="skip-link" href="#observatory-main">Skip to the edition</a>
    <div className="obs-paper">
      <header className="obs-topline"><Link className="brand" to="/">BitKaun<span>?</span></Link><span className="eyebrow">An independent look inside the intelligence.</span><nav aria-label="Observatory navigation"><Link to="/">Home</Link><Link to="/docs/introduction">Field Guide</Link><button onClick={onEnterCLI}>Terminal <ArrowUpRight size={14} /></button></nav></header>
      <main id="observatory-main" tabIndex={-1}>
        <header className="obs-masthead"><div className="obs-masthead-kicker"><span>Data, examined.</span><span>A BitKaun special edition</span><span>Evidence, understood.</span></div><h1 tabIndex={-1}>The Observatory</h1><div className="obs-masthead-bottom"><span>MODEL & DATA JOURNAL</span><span>LOCAL-FIRST INTELLIGENCE</span><span>THE ANALYTICS EDITION</span></div></header>
        <section className="obs-front-page" aria-labelledby="obs-front-title"><div className="obs-front-copy"><span className="eyebrow">Behind the predictions</span><h2 id="obs-front-title">Inside the<br /><em>intelligence.</em></h2><p>A closer reading of our data, the patterns within it, and the models learning to follow the evidence.</p><a href="#dataset" className="obs-read-link">Explore the edition <ArrowDown size={15} /></a></div><div className="obs-front-results"><div className="obs-results-heading"><span className="eyebrow">The benchmark, in brief</span><span className="obs-seal">Saved<br /><em>evaluation</em></span></div><SectionState resource={overview} label="Benchmark overview">{(data, meta) => <><Metrics metrics={data.headline_metrics} /><div className="obs-edition-line"><span>{meta.model_version?.toUpperCase()}</span><span>{number(data.features)} features</span><span>Evaluated {date(data.evaluation_date)}</span></div><p className="obs-caption">{meta.synthetic ? 'Held-out synthetic scenarios. These results do not establish real-world detection performance.' : 'Saved evaluation results.'}</p></>}</SectionState></div></section>
        <nav className="obs-section-index" aria-label="Edition sections"><span className="eyebrow">In this edition</span>{sections.map(([id, label], index) => <a href={`#${id}`} key={id} aria-current={activeSection === id ? 'location' : undefined}><small>0{index + 1}</small>{label}</a>)}</nav>
        <DatasetSection />
        <section id="pipeline" className="obs-section"><Heading index="02" title="From records to reasons." subtitle="Follow a scenario through the architecture, from raw observations to explainable alerts." /><SectionState resource={pipeline} label="System architecture">{data => <><DirectedDiagram diagram={data} /><p className="obs-caption">Fig. 02 — {data.label}. Static architecture; select an arrow to read its connection label.</p></>}</SectionState></section>
        <PerformanceSection />
        <FeaturesSection />
        <section id="patterns" className="obs-section"><Heading index="05" title="An atlas of patterns." subtitle="Four structures worth understanding. A visual field guide to the shapes transactions can take." /><SectionState resource={patterns} label="Pattern atlas">{data => <div className="obs-pattern-grid">{data.patterns.map((pattern, i) => <article key={pattern.id}><div className="obs-pattern-byline"><span className="eyebrow">Plate {String(i + 1).padStart(2, '0')}</span><span className="obs-badge">Illustration</span></div><h3>{pattern.label}</h3><p>{pattern.description}</p><DirectedDiagram diagram={pattern} compact /></article>)}</div>}</SectionState></section>
        <section className="obs-closing"><span className="eyebrow">The next chapter is yours</span><h2>From understanding<br />to <em>investigation.</em></h2><p>Take a closer look at the loaded data in the investigative workspace.</p><button className="editorial-button" onClick={onEnterCLI}>Open the terminal <ArrowUpRight size={18} /></button></section>
      </main>
      <footer className="obs-colophon"><Link className="brand" to="/">BitKaun<span>?</span></Link><span>THE OBSERVATORY · MODEL & DATA JOURNAL</span><a href="#observatory-main">Back to the masthead ↑</a></footer>
    </div>
  </div>;
}
