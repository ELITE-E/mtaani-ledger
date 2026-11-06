#!/usr/bin/env bash
# Re-render all diagrams: ./render.sh  (needs @mermaid-js/mermaid-cli)
cd "$(dirname "$0")"
for f in src/*.mmd; do
  n=$(basename "$f" .mmd)
  mmdc -i "$f" -o "$n.png" -b white -s 2 ${PUPPETEER_CFG:+-p "$PUPPETEER_CFG"}
done
# 01 is hand-laid HTML (Mermaid cannot lay it out legibly): needs playwright
python3 - <<'PY'
from playwright.sync_api import sync_playwright
import os
d=os.getcwd()
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]);pg=b.new_page(device_scale_factor=2,viewport={'width':1290,'height':800})
    pg.goto('file://'+d+'/src/01-chart-of-accounts.html');pg.screenshot(path=d+'/01-chart-of-accounts.png',full_page=True);b.close()
PY
