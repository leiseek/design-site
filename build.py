#!/usr/bin/env python3
"""Build design-site from one JSON file per edition (Dribbble tokens v2).

Usage: python3 build.py
Reads:  content/editions/<date>.json  (one file per edition)
Writes: index.html, archive.html, editions/<date>.html
Daily update: write content/editions/<new-date>.json, run this, commit, push.
Design: Dribbble tokens — pink #ea4c89 only as brand punctuation,
ink #0d0c22, nav #060318 64px, Mona Sans stack, 4-col white grid,
8px image radius, no card backgrounds, no shadows.

i18n: every page renders zh + en strings side by side
(<span class="t-zh">…</span><span class="t-en">…</span>); a tiny inline
script in <head> picks the language from localStorage ('dp-lang') or
navigator.language (zh* -> zh, else en) before first paint, and
assets/i18n.js keeps a manual 中文/EN toggle in sync. Work data carries
comment (zh) + comment_en; categories map to canonical keys so the
filter pills work in both languages.
"""
import html
import json
import pathlib
import hashlib

ROOT = pathlib.Path(__file__).resolve().parent

# (canonical key, zh label, en label)
CATS = [
    ("all", "全部", "All"),
    ("saas", "SaaS", "SaaS"),
    ("ai", "AI", "AI"),
    ("ecommerce", "电商", "E-commerce"),
    ("dashboard", "dashboard", "Dashboard"),
    ("mobile", "移动App", "Mobile App"),
]
CAT_KEY = {"全部": "all", "SaaS": "saas", "AI": "ai", "电商": "ecommerce",
           "dashboard": "dashboard", "移动App": "mobile"}
CAT_ZH = {k: z for k, z, _ in CATS}
CAT_EN = {k: e for k, _, e in CATS}


def esc(s):
    return html.escape(str(s), quote=True)


def t2(zh, en):
    """Bilingual inline span pair (escaped). CSS toggles by <html lang>."""
    return f'<span class="t-zh">{esc(zh)}</span><span class="t-en">{esc(en)}</span>'


def t2r(zh, en):
    """Bilingual inline span pair, raw HTML allowed (for <br> etc.)."""
    return f'<span class="t-zh">{zh}</span><span class="t-en">{en}</span>'


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
    keys = [CAT_KEY.get(c, "all") for c in w.get("categories", [])]
    cats = " ".join(keys)
    cat_zh = " · ".join(CAT_ZH.get(k, k) for k in keys)
    cat_en = " · ".join(CAT_EN.get(k, k) for k in keys)
    comment_en = w.get("comment_en") or w.get("comment") or ""
    if w.get("image"):
        img = f'<img src="{esc(w["image"])}" alt="{esc(w["title"])}" loading="lazy">'
    else:
        img = f'<div class="noimg">{t2r("视频作品，无静态图<br>细节请看原作品页", "Video shot, no still image<br>see the original page for details")}</div>'
    return f"""<article class="work" data-cats="{esc(cats)}">
  <a class="thumb" href="{esc(w['url'])}" target="_blank" rel="noopener">{img}</a>
  <div class="meta2">
    <h3><a href="{esc(w['url'])}" target="_blank" rel="noopener">{esc(w['title'])}</a></h3>
    <div class="author">by {esc(w['author'])}</div>
    <div class="cats">{t2(cat_zh, cat_en)}</div>
    <p class="comment">{t2(w.get('comment') or '', comment_en)}</p>
    <div class="goto"><a href="{esc(w['url'])}" target="_blank" rel="noopener">{t2("看原作品 →", "View original →")}</a></div>
  </div>
</article>"""


def nav(active, depth=0):
    home = "index.html" if depth == 0 else "../index.html"
    archive = "archive.html" if depth == 0 else "../archive.html"
    def cls(name):
        return ' class="active"' if active == name else ""
    return f"""<header class="nav">
  <a class="logo" href="{home}"><span class="dot"></span>{t2("设计拾集", "Design Picks")}</a>
  <nav class="links">
    <a href="{home}"{cls('home')}>{t2("首页", "Home")}</a>
    <a href="{archive}"{cls('archive')}>{t2("归档", "Archive")}</a>
  </nav>
  <span class="spacer"></span>
  <span class="langsw"><button data-lang="zh" class="active">中文</button><i>|</i><button data-lang="en">EN</button></span>
  <a class="btn" href="https://dribbble.com/shots/popular" target="_blank" rel="noopener">{t2("Dribbble 热门", "Popular on Dribbble")}</a>
</header>"""


def toolbar(with_search=True):
    pills = "".join(
        f'<button class="pill{" active" if key == "all" else ""}" data-filter="{key}">{t2(zh, en)}</button>'
        for key, zh, en in CATS
    )
    search = '<input class="search" id="q" type="search" data-ph="search">' if with_search else ""
    return f"""<div class="toolbar">
  <div class="pills">{pills}</div>
  {search}
  <span class="count" id="result-count"></span>
</div>
<div class="empty" id="empty">{t2("没有符合筛选的作品，换个分类或关键词试试。", "Nothing matches — try another category or keyword.")}</div>"""


LANG_DETECT = """<script>(function(){try{var s=localStorage.getItem('dp-lang');var l=s||(((navigator.language||navigator.userLanguage||'en')+'').toLowerCase().indexOf('zh')===0?'zh':'en');document.documentElement.lang=(l==='en'?'en':'zh-CN');}catch(e){}})();</script>"""


def page(title_zh, title_en, desc_zh, desc_en, body, depth=0, active="home", scripts=True):
    prefix = "../" if depth == 1 else ""
    # versioned URLs so cached HTML can never load a stale CSS/JS after deploy
    css = prefix + asset_ver("assets/style.css")
    js_app = prefix + asset_ver("assets/app.js")
    js_i18n = prefix + asset_ver("assets/i18n.js")
    script = f'\n<script src="{js_i18n}"></script>\n<script src="{js_app}"></script>' if scripts else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{LANG_DETECT}
<title>{esc(title_zh)} — 设计拾集</title>
<meta name="dp-title-zh" content="{esc(title_zh)} — 设计拾集">
<meta name="dp-title-en" content="{esc(title_en)} — Design Picks">
<meta name="description" content="{esc(desc_zh)}">
<meta name="dp-desc-zh" content="{esc(desc_zh)}">
<meta name="dp-desc-en" content="{esc(desc_en)}">
<link rel="stylesheet" href="{css}">
</head>
<body>
{nav(active, depth)}
<div class="wrap">
{body}
  <footer>
    <p>{t2r("设计拾集 · 每天从 Dribbble 精选。图片与作品归原作者所有，本站只做收录与点评，点击卡片前往原作品页。",
            "Design Picks · daily selections from Dribbble. Images belong to their creators; this site only curates with notes — click a card to visit the original.")}</p>
    <p><a href="https://dribbble.com/shots/popular">Dribbble</a></p>
  </footer>
</div>{script}
</body>
</html>
"""


DESC_ZH = "每天从 Dribbble 挑 5–10 个值得看的设计，附一句为什么值得借鉴。图片与原作归原作者所有，点击看原作品。"
DESC_EN = "5–10 designs from Dribbble worth your time, every day — each with one line on why it's worth studying. Images belong to their creators; click through to the original."


def meta_line(n_ed, n_works, d1, d2):
    zh = f"{n_ed} 期 · {n_works} 个作品 · {d1} — {d2}"
    en = f"{n_ed} editions · {n_works} works · {d1} — {d2}"
    return t2(zh, en)


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
  <span class="badge">{t2("今日精选", "Today's picks")}</span>
  <h1>{t2("每天值得看的设计", "Design worth looking at, daily")}</h1>
  <p>{t2(DESC_ZH, DESC_EN)}</p>
  <p class="meta">{meta_line(len(editions), total_works, first_date, last_date)}</p>
</section>
{toolbar()}
<section class="section" data-edition="{esc(latest['date'])}">
  <div class="section-head"><h2>{t2(f"最新一期 · {latest['date']}", f"Latest · {latest['date']}")}</h2><span class="sub">{t2(f"{len(latest['works'])} 个作品", f"{len(latest['works'])} works")}</span></div>
  {grid(latest['works'])}
</section>
<section class="section">
  <div class="section-head"><h2>{t2("往期不用点详情", "Browse past editions inline")}</h2><span class="sub"><a href="archive.html">{t2("去归档页直接看全部作品 →", "Browse the full archive →")}</a></span></div>
  <p style="color:var(--smoke)">{t2("归档页按日期展开每一期的全部作品，带分类筛选和搜索，不用一期一期点开。", "The archive expands every edition's works directly — filter by category or search, no need to open editions one by one.")}</p>
</section>"""
    (ROOT / "index.html").write_text(
        page(f"最新一期 · {latest['date']}", f"Latest · {latest['date']}", DESC_ZH, DESC_EN,
             index_body, depth=0, active="home"), encoding="utf-8")

    # ---- archive: every edition expanded inline, no click needed ----
    jump = "".join(f'<a href="#{esc(e["date"])}">{esc(e["date"])}</a>' for e in editions)
    sections = ""
    for e in editions:
        sections += f"""<section class="section" id="{esc(e["date"])}" data-edition="{esc(e['date'])}">
  <div class="section-head"><h2>{esc(e['date'])}</h2><span class="sub">{t2(f"{len(e['works'])} 个作品 · ", f"{len(e['works'])} works · ")}<a href="editions/{esc(e['date'])}.html">{t2("当期页 →", "Edition page →")}</a></span></div>
  {grid(e['works'])}
</section>
"""
    arch_body = f"""<section class="hero">
  <span class="badge">{t2("全部归档", "Full archive")}</span>
  <h1>{t2("按日期展开，全部作品", "Every edition, expanded by date")}</h1>
  <p>{t2("每一期都在下面直接展开，不用点详情。筛分类、搜关键词可以跨期过滤。", "Each edition is expanded inline below. Filter by category or search across editions.")}</p>
  <p class="meta">{meta_line(len(editions), total_works, first_date, last_date)}</p>
</section>
{toolbar()}
<div class="jump">{jump}</div>
{sections}"""
    (ROOT / "archive.html").write_text(
        page("全部归档", "Full archive", DESC_ZH, DESC_EN, arch_body, depth=0, active="archive"),
        encoding="utf-8")

    # ---- edition pages: sticky nav + breadcrumb + home actions ----
    outdir = ROOT / "editions"
    outdir.mkdir(exist_ok=True)
    for idx, e in enumerate(editions):
        prev_link = ""
        next_link = ""
        if idx + 1 < len(editions):
            d = editions[idx + 1]["date"]
            prev_link = f'<a class="btn-ghost" href="{esc(d)}.html">{t2(f"← 上一期 {d}", f"← Previous {d}")}</a>'
        if idx > 0:
            d = editions[idx - 1]["date"]
            next_link = f'<a class="btn-ghost" href="{esc(d)}.html">{t2(f"下一期 {d} →", f"Next {d} →")}</a>'
        body = f"""<p class="breadcrumb"><a href="../index.html">{t2("首页", "Home")}</a> / <a href="../archive.html">{t2("归档", "Archive")}</a> / {esc(e['date'])}</p>
<section class="hero">
  <span class="badge">{esc(e['date'])}</span>
  <h1>{t2(f"{e['date']} 的精选", f"{e['date']} picks")}</h1>
  <p>{t2(f"本期 {len(e['works'])} 个作品。", f"{len(e['works'])} works in this edition.")}</p>
</section>
<div class="actions">
  <a class="btn-dark" href="../index.html">{t2("← 回首页", "← Home")}</a>
  <a class="btn-ghost" href="../archive.html">{t2("全部归档", "Full archive")}</a>
</div>
{toolbar()}
<section class="section" data-edition="{esc(e['date'])}">
  {grid(e['works'])}
</section>
<div class="pager"><span>{prev_link}</span><span>{next_link}</span></div>"""
        (outdir / f"{e['date']}.html").write_text(
            page(e["date"], e["date"], DESC_ZH, DESC_EN, body, depth=1, active=""),
            encoding="utf-8")
    print(f"built: {len(editions)} editions, {total_works} works, latest {last_date}")


if __name__ == "__main__":
    main()
