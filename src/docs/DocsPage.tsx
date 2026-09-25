import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useNavigationType } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, ChevronDown, Menu, Search, X } from 'lucide-react';
import { groups, pages, reviewDate, reviewRevision, searchDocs, type DocPage } from './content';
import { DocMarkdown } from './DocMarkdown';
import './docs.css';

function Navigation({ page, onNavigate }: { page?: DocPage; onNavigate?: () => void }) {
  return <nav className="docs-navigation" aria-label="Documentation chapters">
    {groups.map(group => <div className="docs-nav-group" key={group}><h2>{group}</h2>
      {pages.filter(candidate => candidate.group === group).map(candidate => <Link key={candidate.slug} to={`/docs/${candidate.slug}`} aria-current={page?.slug === candidate.slug ? 'page' : undefined} onClick={onNavigate}><span>{String(candidate.number).padStart(2, '0')}</span>{candidate.label}{candidate.slug === 'deadlock' && <i aria-label="Planned" />}</Link>)}
    </div>)}
  </nav>;
}

export function DocsPage({ onEnterCLI }: { onEnterCLI: () => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const navigationType = useNavigationType();
  const slug = location.pathname.replace(/^\/docs\/?/, '').replace(/\/$/, '') || 'introduction';
  const page = pages.find(page => page.slug === slug);
  const scrollRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const savedScroll = useRef(new Map<string, number>());
  const searchDialog = useRef<HTMLDialogElement>(null);
  const menuDialog = useRef<HTMLDialogElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const [activeHeading, setActiveHeading] = useState('');
  const results = useMemo(() => searchDocs(query), [query]);
  const previous = page ? pages[page.number - 2] : undefined;
  const next = page ? pages[page.number] : undefined;

  const openSearch = () => { searchDialog.current?.showModal(); searchInput.current?.focus(); };
  const closeSearch = () => searchDialog.current?.close();
  const openResult = (href: string) => { closeSearch(); navigate(href); };

  useEffect(() => {
    document.title = `${page?.label ?? 'Page not found'} — BitKaun Field Guide`;
  }, [page]);

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault(); openSearch();
      }
    };
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);

  useLayoutEffect(() => {
    const root = scrollRef.current;
    if (!root) return;
    menuDialog.current?.close();
    let hash = location.hash.slice(1);
    try { hash = decodeURIComponent(hash); } catch { /* Treat malformed hashes as missing anchors. */ }
    const heading = hash ? document.getElementById(hash) : null;
    if (heading) heading.scrollIntoView({ block: 'start' });
    else root.scrollTop = navigationType === 'POP' ? savedScroll.current.get(location.key) ?? 0 : 0;
    titleRef.current?.focus({ preventScroll: true });
    return () => { savedScroll.current.set(location.key, root.scrollTop); };
  }, [location.key, location.hash, page, navigationType]);

  useEffect(() => {
    const root = scrollRef.current;
    if (!root || !page) return;
    let frame = 0;
    const update = () => {
      const threshold = root.getBoundingClientRect().top + 155;
      const current = [...page.headings].reverse().find(heading => (document.getElementById(heading.id)?.getBoundingClientRect().top ?? Infinity) <= threshold);
      setActiveHeading(current?.id ?? '');
    };
    const onScroll = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); };
    update();
    root.addEventListener('scroll', onScroll, { passive: true });
    return () => { root.removeEventListener('scroll', onScroll); cancelAnimationFrame(frame); };
  }, [page]);

  const contents = <nav aria-label="On this page">{page?.headings.map(heading => <a key={heading.id} href={`#${heading.id}`} className={heading.depth > 2 ? 'docs-toc-nested' : ''} aria-current={activeHeading === heading.id ? 'location' : undefined}>{heading.title}</a>)}</nav>;

  return <div className="editorial docs-shell" ref={scrollRef}>
    <a className="skip-link" href="#docs-article">Skip to article</a>
    <header className="docs-header">
      <div className="docs-identity"><Link to="/" className="brand" aria-label="BitKaun home">BitKaun<span>?</span></Link><span className="docs-header-divider" /><Link to="/docs/introduction" className="docs-guide-name">Field Guide</Link></div>
      <button className="docs-search-trigger" onClick={openSearch} aria-label="Search the field guide"><Search size={16} /><span>Search the field guide…</span><kbd>Ctrl K</kbd></button>
      <button className="docs-terminal-link" onClick={onEnterCLI} aria-label="Open Terminal">Open Terminal <ArrowUpRight size={16} /></button>
      <button className="docs-menu-trigger" onClick={() => menuDialog.current?.showModal()} aria-label="Open chapter navigation"><Menu size={22} /></button>
    </header>

    <div className="docs-grid">
      <aside className="docs-sidebar"><Link to="/" className="docs-back-home"><ArrowLeft size={13} /> Back to the study</Link><Navigation page={page} /><div className="docs-sidebar-note"><span className="eyebrow">An investigator's companion</span><p>A little context.<br />A clearer perspective.</p><span className="docs-sidebar-mark" aria-hidden="true">{'{ ₿ }'}</span></div></aside>
      <main className="docs-main" id="docs-article" tabIndex={-1}>
        {page ? <>
          <div className="docs-breadcrumb eyebrow"><BookOpen size={13} /><span>{page.group}</span><span>/</span><span>{String(page.number).padStart(2, '0')}</span></div>
          <header className="docs-article-header">
            <p className="docs-chapter-label">{page.label}{page.slug === 'deadlock' && <span className="docs-planned">Planned</span>}</p>
            <h1 ref={titleRef} tabIndex={-1}>{page.title}</h1>
            <div className="docs-article-meta"><span>{page.minutes} min read</span><span>Content reviewed {reviewDate}</span></div>
          </header>
          {page.slug === 'introduction' && <div className="docs-welcome"><span className="eyebrow">Start with a little curiosity.</span><p>Your workspace, from the first command to the final finding.</p><div><Link to="/docs/setup">Set up locally <ArrowRight size={15} /></Link><Link to="/docs/quickstart">Your first investigation <ArrowRight size={15} /></Link></div><pre aria-hidden="true">{'   .------.\n  /  |||   \\\n |   |B|    |\n  \\  |||   /\n   `------\''}</pre></div>}
          {!!page.headings.length && <details className="docs-mobile-toc"><summary>On this page <ChevronDown size={15} /></summary>{contents}</details>}
          <article className="docs-prose" key={page.slug}><DocMarkdown page={page} /></article>
          <div className="docs-page-navigation">{previous ? <Link to={`/docs/${previous.slug}`}><span><ArrowLeft size={13} /> Previous chapter</span><strong>{previous.label}</strong></Link> : <Link to="/"><span><ArrowLeft size={13} /> Back to</span><strong>The study</strong></Link>}{next ? <Link to={`/docs/${next.slug}`}><span>Next chapter <ArrowRight size={13} /></span><strong>{next.label}</strong></Link> : <Link to="/docs/introduction"><span>Return to <ArrowRight size={13} /></span><strong>Introduction</strong></Link>}</div>
          <footer className="docs-article-footer"><span>BITKAUN? / THE FIELD GUIDE</span><span>Source review · {reviewRevision}</span></footer>
        </> : <div className="docs-not-found"><p className="eyebrow">404 / A missing page</p><h1 ref={titleRef} tabIndex={-1}>A small detour.</h1><p>This chapter doesn't exist. Find your way back through the guide or search for what you need.</p><Link className="editorial-button" to="/docs/introduction">Back to the introduction <ArrowRight size={16} /></Link></div>}
      </main>
      <aside className="docs-toc">{!!page?.headings.length && <><p className="eyebrow">On this page</p>{contents}</>}<div className="docs-toc-help"><span className="eyebrow">Need your bearings?</span><Link to="/docs/quickstart">Start an investigation <ArrowUpRight size={13} /></Link><Link to="/docs/troubleshooting">Troubleshooting <ArrowUpRight size={13} /></Link></div></aside>
    </div>

    <dialog className="docs-search-dialog editorial" ref={searchDialog} aria-labelledby="docs-search-title" onClick={event => { if (event.target === event.currentTarget) closeSearch(); }}>
      <div className="docs-search-content"><h2 className="sr-only" id="docs-search-title">Search the field guide</h2><div className="docs-search-input-row"><Search size={20} /><input ref={searchInput} value={query} placeholder="Search commands, setup, and concepts…" aria-label="Search documentation" aria-controls="docs-search-results" onChange={event => { setQuery(event.target.value); setSelected(0); }} onKeyDown={event => {
        if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
          event.preventDefault(); const nextIndex = Math.max(0, Math.min(results.length - 1, selected + (event.key === 'ArrowDown' ? 1 : -1))); setSelected(nextIndex); document.getElementById(`docs-result-${nextIndex}`)?.scrollIntoView({ block: 'nearest' });
        }
        if (event.key === 'Enter' && results[selected]) { event.preventDefault(); openResult(results[selected].href); }
      }} /><button onClick={closeSearch} aria-label="Close search"><X size={20} /></button></div>
      <div className="docs-search-results" id="docs-search-results"><p className="docs-search-status" role="status">{!query.trim() ? 'A good place to begin' : results.length ? `${results.length} matching sections` : `No results for “${query}”. Try “setup”, “alerts”, or “graph”.`}</p>
        {!query.trim() ? <div className="docs-search-suggestions">{['setup', 'quickstart', 'commands'].map(slug => { const page = pages.find(page => page.slug === slug)!; return <button key={slug} onClick={() => openResult(`/docs/${slug}`)}><BookOpen size={17} />{page.label}<ArrowRight size={15} /></button>; })}</div> : results.map((result, index) => <button id={`docs-result-${index}`} key={result.href} className={`docs-search-result${index === selected ? ' selected' : ''}`} onClick={() => openResult(result.href)}><span className="eyebrow">{result.page.group} / {result.page.label}</span><strong>{result.title}</strong><span>{result.excerpt}</span></button>)}
      </div><div className="docs-search-footer"><span>↑ ↓ navigate · Enter open</span><span>Esc to close</span></div></div>
    </dialog>
    <dialog className="docs-menu-dialog editorial" ref={menuDialog} aria-label="Documentation navigation" onClick={event => { if (event.target === event.currentTarget) menuDialog.current?.close(); }}><div><header><span className="brand">Field Guide</span><button onClick={() => menuDialog.current?.close()} aria-label="Close chapter navigation"><X size={20} /></button></header><Link className="docs-back-home" to="/">← Back to the study</Link><Navigation page={page} onNavigate={() => menuDialog.current?.close()} /></div></dialog>
  </div>;
}
