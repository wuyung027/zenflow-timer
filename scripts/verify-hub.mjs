import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '..');
const BASE = 'https://zenflow-timer.vercel.app';
const tools = ['pomodoro','password-generator','word-counter','text-diff','dev-units','markdown-converter','json-formatter','og-preview','cron-builder','svg-optimizer'];
const guides = ['pomodoro-focus-science','developer-workflow-privacy','ambient-sound-productivity'];
const pages = {'/':'index.html','/tools':'tools/index.html','/guides':'guides/index.html','/about':'about.html','/privacy':'privacy.html','/terms':'terms.html','/contact':'contact.html'};
for (const s of tools) pages[`/tools/${s}`] = `tools/${s}.html`;
for (const s of guides) pages[`/guides/${s}`] = `guides/${s}.html`;
const min = {'/':700,'/tools':200,'/guides':200,'/about':400,'/privacy':600,'/terms':600,'/contact':250};
for (const s of tools) min[`/tools/${s}`] = 1200;
for (const s of guides) min[`/guides/${s}`] = 1000;
const banned = ['advertisement area','advertisement ·','reserved space','this copy','has not been configured','placeholders only','lorem ipsum','wooyoung','click the ads','support us by clicking','[your_email]'];
const failures = [];
const plain = s => s.replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&[a-z#0-9]+;/gi,' ');
const words = s => (plain(s).match(/[A-Za-z][A-Za-z'-]+/g) || []).length;

for (const [url, rel] of Object.entries(pages)) {
  const fp = path.join(ROOT, rel);
  if (!fs.existsSync(fp)) { failures.push(`MISSING ${rel}`); continue; }
  const source = fs.readFileSync(fp, 'utf8');
  const low = plain(source).toLowerCase();
  if ((source.match(/<h1[^>]*>/g) || []).length !== 1) failures.push(`${rel}: h1 count`);
  if ((source.match(/pagead\/js\/adsbygoogle\.js\?client=ca-pub-3686574001707459/g) || []).length !== 1) failures.push(`${rel}: adsense script count`);
  if ((source.match(/<meta name="google-adsense-account" content="ca-pub-3686574001707459">/g) || []).length !== 1) failures.push(`${rel}: adsense account meta count`);
  if (!source.includes(`<link rel="canonical" href="${BASE}${url}">`)) failures.push(`${rel}: canonical`);
  const title = source.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? '';
  if (!title || title.length > 70) failures.push(`${rel}: title`);
  const description = source.match(/<meta name="description" content="([^"]+)"/)?.[1] ?? '';
  if (description.length < 120 || description.length > 170) failures.push(`${rel}: description ${description.length}`);
  for (const match of source.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)) {
    try { JSON.parse(match[1]); } catch { failures.push(`${rel}: JSON-LD`); }
  }
  let main = source.match(/<main[^>]*>([\s\S]*?)<\/main>/)?.[1] ?? source;
  main = main.replace(/<aside class="zf-related"[\s\S]*?<\/aside>/g, ' ');
  const count = words(main);
  if (count < min[url]) failures.push(`${rel}: only ${count} words (min ${min[url]})`);
  for (const term of banned) if (low.includes(term)) failures.push(`${rel}: banned ${term}`);
}

const sitemap = fs.readFileSync(path.join(ROOT,'sitemap.xml'),'utf8');
const sitemapUrls = new Set([...sitemap.matchAll(/<loc>https:\/\/zenflow-timer\.vercel\.app([^<]*)<\/loc>/g)].map(m => m[1]));
if (sitemapUrls.size !== Object.keys(pages).length || Object.keys(pages).some(p => !sitemapUrls.has(p))) failures.push('sitemap mismatch');
if (fs.readFileSync(path.join(ROOT,'ads.txt'),'utf8').trim() !== 'google.com, pub-3686574001707459, DIRECT, f08c47fec0942fa0') failures.push('ads.txt');

console.log(failures.length ? failures.join('\n') : 'ALL CHECKS PASSED');
process.exit(failures.length ? 1 : 0);
