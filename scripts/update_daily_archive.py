#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sys
import textwrap
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from arxiv_utils import fetch_feed, parse_feed_entries, arxiv_abs_url


def parse_args():
    parser = argparse.ArgumentParser(description="Generate daily paper archive from arXiv")
    parser.add_argument("--config", default="config/topics.json")
    parser.add_argument("--output-dir", default="daily")
    parser.add_argument("--date", help="Target date in YYYY-MM-DD, default: today in config timezone")
    return parser.parse_args()


def load_config(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_target_date(date_str: Optional[str], tz_name: str) -> dt.date:
    tz = ZoneInfo(tz_name)
    if date_str:
        return dt.date.fromisoformat(date_str)
    return dt.datetime.now(tz).date()


def local_date(iso_str: str, tz_name: str) -> dt.date:
    ts = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return ts.astimezone(ZoneInfo(tz_name)).date()


def collect_papers(config, target_date: dt.date):
    tz_name = config["timezone"]
    merged = {}
    for topic in config["topics"]:
        raw_feed = fetch_feed(
            search_query=topic["query"],
            max_results=config.get("max_results_per_topic", 50),
            sort_by="submittedDate",
            sort_order="descending",
        )
        for paper in parse_feed_entries(raw_feed):
            published_date = local_date(str(paper["published"]), tz_name)
            if published_date != target_date:
                continue
            paper_key = str(paper.get("arxiv_id") or paper.get("id") or "")
            if not paper_key:
                continue
            if paper_key not in merged:
                paper["topic_labels"] = []
                paper["topic_names"] = []
                merged[paper_key] = paper
            merged[paper_key]["topic_labels"].append(topic["label"])
            merged[paper_key]["topic_names"].append(topic["name"])
    papers = list(merged.values())
    papers.sort(key=lambda item: (str(item["published"]), str(item["title"])), reverse=True)
    return papers


def render_markdown(config, target_date: dt.date, papers):
    topic_labels = "、".join(topic["label"] for topic in config["topics"])
    lines = [
        f"# Daily Papers — {target_date.isoformat()}",
        "",
        f"研究方向：{topic_labels}",
        f"共收录：{len(papers)} 篇",
        "",
        "## 检索说明",
        "",
        "- 数据源：arXiv API",
        "- 筛选规则：按关键词检索后，仅保留目标日期新增论文",
        "- 发表状态补充：每日会重新检查历史 arXiv 元数据中的 DOI / journal_ref",
        "- 注意：这是关键词召回结果，仍建议人工快速过一遍标题与摘要",
        "",
    ]

    if not papers:
        lines.extend([
            "## 今日结果",
            "",
            "今天没有匹配到新增论文。",
            "",
        ])
        return "\n".join(lines)

    lines.extend(["## 今日论文", ""])
    for idx, paper in enumerate(papers, start=1):
        abstract = textwrap.shorten(str(paper["summary"]), width=420, placeholder="...")
        arxiv_id = str(paper.get("arxiv_id", "") or paper.get("id", ""))
        lines.extend([
            f"### {idx}. {paper['title']}",
            f"- arXiv: {arxiv_id}",
            f"- Link: {arxiv_abs_url(arxiv_id)}",
            f"- PDF: {paper['pdf_link'] or 'N/A'}",
            f"- Authors: {', '.join(paper['authors'])}",
            f"- Published: {paper['published']}",
            f"- Publication Status: {paper['publication_status']}",
            f"- Publication: {paper['journal_ref'] or 'N/A'}",
            f"- DOI: {paper['doi'] or 'N/A'}",
            f"- Topics: {', '.join(sorted(set(paper['topic_labels'])))}",
            f"- Categories: {', '.join(sorted(set(paper['categories'])))}",
            f"- Abstract: {abstract}",
            "",
        ])
    return "\n".join(lines)


def main():
    args = parse_args()
    config_path = Path(args.config)
    repo_root = config_path.resolve().parent.parent
    config = load_config(config_path)
    target_date = resolve_target_date(args.date, config["timezone"])
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = collect_papers(config, target_date)
    content = render_markdown(config, target_date, papers)
    out_path = output_dir / f"{target_date.isoformat()}.md"
    out_path.write_text(content + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Paper count: {len(papers)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
