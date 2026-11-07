#!/usr/bin/env bash
# Checks that everything the workflow needs is installed. Run: bash tools/setup-check.sh
ok=0; miss=0
check() { if command -v "$1" >/dev/null 2>&1; then echo "  ✓ $1"; ok=$((ok+1)); else echo "  ✕ $1  ->  $2"; miss=$((miss+1)); fi; }
# board-sync/setup.sh installs everything into this venv; the system python3 is only the fallback.
PY=python3; [ -x skills/board-sync/.venv/bin/python ] && PY=skills/board-sync/.venv/bin/python
echo "Tools"
check python3 "install Python 3.10+ from python.org"
check ffmpeg  "macOS: brew install ffmpeg · Windows: winget install ffmpeg"
check ffprobe "comes with ffmpeg"
check node    "optional, only for editing kit.js: nodejs.org"
# Any coding-agent harness runs the workflow: OMP (Joey's) or Claude Code (upstream default).
if command -v omp >/dev/null 2>&1; then echo "  ✓ omp (agent harness)"; ok=$((ok+1))
elif command -v claude >/dev/null 2>&1; then echo "  ✓ claude (agent harness)"; ok=$((ok+1))
else echo "  ✕ agent harness  ->  install OMP or Claude Code (https://claude.com/claude-code)"; miss=$((miss+1)); fi
echo "Python packages ($PY)"
for p in faster_whisper playwright numpy PIL; do
  if "$PY" -c "import $p" 2>/dev/null; then echo "  ✓ $p"; ok=$((ok+1)); else echo "  ✕ $p  ->  bash skills/board-sync/setup.sh"; miss=$((miss+1)); fi
done
# Whisper must decode real audio: faster-whisper 1.2.x breaks on PyAV 19 even though the import works.
wav="${TMPDIR:-/tmp}/setup-check-$$.wav"
if ffmpeg -v error -y -f lavfi -i anullsrc=r=16000:cl=mono -t 1 "$wav" 2>/dev/null \
  && "$PY" -c "import sys; from faster_whisper.audio import decode_audio; decode_audio(sys.argv[1])" "$wav" 2>/dev/null; then
  echo "  ✓ Whisper audio decode"; ok=$((ok+1))
else echo "  ✕ Whisper audio decode  ->  bash skills/board-sync/setup.sh (needs av<19)"; miss=$((miss+1)); fi
rm -f "$wav"
if "$PY" -c "from playwright.sync_api import sync_playwright as s; p=s().start(); b=p.chromium.launch(); b.close(); p.stop()" 2>/dev/null; then
  echo "  ✓ Chromium for Playwright"; ok=$((ok+1))
elif "$PY" -c "from playwright.sync_api import sync_playwright as s; p=s().start(); b=p.chromium.launch(channel='chrome'); b.close(); p.stop()" 2>/dev/null; then
  echo "  ✓ Chrome (use --chrome with tools/export.py)"; ok=$((ok+1))
else echo "  ✕ Chromium for Playwright  ->  $PY -m playwright install chromium"; miss=$((miss+1)); fi
echo "Repo"
[ -f boards/index.html ] && echo "  ✓ boards/ ($(ls boards/*.html | wc -l | tr -d ' ') files)" || { echo "  ✕ run this from the repo folder"; miss=$((miss+1)); }
[ -f tools/export.py ] && echo "  ✓ tools/export.py" || { echo "  ✕ tools/export.py missing"; miss=$((miss+1)); }
[ -f checks.md ] && echo "  ✓ checks.md" || { echo "  ✕ checks.md missing"; miss=$((miss+1)); }
echo
if [ $miss -eq 0 ]; then echo "All set. Open boards/index.html to see every board."; else echo "$miss missing. Install them, then run this again."; exit 1; fi
