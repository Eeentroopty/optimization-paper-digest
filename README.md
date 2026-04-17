# Optimization Paper Digest

一个面向以下研究方向的每日/每周论文整理与归档仓库：

- 分布式优化
- 历史信息复用的优化
- 异步分布式优化
- 大规模优化算法

## 目录结构

```text
config/                 主题与检索词配置
scripts/                自动抓取、刷新与生成脚本
daily/                  每日归档
weekly/                 每周归档
docs/                   GitHub Pages 静态网页源
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

### 3. 刷新历史论文发表状态

```bash
python3 scripts/refresh_publication_status.py
```

这一步会重新检查所有历史 daily 归档中的 arXiv 条目：

- 如果 arXiv 后来补充了 `journal_ref`
- 或者补充了 `DOI`

那么对应论文页面会自动更新：

- `Publication Status`
- `Publication`
- `DOI`

### 4. 生成本周汇总

```bash
python3 scripts/update_weekly_summary.py
```

### 5. 构建 GitHub Pages 页面

```bash
python3 scripts/build_pages_content.py
```

### 6. 一键执行并推送

```bash
bash scripts/daily_run.sh
```

> `daily_run.sh` 会：
> 1. 抓取 arXiv 新论文
> 2. 生成 `daily/YYYY-MM-DD.md`
> 3. 刷新历史归档的发表状态
> 4. 更新 `weekly/YYYY-Www.md`
> 5. 构建 `docs/` 下的 GitHub Pages 页面
> 6. 若检测到变更，则自动 `git add / commit / push`

## Daily 页面中的发表信息

每篇论文现在会带上如下字段：

- `Publication Status`: `Published` / `Preprint only`
- `Publication`: 期刊或会议引用信息（若 arXiv 已提供）
- `DOI`: DOI（若 arXiv 已提供）

## 说明与当前限制

- 当前版本默认使用 arXiv API 做关键词检索，适合先跑通流程。
- 发表状态刷新 **v1 只依赖 arXiv 当前暴露的元数据**。
  - 也就是说，只有当作者在 arXiv 页面补充了 `journal_ref` 或 `DOI`，这里才会自动显示。
  - 如果论文实际上已经发表，但 arXiv 元数据还没更新，当前版本不会自动识别。
- 对“历史信息复用的优化”这类方向，关键词命中会有噪声，建议运行几天后再微调 `config/topics.json`。

## 后续可扩展方向

- 接入 Crossref，做更强的 DOI / venue 补全
- 接入 OpenReview / Semantic Scholar
- 增加标签页、搜索、作者/主题筛选
- 在 weekly 中加入趋势、重点论文、精读建议
