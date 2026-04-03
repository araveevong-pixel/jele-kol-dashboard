#!/usr/bin/env python3
"""
update_actual_use.py — Update CAMPAIGN_ACTUAL_USE_DEFAULT in index.html
=======================================================================
Usage:
  python3 update_actual_use.py <amount> [html_path]
  python3 update_actual_use.py 430000 ../index.html
"""

import re
import sys
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 update_actual_use.py <amount> [html_path]")
        sys.exit(1)

    try:
        amount = float(sys.argv[1].replace(",", ""))
    except ValueError:
        print(f"❌ Invalid amount: {sys.argv[1]}")
        sys.exit(1)

    html_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "index.html")
    html_path = os.path.abspath(html_path)

    print(f"💰 Updating Actual Use → {amount:,.0f} ฿")
    print(f"   File: {html_path}")

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    old_pattern = r"const CAMPAIGN_ACTUAL_USE_DEFAULT\s*=\s*[\d.]+;"
    match = re.search(old_pattern, html)
    if not match:
        print("❌ Could not find CAMPAIGN_ACTUAL_USE_DEFAULT in HTML")
        sys.exit(1)

    old_value = re.search(r"[\d.]+", match.group()).group()
    new_line = f"const CAMPAIGN_ACTUAL_USE_DEFAULT = {amount};"
    html = re.sub(
        r"const CAMPAIGN_ACTUAL_USE_DEFAULT\s*=\s*[\d.]+;.*",
        new_line + " // ← auto-updated by update_actual_use.py",
        html
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Updated: {old_value} → {amount:,.0f}")


if __name__ == "__main__":
    main()
