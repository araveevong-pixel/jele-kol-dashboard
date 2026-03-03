#!/usr/bin/env python3
"""
update_dashboard.py — อ่าน kol_linkpost_data.json แล้วเขียนลง Dashboard HTML โดยตรง
ไม่ต้อง Import เอง เปิด Dashboard มาเห็นข้อมูลล่าสุดเลย

วิธีใช้:
  python3 update_dashboard.py

จะอ่านไฟล์:
  - kol_linkpost_data.json   (ข้อมูลจาก scraper)
  - kol-overview-dashboard.html (dashboard)

แล้วแทนที่ KOL_DATA ใน dashboard ด้วยข้อมูลจริงจาก JSON
"""

import json
import re
import os
import sys
from datetime import datetime

# === Config ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "kol_linkpost_data.json")
DASHBOARD_FILE = os.path.join(SCRIPT_DIR, "kol-overview-dashboard.html")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def kol_to_js(kol):
    """Convert a single KOL dict to JS object string"""
    parts = []
    parts.append(f"username:'{kol['username']}'")
    parts.append(f"tier:'{kol['tier']}'")
    parts.append(f"platform:'{kol.get('platform','TikTok')}'")
    parts.append(f"category:'{kol.get('category','')}'")
    parts.append(f"followers:{kol.get('followers',0)}")
    parts.append(f"views:{kol.get('views',0)}")
    parts.append(f"likes:{kol.get('likes',0)}")
    parts.append(f"shares:{kol.get('shares',0)}")
    parts.append(f"comments:{kol.get('comments',0)}")
    parts.append(f"saves:{kol.get('saves',0)}")
    parts.append(f"posts:{kol.get('posts',0)}")
    parts.append(f"kpi_views:{kol.get('kpi_views',0)}")
    parts.append(f"posted:{'true' if kol.get('posted') else 'false'}")
    if kol.get('link'):
        parts.append(f"link:'{kol['link']}'")
    parts.append(f"batch:'{kol.get('batch','')}'")
    return "{" + ",".join(parts) + "}"

def build_kol_data_js(kols):
    """Build the full let KOL_DATA = [...]; block"""
    now = datetime.now().strftime("%d %b %Y %H:%M")
    lines = [f"let KOL_DATA = [  // auto-updated {now}"]

    # Group by batch
    batches = {}
    for k in kols:
        b = k.get('batch', 'Other')
        if b not in batches:
            batches[b] = []
        batches[b].append(k)

    first = True
    for batch_name, batch_kols in batches.items():
        lines.append(f"  // === {batch_name} ===")
        for k in batch_kols:
            prefix = "  " if first else "  "
            first = False
            lines.append(f"  {kol_to_js(k)},")

    lines.append("];")
    return "\n".join(lines)

def update_dashboard(html, kols):
    """Replace KOL_DATA block in HTML"""
    new_block = build_kol_data_js(kols)

    # Match: let KOL_DATA = [ ... ];
    pattern = r'let KOL_DATA = \[.*?\];'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        print("❌ ไม่พบ KOL_DATA ใน dashboard HTML")
        return None

    updated = html[:match.start()] + new_block + html[match.end():]
    return updated

def main():
    # Check files exist
    if not os.path.exists(JSON_FILE):
        print(f"❌ ไม่พบไฟล์ {JSON_FILE}")
        print("   รัน tiktok_scraper.py --linkpost ก่อน")
        sys.exit(1)

    if not os.path.exists(DASHBOARD_FILE):
        print(f"❌ ไม่พบไฟล์ {DASHBOARD_FILE}")
        sys.exit(1)

    # Load data
    kols = load_json(JSON_FILE)
    print(f"📊 อ่านข้อมูล {len(kols)} KOLs จาก JSON")

    posted = [k for k in kols if k.get('posted')]
    total_views = sum(k.get('views', 0) for k in posted)
    print(f"   ✅ Posted: {len(posted)} | Total Views: {total_views:,}")

    # Read dashboard
    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    # Update
    updated = update_dashboard(html, kols)
    if updated is None:
        sys.exit(1)

    # Write back
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"✅ อัปเดต Dashboard เรียบร้อย!")
    print(f"   เปิด kol-overview-dashboard.html ใน browser ได้เลย")

if __name__ == "__main__":
    main()
