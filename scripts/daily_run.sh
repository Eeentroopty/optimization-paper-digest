#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

TARGET_DATE="${1:-$(TZ=Asia/Shanghai date +%F)}"

python3 scripts/update_daily_archive.py --date "$TARGET_DATE"
python3 scripts/update_weekly_summary.py --date "$TARGET_DATE"
python3 scripts/build_pages_content.py

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository yet: $REPO_DIR"
  exit 0
fi

git add daily weekly docs README.md config/topics.json scripts .github

if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git commit -m "chore: update paper archive for $TARGET_DATE"
git push

echo "Pushed updates for $TARGET_DATE"
