# Optimization Paper Digest

一个面向以下研究方向的每日/每周论文整理与归档仓库：

- 分布式优化
- 历史信息复用的优化
- 异步分布式优化
- 大规模优化算法

## 目录结构

```text
config/                 主题与检索词配置
scripts/                自动抓取与生成脚本
daily/                  每日归档
weekly/                 每周归档
```

## 展示方式

### GitHub 仓库

可直接在仓库网页中查看 Markdown 归档。

### GitHub Pages（推荐给课题组同学浏览）

仓库推到 GitHub 后，可在仓库设置中开启 GitHub Pages：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`

开启后，网站地址通常为：

```text
https://<github-username>.github.io/optimization-paper-digest/
```

`scripts/build_pages_content.py` 会自动把 `daily/` 与 `weekly/` 同步成 `docs/` 下的 Pages 页面。

## 使用方式

### 1. 调整主题配置
编辑 `config/topics.json`，按你的研究兴趣修改关键词。

### 2. 生成当日归档

```bash
python3 scripts/update_daily_archive.py
```

### 3. 生成本周汇总

```bash
python3 scripts/update_weekly_summary.py
```

### 4. 一键执行并推送

```bash
bash scripts/daily_run.sh
```

> `daily_run.sh` 会：
> 1. 抓取 arXiv 论文
> 2. 生成 `daily/YYYY-MM-DD.md`
> 3. 更新 `weekly/YYYY-Www.md`
> 4. 构建 `docs/` 下的 GitHub Pages 页面
> 5. 若检测到变更，则自动 `git add / commit / push`

## 说明

- 当前版本默认使用 arXiv API 做关键词检索，适合先跑通流程。
- 对“历史信息复用的优化”这类方向，关键词命中会有噪声，建议运行几天后再微调 `config/topics.json`。
- 后续可以继续扩展：
  - 增加更强的摘要/筛选逻辑
  - 接入 OpenReview / Semantic Scholar / Crossref
  - 增加标签页、搜索、作者/主题筛选
