#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


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


def fetch_arxiv(query: str, max_results: int):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "research-paper-archive/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_entry(entry):
    title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
    summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
    paper_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
    updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
    authors = [author.findtext("atom:name", default="", namespaces=ATOM_NS) for author in entry.findall("atom:author", ATOM_NS)]
    categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS)]
    links = entry.findall("atom:link", ATOM_NS)
    pdf_link = ""
    for link in links:
        if link.attrib.get("title") == "pdf":
            pdf_link = link.attrib.get("href", "")
            break
    return {
        "id": paper_id,
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "authors": [a for a in authors if a],
        "categories": [c for c in categories if c],
        "pdf_link": pdf_link,
    }


def local_date(iso_str: str, tz_name: str) -> dt.date:
    ts = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return ts.astimezone(ZoneInfo(tz_name)).date()


def collect_papers(config, target_date: dt.date):
    tz_name = config["timezone"]
    merged = {}
    for topic in config["topics"]:
        raw = fetch_arxiv(topic["query"], config.get("max_results_per_topic", 50))
        root = ET.fromstring(raw)
        for entry in root.findall("atom:entry", ATOM_NS):
            paper = parse_entry(entry)
            published_date = local_date(paper["published"], tz_name)
            if published_date != target_date:
                continue
            if paper["id"] not in merged:
                paper["topic_labels"] = []
                paper["topic_names"] = []
                merged[paper["id"]] = paper
            merged[paper["id"]]["topic_labels"].append(topic["label"])
            merged[paper["id"]]["topic_names"].append(topic["name"])
    papers = list(merged.values())
    papers.sort(key=lambda item: (item["published"], item["title"]), reverse=True)
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
        abstract = textwrap.shorten(paper["summary"], width=420, placeholder="...")
        lines.extend([
            f"### {idx}. {paper['title']}",
            f"- arXiv: {paper['id']}",
            f"- Link: {paper['id']}",
            f"- PDF: {paper['pdf_link'] or 'N/A'}",
            f"- Authors: {', '.join(paper['authors'])}",
            f"- Published: {paper['published']}",
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
