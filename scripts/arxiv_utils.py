#!/usr/bin/env python3
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List, Optional

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_ABS_PREFIXES = (
    "http://arxiv.org/abs/",
    "https://arxiv.org/abs/",
    "http://www.arxiv.org/abs/",
    "https://www.arxiv.org/abs/",
    "arXiv:",
)


def normalize_arxiv_id(value: str) -> str:
    text = (value or "").strip()
    for prefix in ARXIV_ABS_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    text = text.split("?", 1)[0].split("#", 1)[0].strip()
    if text.endswith(".pdf"):
        text = text[:-4]
    text = re.sub(r"v\d+$", "", text)
    return text.strip()


def arxiv_abs_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/abs/{normalize_arxiv_id(arxiv_id)}"


def arxiv_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{normalize_arxiv_id(arxiv_id)}.pdf"


def publication_status(doi: str, journal_ref: str) -> str:
    return "Published" if (doi or journal_ref) else "Preprint only"


def fetch_feed(*, search_query: str = "", id_list: Optional[Iterable[str]] = None, max_results: int = 10,
               sort_by: str = "submittedDate", sort_order: str = "descending") -> bytes:
    ids = [normalize_arxiv_id(item) for item in (id_list or []) if normalize_arxiv_id(item)]
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    if ids:
        params["id_list"] = ",".join(ids)
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "optimization-paper-digest/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_entry(entry: ET.Element) -> Dict[str, object]:
    raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    arxiv_id = normalize_arxiv_id(raw_id)
    title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
    summary = " ".join((entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").split())
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
    updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
    journal_ref = " ".join((entry.findtext("arxiv:journal_ref", default="", namespaces=ATOM_NS) or "").split())
    doi = " ".join((entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS) or "").split())

    authors = [
        author.findtext("atom:name", default="", namespaces=ATOM_NS)
        for author in entry.findall("atom:author", ATOM_NS)
    ]
    categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS)]

    pdf_link = ""
    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("title") == "pdf":
            pdf_link = link.attrib.get("href", "")
            break
    if not pdf_link and arxiv_id:
        pdf_link = arxiv_pdf_url(arxiv_id)

    return {
        "id": raw_id,
        "arxiv_id": arxiv_id,
        "title": title,
        "summary": summary,
        "published": published,
        "updated": updated,
        "authors": [a for a in authors if a],
        "categories": [c for c in categories if c],
        "pdf_link": pdf_link,
        "doi": doi,
        "journal_ref": journal_ref,
        "publication_status": publication_status(doi, journal_ref),
    }


def parse_feed_entries(raw_feed: bytes) -> List[Dict[str, object]]:
    root = ET.fromstring(raw_feed)
    return [parse_entry(entry) for entry in root.findall("atom:entry", ATOM_NS)]


def fetch_entries_by_ids(arxiv_ids: Iterable[str], batch_size: int = 20) -> Dict[str, Dict[str, object]]:
    normalized = [normalize_arxiv_id(item) for item in arxiv_ids if normalize_arxiv_id(item)]
    result: Dict[str, Dict[str, object]] = {}
    for offset in range(0, len(normalized), batch_size):
        batch = normalized[offset: offset + batch_size]
        if not batch:
            continue
        raw_feed = fetch_feed(id_list=batch, max_results=len(batch), sort_by="lastUpdatedDate")
        for paper in parse_feed_entries(raw_feed):
            paper_id = str(paper.get("arxiv_id", ""))
            if paper_id:
                result[paper_id] = paper
    return result
