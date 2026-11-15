#!/usr/bin/env bash
# One command: process new photos, commit, and push to GitHub.
#   tools/publish.sh                 (uses a default commit message)
#   tools/publish.sh "Add Iceland series"
set -euo pipefail
cd "$(dirname "$0")/.."
echo "→ Building optimised images…"
python3 tools/build.py
git add -A
if git diff --cached --quiet; then
  echo "Nothing new to publish."
  exit 0
fi
git commit -m "${1:-Update portfolio}"
echo "→ Pushing to GitHub…"
git push
echo "Done. GitHub Pages refreshes in a minute or two."
