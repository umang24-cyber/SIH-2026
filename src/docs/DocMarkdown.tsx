import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Link } from 'react-router-dom';
import { Check, Copy, ArrowUpRight } from 'lucide-react';
import { type DocPage, resolveDocLink } from './content';

function textOf(children: React.ReactNode): string {
  return React.Children.toArray(children).map(child => typeof child === 'string' || typeof child === 'number' ? String(child) : React.isValidElement<{ children?: React.ReactNode }>(child) ? textOf(child.props.children) : '').join('');
}

function CodeBlock({ children, page }: { children?: React.ReactNode; page: DocPage }) {
  const code = textOf(children).replace(/\n$/, '');
  const element = React.Children.toArray(children).find(React.isValidElement) as React.ReactElement<{ className?: string }> | undefined;
  const language = element?.props.className?.replace('language-', '') ?? 'text';
  const labels: Record<string, string> = { bash: 'Bash / system shell', powershell: 'Windows PowerShell', python: 'Python', json: 'JSON', csv: 'CSV' };
  const label = labels[language] ?? (language === 'text' && ['setup', 'quickstart', 'commands', 'cases'].includes(page.slug) ? 'BitKaun terminal' : 'Plain text / example');
  const [status, setStatus] = useState<'idle' | 'copied' | 'failed'>('idle');
  const timer = useRef<ReturnType<typeof setTimeout>>();
  useEffect(() => () => clearTimeout(timer.current), []);
  const copy = async () => {
    try { await navigator.clipboard.writeText(code); setStatus('copied'); }
    catch { setStatus('failed'); }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setStatus('idle'), 3000);
  };
  return <div className="docs-code-block">
    <div className="docs-code-bar"><span>{label}</span><button onClick={copy} aria-label={`Copy ${label} example`}>{status === 'copied' ? <Check size={13} /> : <Copy size={13} />}<span aria-live="polite">{status === 'copied' ? 'Copied' : status === 'failed' ? 'Select & copy manually' : 'Copy'}</span></button></div>
    <pre tabIndex={0} aria-label={`${label} example`}>{children}</pre>
  </div>;
}

export function DocMarkdown({ page }: { page: DocPage }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm, () => () => page.tree]} components={{
    pre: ({ children }) => <CodeBlock page={page}>{children}</CodeBlock>,
    table: ({ children }) => <div className="docs-table-scroll" role="region" aria-label="Reference table" tabIndex={0}><table>{children}</table></div>,
    h2: ({ children, id }) => <h2 id={id}><a className="docs-heading-link" href={`#${id}`} aria-label={`Link to ${textOf(children)}`}>{children}<span aria-hidden="true">#</span></a></h2>,
    h3: ({ children, id }) => <h3 id={id}><a className="docs-heading-link" href={`#${id}`}>{children}<span aria-hidden="true">#</span></a></h3>,
    a: ({ href, children }) => {
      if (!href) return <span>{children}</span>;
      const url = resolveDocLink(href);
      if (url.startsWith('/docs/')) return <Link to={url}>{children}</Link>;
      if (url.startsWith('#')) return <a href={url}>{children}</a>;
      return <a href={url} target="_blank" rel="noreferrer">{children}<ArrowUpRight className="docs-external-icon" size={12} aria-label="opens in a new tab" /></a>;
    },
  }}>{''}</ReactMarkdown>;
}
