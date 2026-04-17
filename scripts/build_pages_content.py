#!/usr/bin/env python3
import datetime as dt
import json
from pathlib import Path


def md_link(path: Path) -> str:
    return path.as_posix()


def add_front_matter(title: str, body: str) -> str:
    return f"---\nlayout: default\ntitle: {title}\n---\n\n" + body.lstrip()


def load_topics(config_path: Path):
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data.get("topics", [])


def extract_first_nonempty_line(text: str, prefix: str = "- Abstract:") -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


def main():
    repo = Path(__file__).resolve().parent.parent
    daily_dir = repo / "daily"
    weekly_dir = repo / "weekly"
    docs_dir = repo / "docs"
    docs_daily = docs_dir / "daily"
    docs_weekly = docs_dir / "weekly"
    docs_daily.mkdir(parents=True, exist_ok=True)
    docs_weekly.mkdir(parents=True, exist_ok=True)

    topics = load_topics(repo / "config" / "topics.json")

    daily_entries = []
    for path in sorted(daily_dir.glob("*.md"), reverse=True):
        if path.name == ".gitkeep":
            continue
        text = path.read_text(encoding="utf-8")
        abstract = extract_first_nonempty_line(text)
        title = f"Daily Papers — {path.stem}"
        out = docs_daily / path.name
        out.write_text(add_front_matter(title, text), encoding="utf-8")
        daily_entries.append({"date": path.stem, "path": md_link(Path("daily") / path.name), "abstract": abstract})

    weekly_entries = []
    for path in sorted(weekly_dir.glob("*.md"), reverse=True):
        if path.name == ".gitkeep":
            continue
        text = path.read_text(encoding="utf-8")
        title = f"Weekly Summary — {path.stem}"
        out = docs_weekly / path.name
        out.write_text(add_front_matter(title, text), encoding="utf-8")
        weekly_entries.append({"week": path.stem, "path": md_link(Path("weekly") / path.name)})

    topic_lines = [f"- **{t['label']}**  \n  Query: `{t['query']}`" for t in topics]
    if not topic_lines:
        topic_lines = ["- 暂无主题配置"]

    daily_lines = []
    if daily_entries:
        for item in daily_entries[:30]:
            daily_lines.append(f"- [{item['date']}]({item['path']})")
    else:
        daily_lines.append("- 暂无 daily 归档")

    weekly_lines = []
    if weekly_entries:
        for item in weekly_entries[:20]:
            weekly_lines.append(f"- [{item['week']}]({item['path']})")
    else:
        weekly_lines.append("- 暂无 weekly 归档")

    today = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    index_md = f"""---
layout: default
title: Optimization Paper Digest
---

# Optimization Paper Digest

面向以下研究方向的每日/每周论文归档与整理：

{chr(10).join(topic_lines)}

## Daily Updates

{chr(10).join(daily_lines)}

## Weekly Summaries

{chr(10).join(weekly_lines)}

## About

- 数据源：arXiv API
- 更新方式：GitHub Actions 每日自动运行
- 历史论文会每日刷新 arXiv 上已补充的 DOI / journal_ref
- 最近页面生成时间：{today}
- 仓库：GitHub repository + GitHub Pages (/docs source)
"""
    (docs_dir / "index.md").write_text(index_md, encoding="utf-8")

    config_yml = """title: Optimization Paper Digest
description: Daily and weekly paper digest for optimization research.
theme: minima
markdown: kramdown
plugins:
  - jekyll-feed
show_excerpts: false
"""
    (docs_dir / "_config.yml").write_text(config_yml, encoding="utf-8")

    home_readme = "# GitHub Pages Source\n\n该目录会被 GitHub Pages 渲染为静态网页。\n"
    (docs_dir / "README.md").write_text(home_readme, encoding="utf-8")

    print(f"Built docs site in {docs_dir}")


if __name__ == "__main__":
    main()
