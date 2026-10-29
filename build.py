#!/usr/bin/env python3
"""Build design-site from content/editions.json.

Usage: python3 build.py
Reads:  content/editions.json  (list of editions, newest first or not)
Writes: index.html, archive.html, editions/<date>.html
Daily update flow: append a new edition object to content/editions.json,
run this script, commit and push. GitHub Pages rebuilds from main.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
SITE_NAME = "设计拾集"
SITE_EN = "Design Picks — Daily selections from Dribbble"
BASE_DESC = "每天从 Dribbble 挑 5–10 个值得看的设计，附一句为什么值得借鉴。图片与原作归原作者所有，点击卡片看原作品。"


def esc(s):
    return html.escape(str(s), quote=True)


def work_card(w, i, prefix=""):
    num = f"{i:02d}"
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in w.get("categories", []))
    if w.get("image"):
        img = f'<img src="{esc(w["image"])}" alt="{esc(w["title"])}" loading="lazy">'
    else:
        img = '<div class="noimg">视频作品，无静态图<br>细节请看原作品页</div>'
    return f"""<a class="work" href="{esc(w['url'])}" target="_blank" rel="noopener">
  <div class="img">{img}</div>
  <div class="body">
    <div class="num">No. {num}</div>
    <h3>{esc(w['title'])}</h3>
    <div class="author">by {esc(w['author'])}</div>
    <div class="tags">{tags}</div>
    <p class="comment">{esc(w.get('comment') or '')}</p>
    <div class="goto">看原作品 →</div>
  </div>
</a>"""


def page(title, head_extra, body, depth=0):
    css = "assets/style.css" if depth == 0 else "../assets/style.css"
    home = "index.html" if depth == 0 else "../index.html"
    archive = "archive.html" if depth == 0 else "../archive.html"
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
<div class="wrap">
  <div class="topbar"><span>design.znio.io</span><span><a href="{home}">最新一期</a> &nbsp;·&nbsp; <a href="{archive}">全部归档</a></span></div>
{body}
  <footer>
    <p>{SITE_NAME} · 每天从 Dribbble 精选。图片与作品归原作者所有，本站只做收录与点评，点击卡片前往原作品页。</p>
    <p><a href="https://dribbble.com/shots/popular">Dribbble 热门</a> · <a href="{home}">回首页</a></p>
  </footer>
</div>
</body>
</html>
"""


def masthead(total_editions, total_works, first_date, last_date):
    return f"""<header class="masthead">
  <h1>{SITE_NAME}</h1>
  <div class="en">{SITE_EN}</div>
  <p>{BASE_DESC}</p>
  <p class="meta">{total_editions} 期 · {total_works} 个作品 · {esc(first_date)} — {esc(last_date)}</p>
</header>"""


def main():
    editions = json.loads((ROOT / "content" / "editions.json").read_text(encoding="utf-8"))
    editions = sorted(editions, key=lambda e: e["date"], reverse=True)
    total_works = sum(len(e["works"]) for e in editions)
    first_date = editions[-1]["date"] if editions else ""
    last_date = editions[0]["date"] if editions else ""

    # index: latest edition + archive teaser
    latest = editions[0]
    cards = "\n".join(work_card(w, i + 1) for i, w in enumerate(latest["works"]))
    rows = ""
    for e in editions:
        rows += f'<tr><td class="date">{esc(e["date"])}</td><td>{len(e["works"])} 个</td><td><a href="editions/{esc(e["date"])}.html">{esc(e["works"][0]["title"])} 等</a></td></tr>\n'
    index_body = f"""{masthead(len(editions), total_works, first_date, last_date)}
<h2>最新一期 · {esc(latest['date'])}</h2>
<p class="section-note">本期 {len(latest['works'])} 个作品。</p>
<div class="grid">
{cards}
</div>
<hr class="rule">
<h2>归档</h2>
<table class="archive">
<tr><th>日期</th><th>数量</th><th>本期首作</th></tr>
{rows}</table>
<p><a href="archive.html">看全部归档 →</a></p>"""
    (ROOT / "index.html").write_text(page(f"最新一期 · {latest['date']}", "", index_body, depth=0), encoding="utf-8")

    # archive page
    arch_body = f"""{masthead(len(editions), total_works, first_date, last_date)}
<h2>全部归档</h2>
<p class="section-note">按推送日期倒序，每期 5–10 个作品。</p>
<table class="archive">
<tr><th>日期</th><th>数量</th><th>本期作品</th></tr>
{''.join(f'<tr><td class="date">{esc(e["date"])}</td><td>{len(e["works"])} 个</td><td><a href="editions/{esc(e["date"])}.html">' + "、".join(esc(w["title"]) for w in e["works"]) + "</a></td></tr>\n" for e in editions)}</table>"""
    (ROOT / "archive.html").write_text(page("全部归档", "", arch_body, depth=0), encoding="utf-8")

    # edition pages
    outdir = ROOT / "editions"
    outdir.mkdir(exist_ok=True)
    for idx, e in enumerate(editions):
        cards = "\n".join(work_card(w, i + 1) for i, w in enumerate(e["works"]))
        prev_link = ""
        next_link = ""
        if idx + 1 < len(editions):
            prev_ed = editions[idx + 1]
            prev_link = f'<a href="{esc(prev_ed["date"])}.html">← 上一期 {esc(prev_ed["date"])}</a>'
        if idx > 0:
            next_ed = editions[idx - 1]
            next_link = f'<a href="{esc(next_ed["date"])}.html">下一期 {esc(next_ed["date"])} →</a>'
        body = f"""<header class="masthead">
  <h1>{esc(e['date'])}</h1>
  <div class="en">{SITE_EN}</div>
  <p>本期 {len(e['works'])} 个作品。</p>
</header>
<div class="grid">
{cards}
</div>
<div class="pager"><span>{prev_link}</span><span>{next_link}</span></div>"""
        (outdir / f"{e['date']}.html").write_text(page(e["date"], "", body, depth=1), encoding="utf-8")
    print(f"built: {len(editions)} editions, {total_works} works, latest {last_date}")


if __name__ == "__main__":
    main()
