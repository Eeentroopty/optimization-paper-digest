#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from arxiv_utils import fetch_entries_by_ids, normalize_arxiv_id, publication_status

PAPER_HEADING_PREFIX = "### "
ARXIV_PREFIX = "- arXiv: "
PUBLISHED_PREFIX = "- Published:"
PUB_STATUS_PREFIX = "- Publication Status:"
PUBLICATION_PREFIX = "- Publication:"
DOI_PREFIX = "- DOI:"
MANAGED_PREFIXES = (PUB_STATUS_PREFIX, PUBLICATION_PREFIX, DOI_PREFIX)


def parse_args():
    parser = argparse.ArgumentParser(description="Refresh archived paper publication status from current arXiv metadata")
    parser.add_argument("--daily-dir", default="daily", help="Directory containing archived daily markdown files")
    parser.add_argument("--batch-size", type=int, default=20, help="arXiv id_list batch size")
    return parser.parse_args()


def split_blocks(lines: List[str]) -> List[Tuple[int, int]]:
    starts = [idx for idx, line in enumerate(lines) if line.startswith(PAPER_HEADING_PREFIX)]
    blocks: List[Tuple[int, int]] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        blocks.append((start, end))
    return blocks


def extract_arxiv_id(block_lines: Iterable[str]) -> str:
    for line in block_lines:
        if line.startswith(ARXIV_PREFIX):
            return normalize_arxiv_id(line[len(ARXIV_PREFIX):].strip())
    return ""


def build_metadata_lines(metadata: Dict[str, object]) -> List[str]:
    doi = str(metadata.get("doi", "") or "")
    journal_ref = str(metadata.get("journal_ref", "") or "")
    return [
        f"- Publication Status: {publication_status(doi, journal_ref)}",
        f"- Publication: {journal_ref or 'N/A'}",
        f"- DOI: {doi or 'N/A'}",
    ]


def refresh_block(block_lines: List[str], metadata: Dict[str, object]) -> List[str]:
    published_idx = next((idx for idx, line in enumerate(block_lines) if line.startswith(PUBLISHED_PREFIX)), None)

    cleaned: List[str] = []
    for line in block_lines:
        if line.startswith(MANAGED_PREFIXES):
            continue
        cleaned.append(line)

    metadata_lines = build_metadata_lines(metadata)
    if published_idx is None:
        return cleaned + metadata_lines

    adjusted_published_idx = next(idx for idx, line in enumerate(cleaned) if line.startswith(PUBLISHED_PREFIX))
    return cleaned[:adjusted_published_idx + 1] + metadata_lines + cleaned[adjusted_published_idx + 1:]


def refresh_file(path: Path, metadata_map: Dict[str, Dict[str, object]]) -> Tuple[bool, int]:
    original_text = path.read_text(encoding="utf-8")
    lines = original_text.splitlines()
    blocks = split_blocks(lines)
    if not blocks:
        return False, 0

    refreshed = 0
    output: List[str] = []
    cursor = 0
    for start, end in blocks:
        output.extend(lines[cursor:start])
        block_lines = lines[start:end]
        arxiv_id = extract_arxiv_id(block_lines)
        metadata = metadata_map.get(arxiv_id)
        if arxiv_id and metadata:
            refreshed += 1
            output.extend(refresh_block(block_lines, metadata))
        else:
            output.extend(block_lines)
        cursor = end
    output.extend(lines[cursor:])

    new_text = "\n".join(output)
    if original_text.endswith("\n"):
        new_text += "\n"
    changed = new_text != original_text
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed, refreshed


def main():
    args = parse_args()
    repo_root = Path(args.daily_dir).resolve().parent
    daily_dir = repo_root / Path(args.daily_dir).name
    files = sorted(path for path in daily_dir.glob("*.md") if path.name != ".gitkeep")

    ids = []
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        for start, end in split_blocks(lines):
            arxiv_id = extract_arxiv_id(lines[start:end])
            if arxiv_id:
                ids.append(arxiv_id)

    metadata_map = fetch_entries_by_ids(ids, batch_size=args.batch_size) if ids else {}

    changed_files = 0
    refreshed_papers = 0
    for path in files:
        changed, refreshed = refresh_file(path, metadata_map)
        if changed:
            changed_files += 1
        refreshed_papers += refreshed

    print(f"Scanned files: {len(files)}")
    print(f"Papers refreshed: {refreshed_papers}")
    print(f"Files updated: {changed_files}")


if __name__ == "__main__":
    main()
