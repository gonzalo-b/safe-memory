#!/usr/bin/env node
/* Memory Design System · check-ds
 * The guard. Fails the build when product code steps outside the system.
 * Zero dependencies. Node 18+.
 *
 *   node memory-ds/scripts/check-ds.mjs src app components
 *   node memory-ds/scripts/check-ds.mjs --json src        machine-readable
 *
 * What it refuses, and why:
 *   raw-colour     a hex, rgb(), hsl(), lch() or oklch() literal. Use a --m- token.
 *   border         any drawn border, divide or outline. Memory is borderless.
 *   shadow         a box-shadow that is not a token. Only floating surfaces cast one.
 *   radius         a literal radius. Use the --m-radius- ladder.
 *   font           a font-family that is not a --m-font- token.
 *   tw-arbitrary   a Tailwind arbitrary colour, shadow or radius: bg-[#fff], rounded-[10px].
 *   tw-palette     a stock Tailwind palette class: bg-slate-900, text-red-500.
 *
 * A line that carries the comment  ds-allow: <reason>  is skipped. The reason is mandatory,
 * and every use is printed at the end so exceptions stay visible.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname, relative } from 'node:path';

const args = process.argv.slice(2);
const asJson = args.includes('--json');
const roots = args.filter((a) => !a.startsWith('--'));
if (!roots.length) { console.error('usage: check-ds.mjs [--json] <dir|file> [...]'); process.exit(2); }

const STYLE = new Set(['.css', '.scss', '.pcss', '.less']);
const MARKUP = new Set(['.tsx', '.jsx', '.ts', '.js', '.mjs', '.html', '.vue', '.svelte', '.astro', '.mdx']);
const SKIP_DIR = /(^|\/)(node_modules|\.next|\.git|dist|build|out|coverage|memory-ds|Memory Design System)(\/|$)/;
const PALETTE = 'slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|black|white';

const RULES = [
  { id: 'raw-colour', where: 'all', re: /(?<![&\w#/-])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b(?![\w-])/, skip: /(href|xlink:href|url\()\s*=?\s*["'(]?#|#m-i-/, msg: 'raw hex colour. Use var(--m-…) or a theme utility.' },
  { id: 'raw-colour', where: 'all', re: /\b(?:rgba?|hsla?|lch|oklch|lab|oklab)\(\s*[\d.]/, msg: 'raw colour function. Use var(--m-…).' },
  { id: 'border', where: 'style', re: /(?<![\w-])(?:border(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?(?:-width)?|outline)\s*:(?!\s*(?:0\b|none\b|inherit\b|unset\b|initial\b))[^;]+/, msg: 'a drawn border or outline. Separate with a surface step or a fill. Focus uses var(--m-ring).' },
  { id: 'border', where: 'markup', re: /(?<=[\s"'`:])(?:border(?:-[trblxyse])?(?:-(?:[1-9]\d*|\[[^\]]+\]))?|divide-[xy](?:-\d+)?|outline(?:-(?:[1-9]\d*|dashed|dotted|double))?)(?=[\s"'`])/, skip: /border-(?:0|none|transparent)|outline-(?:0|none|hidden)/, msg: 'a Tailwind border, divide or outline utility. Memory is borderless.' },
  { id: 'shadow', where: 'style', re: /box-shadow\s*:(?!\s*(?:none\b|inherit\b|var\(--m-))[^;]+/, msg: 'a literal box-shadow. Use var(--m-shadow-float), var(--m-shadow-sheet) or var(--m-ring).' },
  { id: 'shadow', where: 'markup', re: /(?<=[\s"'`:])shadow-(?:sm|md|lg|xl|2xl|inner|\[[^\]]+\])(?=[\s"'`])/, msg: 'a stock Tailwind shadow. Use shadow-float, shadow-sheet or shadow-ring.' },
  { id: 'radius', where: 'style', re: /border-(?:[a-z-]+-)?radius\s*:(?!\s*(?:0\b|inherit\b|var\(--m-radius-))[^;]*\d/, msg: 'a literal radius. Use the var(--m-radius-…) ladder.' },
  { id: 'radius', where: 'markup', re: /(?<=[\s"'`:])rounded(?:-[trblse]{1,2})?-(?:sm|md|lg|xl|2xl|3xl|\[[^\]]+\])(?=[\s"'`])/, msg: 'a stock Tailwind radius. Use rounded-ctl, rounded-card, rounded-sheet, rounded-tile…' },
  { id: 'font', where: 'style', re: /font-family\s*:(?!\s*(?:inherit\b|var\(--m-font-))[^;]+/, msg: 'a literal font-family. Use var(--m-font-ui) or var(--m-font-mono).' },
  { id: 'tw-arbitrary', where: 'markup', re: /(?<=[\s"'`:])(?:bg|text|fill|stroke|from|via|to|ring|decoration|accent|caret)-\[(?:#|rgb|hsl|lch|oklch)[^\]]*\]/, msg: 'a Tailwind arbitrary colour. Use a theme colour: bg-surface, text-fg-2, bg-primary…' },
  { id: 'tw-palette', where: 'markup', re: new RegExp(`(?<=[\\s"'\`:])(?:bg|text|fill|stroke|from|via|to|ring|decoration|placeholder|caret|accent)-(?:${PALETTE})(?:-\\d{2,3})?(?:\\/\\d+)?(?=[\\s"'\`])`), msg: 'a stock Tailwind palette class. Use a theme colour: bg-surface, text-fg-2, bg-primary…' },
];

const findings = [], allowed = [];
function walk(p) {
  const st = statSync(p);
  if (st.isDirectory()) { if (SKIP_DIR.test(p + '/')) return; for (const f of readdirSync(p)) walk(join(p, f)); return; }
  const ext = extname(p); const isStyle = STYLE.has(ext), isMarkup = MARKUP.has(ext);
  if (!isStyle && !isMarkup) return; if (SKIP_DIR.test(p)) return;
  const lines = readFileSync(p, 'utf8').split('\n');
  lines.forEach((line, i) => {
    const allow = line.match(/ds-allow:\s*(\S.*?)\s*(\*\/|-->|\}|$)/);
    const hits = [];
    for (const r of RULES) {
      if (r.where === 'style' && !(isStyle || /style|css`|styled\./.test(line) || ext === '.html' || ext === '.vue' || ext === '.svelte' || ext === '.astro')) continue;
      if (r.where === 'markup' && !isMarkup) continue;
      const m = line.match(r.re); if (!m) continue; if (r.skip && r.skip.test(line)) continue;
      hits.push({ rule: r.id, msg: r.msg, match: m[0].trim().slice(0, 60) });
    }
    if (!hits.length) return;
    if (allow) { allowed.push({ file: relative(process.cwd(), p), line: i + 1, reason: allow[1] }); return; }
    for (const h of hits) findings.push({ file: relative(process.cwd(), p), line: i + 1, ...h });
  });
}
for (const r of roots) walk(r);

if (asJson) { console.log(JSON.stringify({ ok: findings.length === 0, findings, allowed }, null, 2)); process.exit(findings.length ? 1 : 0); }
for (const f of findings) console.log(`${f.file}:${f.line}  [${f.rule}]  ${f.match}\n    ${f.msg}`);
if (allowed.length) { console.log(`\n${allowed.length} allowed exception(s):`); for (const a of allowed) console.log(`  ${a.file}:${a.line}  ${a.reason}`); }
console.log(findings.length ? `\nMemory DS check failed: ${findings.length} violation(s).` : `\nMemory DS check passed.`);
process.exit(findings.length ? 1 : 0);
