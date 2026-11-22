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
for t in TOOLS: MIN[f"/tools/{t}"] = 1200
for g in GUIDES: MIN[f"/guides/{g}"] = 1000
BANNED = ["advertisement area","advertisement ·","reserved space","this copy",
          "has not been configured","placeholders only","lorem ipsum","wooyoung",
          "click the ads","support us by clicking"]
fails = []
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
    if s.count("ca-pub-3686574001707459") != 1: fails.append(f"{rel}: adsense script count != 1")
    if f'<link rel="canonical" href="{BASE}{path}">' not in s: fails.append(f"{rel}: canonical mismatch for {path}")
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    if not t or len(t.group(1)) > 70: fails.append(f"{rel}: title missing/too long")
    d = re.search(r'<meta name="description" content="([^"]+)"', s)
    if not d or not (120 <= len(d.group(1)) <= 170): fails.append(f"{rel}: meta description length")
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not blocks: fails.append(f"{rel}: no JSON-LD")
    for b in blocks:
        try: json.loads(b)
        except Exception: fails.append(f"{rel}: JSON-LD parse error")
    main = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)
    body = main.group(1) if main else s
    body = re.sub(r'<aside class="zf-related".*?</aside>', " ", body, flags=re.S)
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
sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
sm_urls = set(re.findall(r"<loc>https://zenflow-timer\.vercel\.app(/[^<]*)</loc>", sm))
if sm_urls != set(PAGES): fails.append(f"sitemap mismatch: missing {set(PAGES)-sm_urls}, extra {sm_urls-set(PAGES)}")
robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
if "Sitemap: https://zenflow-timer.vercel.app/sitemap.xml" not in robots: fails.append("robots.txt sitemap line")
ads = open(os.path.join(ROOT, "ads.txt"), encoding="utf-8").read().strip()
if ads != "google.com, pub-3686574001707459, DIRECT, f08c47fec0942fa0": fails.append("ads.txt line")
print("\n".join(fails) if fails else "ALL CHECKS PASSED")
sys.exit(1 if fails else 0)

추가 육안/도구 확인:
- `python3 -m http.server 8000` 으로 띄워 `/`, `/tools/pomodoro` 등 20개 URL이 열리는지 확인
  (clean URL은 로컬 서버에서 `tools/pomodoro.html`로 확인, Vercel에서 확장자 없이 서빙됨).
- 각 툴 페이지에서 콘솔 에러 0 (특히 법적 모달 제거 후 남은 JS 참조 정리), 390px 폭 레이아웃,
  타이머 시작/정지, 비밀번호 재생성, diff 비교, JSON prettify, cron 다음 실행 5회, SVG 미리보기가 실제로 동작하는지.

====================================================================
[10] 하지 말 것
====================================================================
- 법적 페이지를 모달/해시로 되돌리기, 10개 툴을 한 HTML에 탭으로 몰아넣기
- 소스 HTML을 레포에 남겨 `/pomodoro.html` 같은 중복 얇은 페이지 만들기
- 광고 슬롯·자리표시 박스·가짜 광고 미리보기 넣기
- 가짜 후기/평점/사용자 수/언론 언급 만들기
- 이메일·전화·주소·회사명 창작, "미설정" 상태 문구 남기기
- 기존 10개 사이트(다른 vercel.app 도메인)를 건드리거나 링크로 엮기 (이번 작업 범위 밖)
- `git push`, Vercel 대시보드 조작, 애드센스 계정 조작 (사람이 한다)
- 유료 SaaS(2·7·8·9·10호기) 링크 삽입 — 무료 도구 사이트의 정체성을 흐린다

====================================================================
[11] 완료 보고 형식
====================================================================
작업이 끝나면 아래를 그대로 출력해라.
1) 생성/수정한 파일 목록(경로)
2) `python3 scripts/verify-hub.py` 최종 출력 (PASSED 여부)
3) 페이지별 단어 수 표 (경로 / 단어 수 / h2 개수 / FAQ 문항 수)
4) 이식한 툴별 "동작 확인" 결과 (타이머·비밀번호·diff·JSON·cron·SVG 등 무엇을 눌러 확인했는지)
5) 배포 전 사람이 채워야 할 자리표시자 위치 (`[YOUR_EMAIL]` 위치 목록)
6) 남은 위험·미확인 사항 (예: 소스 fetch 실패로 재구현한 툴, 브라우저 미검증 항목)
