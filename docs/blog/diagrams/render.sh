#!/bin/bash
# Render each figN-*.html to a 2x PNG. Usage: ./render.sh [file.html ...]
set -euo pipefail
CHROME="$HOME/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell"
cd "$(dirname "$0")"
files=("$@"); [ ${#files[@]} -eq 0 ] && files=(fig*.html)
for f in "${files[@]}"; do
  h=$(grep -o 'body{height:[0-9]*px' "$f" | grep -o '[0-9]*')
  "$CHROME" --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --virtual-time-budget=8000 \
    --window-size=1200,"$h" --screenshot="$PWD/${f%.html}.png" "file://$PWD/$f" >/dev/null 2>&1
  echo "${f%.html}.png"
done
