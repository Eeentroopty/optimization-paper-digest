#!/usr/bin/env python3
import argparse
import datetime as dt
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo


def parse_args():
    parser = argparse.ArgumentParser(description="Generate weekly summary index from daily markdown files")
    parser.add_argument("--daily-dir", default="daily")
    parser.add_argument("--weekly-dir", default="weekly")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--date", help="Anchor date in YYYY-MM-DD, default: today")
    return parser.parse_args()


def resolve_date(date_str: Optional[str], tz_name: str) -> dt.date:
    if date_str:
        return dt.date.fromisoformat(date_str)
    return dt.datetime.now(ZoneInfo(tz_name)).date()


def extract_count(text: str) -> int:
    for line in text.splitlines():
        if line.startswith("共收录：") and "篇" in line:
            raw = line.removeprefix("共收录：").split("篇", 1)[0].strip()
            try:
                return int(raw)
            except ValueError:
                return 0
    return 0


def main():
    args = parse_args()
    anchor = resolve_date(args.date, args.timezone)
    iso_year, iso_week, _ = anchor.isocalendar()
    week_id = f"{iso_year}-W{iso_week:02d}"

    repo_root = Path(args.daily_dir).resolve().parent
    daily_dir = repo_root / Path(args.daily_dir).name
    weekly_dir = repo_root / Path(args.weekly_dir).name
    weekly_dir.mkdir(parents=True, exist_ok=True)

    daily_files = []
    total = 0
    for file in sorted(daily_dir.glob("*.md")):
        try:
            file_date = dt.date.fromisoformat(file.stem)
        except ValueError:
            continue
        y, w, _ = file_date.isocalendar()
        if (y, w) != (iso_year, iso_week):
            continue
        text = file.read_text(encoding="utf-8")
        count = extract_count(text)
        total += count
        daily_files.append((file_date, count, file.name))

    lines = [
        f"# Weekly Summary — {week_id}",
        "",
        f"本周累计收录：{total} 篇",
        f"覆盖天数：{len(daily_files)} 天",
        "",
        "## Daily Index",
        "",
    ]

    if not daily_files:
        lines.extend(["本周还没有 daily 归档。", ""])
    else:
        for file_date, count, filename in daily_files:
            lines.append(f"- [{file_date.isoformat()}](../daily/{filename}) — {count} 篇")
        lines.append("")

    lines.extend([
        "## Notes",
        "",
        "- 当前 weekly 文件默认做索引汇总，不自动生成研究摘要。",
        "- 如果后续你希望加入‘每周趋势/重点论文/值得精读’模块，可以再接入更强的总结逻辑。",
        "",
    ])

    out_path = weekly_dir / f"{week_id}.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
