#!/usr/bin/env python3
"""Build design-site from one JSON file per edition (Dribbble tokens v2).

Usage: python3 build.py
Reads:  content/editions/<date>.json  (one file per edition)
Writes: index.html, archive.html, editions/<date>.html
Daily update: write content/editions/<new-date>.json, run this, commit, push.
Design: Dribbble tokens — pink #ea4c89 only as brand punctuation,
ink #0d0c22, nav #060318 64px, Mona Sans stack, 4-col white grid,
8px image radius, no card backgrounds, no shadows.
"""
import html
import json
import pathlib
import hashlib

ROOT = pathlib.Path(__file__).resolve().parent
SITE_NAME = "设计拾集"
SITE_EN = "Design Picks — Daily selections from Dribbble"
BASE_DESC = "每天从 Dribbble 挑 5–10 个值得看的设计，附一句为什么值得借鉴。图片与原作归原作者所有，点击看原作品。"

CATS = ["全部", "SaaS", "AI", "电商", "dashboard", "移动App"]


def esc(s):
    return html.escape(str(s), quote=True)


def asset_ver(rel):
    """Append a content-hash query (?v=xxxx) to a static asset path.

    CSS/JS changed twice in one evening behind a caching CDN proxy on
    2026-10-28, and a visitor saw broken styles minutes after a deploy —
    most likely old HTML mixed with new CSS from cache. A content hash
    makes every asset change a new URL, so clients can never mix
    versions. Rebuilds without asset changes keep the same URL.
    """
    p = ROOT / rel
    try:
        h = hashlib.md5(p.read_bytes()).hexdigest()[:8]
    except OSError:
        return rel
    return f"{rel}?v={h}"


def load_editions():
    by_date = {}
    legacy = ROOT / "content" / "editions.json"
    if legacy.is_file():
        try:
            for e in json.loads(legacy.read_text(encoding="utf-8")):
                by_date[e["date"]] = e
        except Exception:
            pass
    for p in sorted((ROOT / "content" / "editions").glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        by_date[e["date"]] = e
    return sorted(by_date.values(), key=lambda e: e["date"], reverse=True)


def work_card(w, i):
    cats = " ".join(w.get("categories", []))
    cat_text = " · ".join(w.get("categories", []))
    if w.get("image"):
        img = f'<img src="{esc(w["image"])}" alt="{esc(w["title"])}" loading="lazy">'
    else:
        img = '<div class="noimg">视频作品，无静态图<br>细节请看原作品页</div>'
    return f"""<article class="work" data-cats="{esc(cats)}">
  <a class="thumb" href="{esc(w['url'])}" target="_blank" rel="noopener">{img}</a>
  <div class="meta2">
    <h3><a href="{esc(w['url'])}" target="_blank" rel="noopener">{esc(w['title'])}</a></h3>
    <div class="author">by {esc(w['author'])}</div>
    <div class="cats">{esc(cat_text)}</div>
    <p class="comment">{esc(w.get('comment') or '')}</p>
    <div class="goto"><a href="{esc(w['url'])}" target="_blank" rel="noopener">看原作品 →</a></div>
  </div>
</article>"""


def nav(active, depth=0):
    home = "index.html" if depth == 0 else "../index.html"
    archive = "archive.html" if depth == 0 else "../archive.html"
    def cls(name):
        return ' class="active"' if active == name else ""
    return f"""<header class="nav">
  <a class="logo" href="{home}"><span class="dot"></span>{SITE_NAME}</a>
  <nav class="links">
    <a href="{home}"{cls('home')}>首页</a>
    <a href="{archive}"{cls('archive')}>归档</a>
  </nav>
  <span class="spacer"></span>
  <a class="btn" href="https://dribbble.com/shots/popular" target="_blank" rel="noopener">Dribbble 热门</a>
</header>"""


def toolbar(with_search=True):
    pills = "".join(
        f'<button class="pill{" active" if c == "全部" else ""}" data-filter="{esc(c)}">{esc(c)}</button>'
        for c in CATS
    )
    search = '<input class="search" id="q" type="search" placeholder="搜标题、作者、点评…">' if with_search else ""
    return f"""<div class="toolbar">
  <div class="pills">{pills}</div>
  {search}
  <span class="count" id="result-count"></span>
</div>
<div class="empty" id="empty">没有符合筛选的作品，换个分类或关键词试试。</div>"""


def page(title, body, depth=0, active="home", scripts=True):
    prefix = "../" if depth == 1 else ""
    # versioned URLs so cached HTML can never load a stale CSS/JS after deploy
    css = prefix + asset_ver("assets/style.css")
    js = prefix + asset_ver("assets/app.js")
    script = f'\n<script src="{js}"></script>' if scripts else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {SITE_NAME}</title>
<meta name="description" content="{esc(BASE_DESC)}">
<link rel="stylesheet" href="{css}">
</head>
<body>
{nav(active, depth)}
<div class="wrap">
{body}
  <footer>
    <p>{SITE_NAME} · 每天从 Dribbble 精选。图片与作品归原作者所有，本站只做收录与点评，点击卡片前往原作品页。</p>
    <p><a href="https://dribbble.com/shots/popular">Dribbble 热门</a></p>
  </footer>
</div>{script}
</body>
</html>
"""


def grid(works):
    return '<div class="grid">\n' + "\n".join(work_card(w, i + 1) for i, w in enumerate(works)) + "\n</div>"


def main():
    editions = load_editions()
    total_works = sum(len(e["works"]) for e in editions)
    first_date = editions[-1]["date"] if editions else ""
    last_date = editions[0]["date"] if editions else ""

    # ---- index: latest edition full grid + jump to archive ----
    latest = editions[0]
    index_body = f"""<section class="hero">
  <span class="badge">今日精选</span>
  <h1>每天值得看的设计</h1>
  <p>{BASE_DESC}</p>
  <p class="meta">{len(editions)} 期 · {total_works} 个作品 · {esc(first_date)} — {esc(last_date)}</p>
</section>
{toolbar()}
<section class="section" data-edition="{esc(latest['date'])}">
  <div class="section-head"><h2>最新一期 · {esc(latest['date'])}</h2><span class="sub">{len(latest['works'])} 个作品</span></div>
  {grid(latest['works'])}
</section>
<section class="section">
  <div class="section-head"><h2>往期不用点详情</h2><span class="sub"><a href="archive.html">去归档页直接看全部作品 →</a></span></div>
  <p style="color:var(--smoke)">归档页按日期展开每一期的全部作品，带分类筛选和搜索，不用一期一期点开。</p>
</section>"""
    (ROOT / "index.html").write_text(page(f"最新一期 · {latest['date']}", index_body, depth=0, active="home"), encoding="utf-8")

    # ---- archive: every edition expanded inline, no click needed ----
    jump = "".join(f'<a href="#{esc(e["date"])}">{esc(e["date"])}</a>' for e in editions)
    sections = ""
    for e in editions:
        sections += f"""<section class="section" id="{esc(e['date'])}" data-edition="{esc(e['date'])}">
  <div class="section-head"><h2>{esc(e['date'])}</h2><span class="sub">{len(e['works'])} 个作品 · <a href="editions/{esc(e['date'])}.html">当期页 →</a></span></div>
  {grid(e['works'])}
</section>
"""
    arch_body = f"""<section class="hero">
  <span class="badge">全部归档</span>
  <h1>按日期展开，全部作品</h1>
  <p>每一期都在下面直接展开，不用点详情。筛分类、搜关键词可以跨期过滤。</p>
  <p class="meta">{len(editions)} 期 · {total_works} 个作品</p>
</section>
{toolbar()}
<div class="jump">{jump}</div>
{sections}"""
    (ROOT / "archive.html").write_text(page("全部归档", arch_body, depth=0, active="archive"), encoding="utf-8")

    # ---- edition pages: sticky nav + breadcrumb + home actions ----
    outdir = ROOT / "editions"
    outdir.mkdir(exist_ok=True)
    for idx, e in enumerate(editions):
        prev_link = ""
        next_link = ""
        if idx + 1 < len(editions):
            prev_ed = editions[idx + 1]
            prev_link = f'<a class="btn-ghost" href="{esc(prev_ed["date"])}.html">← 上一期 {esc(prev_ed["date"])}</a>'
        if idx > 0:
            next_ed = editions[idx - 1]
            next_link = f'<a class="btn-ghost" href="{esc(next_ed["date"])}.html">下一期 {esc(next_ed["date"])} →</a>'
        body = f"""<p class="breadcrumb"><a href="../index.html">首页</a> / <a href="../archive.html">归档</a> / {esc(e['date'])}</p>
<section class="hero">
  <span class="badge">{esc(e['date'])}</span>
  <h1>{esc(e['date'])} 的精选</h1>
  <p>本期 {len(e['works'])} 个作品。</p>
</section>
<div class="actions">
  <a class="btn-dark" href="../index.html">← 回首页</a>
  <a class="btn-ghost" href="../archive.html">全部归档</a>
</div>
{toolbar()}
<section class="section" data-edition="{esc(e['date'])}">
  {grid(e['works'])}
</section>
<div class="pager"><span>{prev_link}</span><span>{next_link}</span></div>"""
        (outdir / f"{e['date']}.html").write_text(page(e["date"], body, depth=1, active=""), encoding="utf-8")
    print(f"built: {len(editions)} editions, {total_works} works, latest {last_date}")


if __name__ == "__main__":
    main()
