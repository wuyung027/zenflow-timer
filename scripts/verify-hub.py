#!/usr/bin/env python3
import os, re, sys, json, html, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://zenflow-timer.vercel.app"
TOOLS = ["pomodoro","password-generator","word-counter","text-diff","dev-units",
         "markdown-converter","json-formatter","og-preview","cron-builder","svg-optimizer"]
GUIDES = ["pomodoro-focus-science","developer-workflow-privacy","ambient-sound-productivity"]
PAGES = {"/":"index.html", "/tools":"tools/index.html", "/guides":"guides/index.html",
         "/about":"about.html", "/privacy":"privacy.html", "/terms":"terms.html", "/contact":"contact.html"}
for t in TOOLS: PAGES[f"/tools/{t}"] = f"tools/{t}.html"
for g in GUIDES: PAGES[f"/guides/{g}"] = f"guides/{g}.html"
MIN = {"/":700, "/tools":200, "/guides":200, "/about":400, "/privacy":600, "/terms":600, "/contact":250}
# Word count is only an "is the page empty?" guard, not a quality target.
# Padding pages to hit a number is what produced the repeated workflow text;
# the duplicate-sentence check below guards against that instead.
for t in TOOLS: MIN[f"/tools/{t}"] = 30
for g in GUIDES: MIN[f"/guides/{g}"] = 600
BANNED = ["advertisement area","advertisement ·","reserved space","this copy",
          "has not been configured","placeholders only","lorem ipsum","wooyoung",
          "click the ads","support us by clicking"]
fails = []
main_by_page = {}
def txt(s):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s); return html.unescape(s)
def wc(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]+", txt(s)))
for path, rel in PAGES.items():
    fp = os.path.join(ROOT, rel)
    if not os.path.exists(fp):
        fails.append(f"MISSING {rel}"); continue
    s = open(fp, encoding="utf-8").read()
    low = txt(s).lower()
    if len(re.findall(r"<h1[^>]*>", s)) != 1: fails.append(f"{rel}: h1 count != 1")
    if len(re.findall(r"pagead/js/adsbygoogle\.js\?client=ca-pub-3686574001707459", s)) != 1: fails.append(f"{rel}: adsense script count != 1")
    if s.count('<meta name="google-adsense-account" content="ca-pub-3686574001707459">') != 1: fails.append(f"{rel}: adsense account meta count != 1")
    if f'<link rel="canonical" href="{BASE}{path}">' not in s: fails.append(f"{rel}: canonical mismatch for {path}")
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    if not t or len(t.group(1)) > 70: fails.append(f"{rel}: title missing/too long")
    d = re.search(r'<meta name="description" content="([^"]+)"', s)
    if not d or not (50 <= len(d.group(1)) <= 170): fails.append(f"{rel}: meta description length")
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not blocks: fails.append(f"{rel}: no JSON-LD")
    for b in blocks:
        try: json.loads(b)
        except Exception: fails.append(f"{rel}: JSON-LD parse error")
    main = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)
    body = main.group(1) if main else s
    body = re.sub(r'<aside class="zf-related".*?</aside>', " ", body, flags=re.S)
    main_by_page[rel] = body
    n = wc(body)
    if n < MIN[path]: fails.append(f"{rel}: only {n} words (min {MIN[path]})")
    for b in BANNED:
        if b in low: fails.append(f"{rel}: banned text '{b}'")
    for href in re.findall(r'href="(/[^"#?]*)"', s):
        clean = href.split("#")[0]
        key = clean.rstrip("/") or "/"
        if key in PAGES: continue
        target = os.path.join(ROOT, clean.lstrip("/"))
        if os.path.isfile(target): continue                       # css/js/png 등 실재 자산
        if os.path.isfile(target + ".html"): continue
        if os.path.isdir(target) and os.path.exists(os.path.join(target, "index.html")): continue
        fails.append(f"{rel}: broken internal link {href}")
# The same sentence (8+ words) must not appear in the main content of two pages.
# Directory cards (tool/guide listings) are navigation, like the related aside, so skip them.
owners = {}
for rel, body in main_by_page.items():
    body = re.sub(r'<(article|a) class="zf-card".*?</\1>', " ", body, flags=re.S)
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    text = re.sub(r"</(p|h[1-6]|li|summary|td|th|dt|dd|figcaption)>", "\n", text, flags=re.I)
    text = re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", " ", text), flags=re.I)
    for raw in re.split(r"\n|(?<=[.!?])\s+", text):
        sentence = re.sub(r"\s+", " ", raw).strip()
        if len(sentence.split(" ")) < 8: continue
        owners.setdefault(sentence, set()).add(rel)
for sentence, pages_with in owners.items():
    if len(pages_with) > 1:
        fails.append(f"duplicate sentence on {', '.join(sorted(pages_with))}: \"{sentence[:90]}\"")
# The 404 screen has no publisher content, so it must not load AdSense.
nf = open(os.path.join(ROOT, "404.html"), encoding="utf-8").read()
if re.search(r"adsbygoogle|google-adsense-account", nf): fails.append("404.html: AdSense code present")
if not re.search(r'<meta name="google-site-verification" content="[^"]+">', open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()):
    fails.append("index.html: google-site-verification meta missing")
sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
sm_urls = set(re.findall(r"<loc>https://zenflow-timer\.vercel\.app(/[^<]*)</loc>", sm))
if sm_urls != set(PAGES): fails.append(f"sitemap mismatch: missing {set(PAGES)-sm_urls}, extra {sm_urls-set(PAGES)}")
robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
if "Sitemap: https://zenflow-timer.vercel.app/sitemap.xml" not in robots: fails.append("robots.txt sitemap line")
ads = open(os.path.join(ROOT, "ads.txt"), encoding="utf-8").read().strip()
if ads != "google.com, pub-3686574001707459, DIRECT, f08c47fec0942fa0": fails.append("ads.txt line")
print("\n".join(fails) if fails else "ALL CHECKS PASSED")
sys.exit(1 if fails else 0)
