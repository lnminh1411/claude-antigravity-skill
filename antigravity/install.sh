#!/usr/bin/env bash
# Install the antigravity skill for Claude Code (macOS, Linux, Git Bash on Windows).
#
#   ./install.sh                  for you, in every project
#   ./install.sh --project DIR    for one repository only
#
# Respects CLAUDE_CONFIG_DIR. An existing copy is moved aside, never deleted.
set -euo pipefail

src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
files=(SKILL.md agy_watch.py README.md LICENSE)

case "${1:-}" in
  --project)
    [ -n "${2:-}" ] || { echo "usage: $0 --project DIR" >&2; exit 2; }
    [ -d "$2" ] || { echo "no such directory: $2" >&2; exit 2; }
    dest="$(cd "$2" && pwd)/.claude/skills/antigravity" ;;
  "")
    dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/antigravity" ;;
  -h|--help)
    sed -n '2,7p' "$0"; exit 0 ;;
  *)
    echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
esac

for f in "${files[@]}"; do
  [ -f "$src/$f" ] || { echo "missing $f next to install.sh - extract the whole zip first" >&2; exit 1; }
done

if [ "$(cd "$(dirname "$dest")" 2>/dev/null && pwd)/antigravity" = "$src" ]; then
  echo "already in place: $dest"
else
  if [ -e "$dest" ]; then
    # outside skills/: a copy left there would load as a second skill with the same name
    backups="$(dirname "$(dirname "$dest")")/skill-backups"
    mkdir -p "$backups"
    old="$backups/antigravity-$(date +%Y%m%d-%H%M%S)"
    mv "$dest" "$old"
    echo "previous copy moved to: $old"
  fi
  mkdir -p "$dest"
  for f in "${files[@]}"; do cp "$src/$f" "$dest/$f"; done
  echo "installed: $dest"
fi

py=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>/dev/null; then
    py="$c"; break
  fi
done
if [ -n "$py" ]; then
  "$py" -I "$dest/agy_watch.py" --help >/dev/null && echo "watcher ok ($py)"
else
  echo "warning: no Python 3.8+ found; the skill needs it to watch dispatches" >&2
fi

cat <<'EOF'

Next:
  1. Run `agy` once and finish the browser sign-in (skip if Antigravity is already signed in).
  2. In Claude Code, type:  /antigravity setup
EOF
