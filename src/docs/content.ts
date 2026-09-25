import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import type { Root, RootContent, PhrasingContent } from 'mdast';
import handbook from '../../docs/DOCS.md?raw';

const navigation = [
  ['Getting started', 'Introduction', 'introduction'],
  ['Getting started', 'Local setup', 'setup'],
  ['Getting started', 'Your first investigation', 'quickstart'],
  ['Reference', 'Web terminal commands', 'commands'],
  ['Reference', 'Standalone CLI', 'cli'],
  ['Investigation', 'Upload & correlate data', 'ingestion'],
  ['Investigation', 'Graphs & transactions', 'graphs'],
  ['Investigation', 'ML scores & explanations', 'ml'],
  ['Investigation', 'Cases & reports', 'cases'],
  ['Developer guide', 'Architecture', 'architecture'],
  ['Developer guide', 'Local API reference', 'api'],
  ['Developer guide', 'Data & model versions', 'data-models'],
  ['Help', 'Troubleshooting', 'troubleshooting'],
  ['Help', 'FAQ & glossary', 'faq'],
  ['Project status', 'Deadlock Protocol', 'deadlock'],
] as const;

export interface DocHeading { id: string; title: string; depth: number }
export interface DocPage {
  number: number; group: string; label: string; slug: string; title: string;
  tree: Root; headings: DocHeading[]; text: string; minutes: number;
  searchSections: { title: string; id: string; text: string }[];
}

interface TextNode { type: string; value?: string; children?: TextNode[] }
export function nodeText(node: TextNode): string {
  return node.value ?? node.children?.map(nodeText).join(node.type === 'tableRow' ? ' · ' : ' ') ?? '';
}

export const reviewDate = handbook.match(/\*\*Reviewed:\*\* ([^,]+),/)?.[1] ?? 'See source handbook';
export const reviewRevision = handbook.match(/commit `([^`]+)`/)?.[1] ?? '';
export const groups = [...new Set(navigation.map(([group]) => group))];

// Parse the source once. Fenced code and tables remain structured Markdown;
// headings inside a shell example can never accidentally split a page.
const source = unified().use(remarkParse).use(remarkGfm).parse(handbook);
const sectionStarts = source.children.flatMap((node, index) => {
  const match = node.type === 'heading' && node.depth === 2 ? nodeText(node).match(/^(\d+)\. /) : null;
  return match ? [{ index, number: Number(match[1]) }] : [];
});

function linkSectionReferences(node: TextNode): void {
  if (!node.children || ['link', 'code', 'inlineCode'].includes(node.type)) return;
  node.children = node.children.flatMap(child => {
    if (child.type !== 'text' || !child.value) { linkSectionReferences(child); return [child]; }
    const result: TextNode[] = [];
    const matches = [...child.value.matchAll(/\bSection (\d+)\b/g)];
    let cursor = 0;
    for (const match of matches) {
      const target = navigation[Number(match[1]) - 1];
      if (!target) continue;
      result.push({ type: 'text', value: child.value.slice(cursor, match.index) });
      result.push({ type: 'link', url: `/docs/${target[2]}`, children: [{ type: 'text', value: match[0] }] } as PhrasingContent);
      cursor = match.index! + match[0].length;
    }
    result.push({ type: 'text', value: child.value.slice(cursor) });
    return result;
  });
}

export const pages: DocPage[] = navigation.map(([group, label, slug], index) => {
  const section = sectionStarts.find(section => section.number === index + 1);
  if (!section) throw new Error(`Missing documentation section ${index + 1}: ${label}`);
  const next = sectionStarts.find(candidate => candidate.index > section.index);
  const children = source.children.slice(section.index + 1, next?.index ?? source.children.length);
  const body: RootContent[] = [];
  let title = label as string;
  for (let i = 0; i < children.length; i++) {
    const node = children[i];
    if (node.type === 'heading') {
      const heading = nodeText(node);
      if (heading === 'Page title' && children[i + 1]?.type === 'paragraph') {
        title = nodeText(children[++i]);
        continue;
      }
      if (heading === 'Short description') continue;
      if (heading === 'Suggested links') node.children = [{ type: 'text', value: 'Continue exploring' }];
    }
    body.push(node);
  }
  while (body[body.length - 1]?.type === 'thematicBreak') body.pop();
  const tree: Root = { type: 'root', children: body };
  linkSectionReferences(tree);
  const usedIds = new Map<string, number>();
  const headings: DocHeading[] = [];
  const searchSections = [{ title: label as string, id: '', text: '' }];
  let currentSection = searchSections[0];
  for (const node of body) {
    if (node.type === 'heading') {
      const text = nodeText(node).replace(/^\d+(?:\.\d+)*\.?\s+/, '');
      node.children = [{ type: 'text', value: text }];
      const base = text.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-') || 'section';
      const count = usedIds.get(base) ?? 0;
      usedIds.set(base, count + 1);
      const id = count ? `${base}-${count}` : base;
      node.depth = Math.max(2, node.depth - 1) as 2 | 3 | 4 | 5;
      node.data = { ...node.data, hProperties: { id } };
      headings.push({ id, title: text, depth: node.depth });
      currentSection = { title: text, id, text: '' };
      searchSections.push(currentSection);
    } else {
      currentSection.text += `${nodeText(node)}\n`;
    }
  }
  const text = body.map(nodeText).join('\n');
  return { number: index + 1, group, label, slug, title, tree, headings, text, minutes: Math.max(1, Math.ceil(text.split(/\s+/).length / 220)), searchSections };
});

export interface SearchResult { page: DocPage; title: string; href: string; excerpt: string; score: number }
export function searchDocs(query: string): SearchResult[] {
  const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  return pages.flatMap(page => page.searchSections.flatMap(section => {
    const title = `${page.label} ${section.title}`.toLowerCase();
    const body = section.text.toLowerCase();
    if (!terms.every(term => `${title} ${body}`.includes(term))) return [];
    const score = terms.reduce((sum, term) => sum + (title.includes(term) ? 10 : 1), 0);
    const firstHit = Math.max(0, body.indexOf(terms.find(term => body.includes(term)) ?? ''));
    const start = Math.max(0, firstHit - 65);
    const excerpt = `${start ? '…' : ''}${section.text.slice(start, start + 190).replace(/\s+/g, ' ')}${section.text.length > start + 190 ? '…' : ''}`;
    return [{ page, title: section.title, href: `/docs/${page.slug}${section.id ? `#${section.id}` : ''}`, excerpt, score }];
  })).sort((a, b) => b.score - a.score).slice(0, 24);
}

export function resolveDocLink(href: string): string {
  if (/^(https?:|mailto:|#|\/)/.test(href)) return href;
  // Repository-relative citations are source links, not application routes.
  const sourcePath = new URL(href, 'https://source.local/docs/DOCS.md');
  return `https://github.com/umang24-cyber/SIH-2026/blob/cli${sourcePath.pathname}${sourcePath.hash}`;
}
