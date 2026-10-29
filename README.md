# 设计拾集（design.znio.io）

每天从 Dribbble 挑 5–10 个值得看的设计，附一句为什么值得借鉴，收录成站。

- 首页：最新一期 + 全部归档
- 每期一页：`editions/YYYY-MM-DD.html`
- 数据：`content/editions/YYYY-MM-DD.json`，每期一个文件（约 2 KB），不设一个越长越大的总文件；每期含日期、作品标题、作者、原作品链接、图片直链、中文点评、方向标签
- 生成：`python3 build.py`，输出 `index.html`、`archive.html`、`editions/*.html`（归档页每期只列首作，不随作品数膨胀）
- 发布：GitHub Pages，从 `main` 分支根目录发布，自定义域名 `design.znio.io`（见 `CNAME`）

图片与作品归原作者所有，本站只做收录与点评，点击卡片前往 Dribbble 原作品页。

## 每日更新流程

1. 从 Dribbble 热门页与关键词搜索页挑当日未收录作品 5–10 个，核对发布日期在近 7 天内、质量优先；
2. 去重：对照 `content/editions.json` 已收录的原作品链接，跳过已收录的；
3. 每个作品拿到标题、作者、原作品链接、图片直链（Dribbble CDN），写一句中文点评；
4. 把新一期写成 `content/editions/YYYY-MM-DD.json` 一个新文件（不要改回总文件），跑 `python3 build.py`，检查首页与当期页；
5. 提交并推送到 `main`，等 GitHub Pages 构建完成，核实 `https://design.znio.io/` 与当期页能打开；
6. 向 leo 报告：日期、作品数与标题、发布状态、站点与当期页链接。只报发布情况，不在聊天里重发整期图片与点评。
