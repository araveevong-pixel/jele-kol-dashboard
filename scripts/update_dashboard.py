#!/usr/bin/env python3
"""
update_dashboard.py — Inject scrape_results.json into KOL_DATA in index.html
==============================================================================
Uses KOL_METADATA fallback for any KOL not in scrape results.
Preserves CAMPAIGN_ACTUAL_USE_DEFAULT value.

Usage:
  python3 update_dashboard.py <scrape_results.json> <index.html>
  python3 update_dashboard.py ../scrape_results.json ../index.html
"""

import json
import re
import sys
import os
from datetime import datetime

# ── Full KOL Metadata (48 KOLs) ─────────────────────────────
# Fallback data: username → {tier, category, followers, batch, kpi_views, link, posted}
KOL_METADATA = {
    # Main
    "biw_songkran":   {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 1900000, "batch": "Main",    "kpi_views": 10000000, "link": "https://vt.tiktok.com/ZSm7UqSxm/", "posted": True},
    "fasin22052545":  {"tier": "Macro", "category": "ภาคใต้",   "followers": 297900,  "batch": "Main",    "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcaAb2h/", "posted": True},
    "ovapachannel":   {"tier": "Macro", "category": "ภาคเหนือ", "followers": 397200,  "batch": "Main",    "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcm17pD/", "posted": True},
    "jack.ittiphon":  {"tier": "Mega",  "category": "ภาคกลาง", "followers": 1900000, "batch": "Main",    "kpi_views": 0, "link": "", "posted": False},
    "nophuwanet":     {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 1700000, "batch": "Main",    "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdU6PSb/", "posted": True},
    # Batch 1
    "plugsweden":     {"tier": "Macro", "category": "ภาคกลาง", "followers": 198800,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSukQWcn8/", "posted": True},
    "pakkaput17":     {"tier": "Macro", "category": "ภาคกลาง", "followers": 369700,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcaGQy3/", "posted": True},
    "kuanpuantiew":   {"tier": "Mega",  "category": "ภาคกลาง", "followers": 1100000, "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcato1w/", "posted": True},
    "pexjakkajee":    {"tier": "Mega",  "category": "ภาคกลาง", "followers": 1400000, "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSm7yUL5N/", "posted": True},
    "puwanaipison":   {"tier": "Macro", "category": "ภาคกลาง", "followers": 335900,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcaTqdj/", "posted": True},
    "gotarm65":       {"tier": "Macro", "category": "ภาคเหนือ", "followers": 563000,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSm7MXU59/", "posted": True},
    "tikbadai":       {"tier": "Macro", "category": "ภาคเหนือ", "followers": 680800,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcW2HWK/", "posted": True},
    "patpaladmuang":  {"tier": "Macro", "category": "ภาคเหนือ", "followers": 243700,  "batch": "Batch 1", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSmcaqqea/", "posted": True},
    # Batch 2
    "saokrungthep":   {"tier": "Macro", "category": "ภาคกลาง", "followers": 235200,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuYdxpWe/", "posted": True},
    "ll0499":         {"tier": "Macro", "category": "ภาคกลาง", "followers": 248000,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuY6uqJd/", "posted": True},
    "pooliepraew":    {"tier": "Mega",  "category": "ภาคกลาง", "followers": 1200000, "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuFppTeB/", "posted": True},
    "f_u_i_":         {"tier": "Macro", "category": "ภาคกลาง", "followers": 212200,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuYMC3Qs/", "posted": True},
    "coochamp":       {"tier": "Macro", "category": "ภาคเหนือ", "followers": 639100,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuY8vRRb/", "posted": True},
    "aodbom2":        {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 1700000, "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuYMrAnR/", "posted": True},
    "wootza5555":     {"tier": "Macro", "category": "ภาคอีสาน", "followers": 985100,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuYhbTuQ/", "posted": True},
    "royver_th":      {"tier": "Macro", "category": "ภาคใต้",   "followers": 793300,  "batch": "Batch 2", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuY89A6a/", "posted": True},
    # Batch 3
    "bookteerapat":   {"tier": "Macro", "category": "ภาคอีสาน", "followers": 694700,  "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSumsVbBW/", "posted": True},
    "bunyaporn_2009": {"tier": "Mega",  "category": "ภาคใต้",   "followers": 5900000, "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSumseLjA/", "posted": True},
    "thebellchanel":  {"tier": "Macro", "category": "ภาคใต้",   "followers": 331400,  "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSumN9avE/", "posted": True},
    "tan_slaz19":     {"tier": "Macro", "category": "ภาคกลาง", "followers": 143800,  "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSumNqjHt/", "posted": True},
    "armgoodsunday":  {"tier": "Macro", "category": "ภาคกลาง", "followers": 801800,  "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuaEAwaB/", "posted": True},
    "biggesttha":     {"tier": "Macro", "category": "ภาคอีสาน", "followers": 220900,  "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuasTfRG/", "posted": True},
    "bosck999":       {"tier": "Macro", "category": "ภาคกลาง", "followers": 1500000, "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSumpv8TU/", "posted": True},
    "juno55555":      {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 2600000, "batch": "Batch 3", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSubjckjm/", "posted": True},
    # Batch 4
    "tkpst2":         {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 5500000, "batch": "Batch 4", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUqfAp/", "posted": True},
    "pupemaipriaw":   {"tier": "Macro", "category": "ภาคอีสาน", "followers": 538700,  "batch": "Batch 4", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUJ4Sh/", "posted": True},
    "jekkabot5555":   {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 1500000, "batch": "Batch 4", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUYT3T/", "posted": True},
    "lenpaither":     {"tier": "Micro", "category": "ภาคอีสาน", "followers": 27400,   "batch": "Batch 4", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUxosg/", "posted": True},
    "apirak2539ice":  {"tier": "Mega",  "category": "ภาคอีสาน", "followers": 5400000, "batch": "Batch 4", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUaKFY/", "posted": True},
    # Batch 5 (Mixology)
    "kayshomebar":    {"tier": "Micro", "category": "Mixology",  "followers": 39100,   "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSuuWoyee/", "posted": True},
    "raa_reun_core":  {"tier": "Macro", "category": "Mixology",  "followers": 424000,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSum5tCCk/", "posted": True},
    "maxk_litt":      {"tier": "Macro", "category": "Mixology",  "followers": 703600,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSugeG1XM/", "posted": True},
    "maoaowfeel":     {"tier": "Micro", "category": "Mixology",  "followers": 12600,   "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdU2F7o/", "posted": True},
    "how.to.mao":     {"tier": "Macro", "category": "Mixology",  "followers": 144700,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdURQkp/", "posted": True},
    "arpo_story":     {"tier": "Macro", "category": "Mixology",  "followers": 149100,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUhKR9/", "posted": True},
    "yod_121098":     {"tier": "Mega",  "category": "Mixology",  "followers": 1200000, "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUMfWS/", "posted": True},
    "tatatomang":     {"tier": "Macro", "category": "Mixology",  "followers": 186900,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUQjKV/", "posted": True},
    "taloncamp_sg":   {"tier": "Macro", "category": "Mixology",  "followers": 257100,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdU4owX/", "posted": True},
    "gowithgoldd":    {"tier": "Macro", "category": "Mixology",  "followers": 254000,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUGT5j/", "posted": True},
    "maww_shabu":     {"tier": "Macro", "category": "Mixology",  "followers": 415500,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdULuXB/", "posted": True},
    "tenitbrk":       {"tier": "Mega",  "category": "Mixology",  "followers": 4100000, "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdU7Xfh/", "posted": True},
    "biibuaaastory":  {"tier": "Micro", "category": "Mixology",  "followers": 58900,   "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUeHRa/", "posted": True},
    "snicker_nts":    {"tier": "Macro", "category": "Mixology",  "followers": 114700,  "batch": "Batch 5", "kpi_views": 0, "link": "https://vt.tiktok.com/ZSHdUnfPB/", "posted": True},
}

# Batch ordering for consistent output
BATCH_ORDER = ["Main", "Batch 1", "Batch 2", "Batch 3", "Batch 4", "Batch 5"]

NOT_POSTED_KOLS = {"jack.ittiphon"}


def kol_to_js(kol):
    """Convert a single KOL dict to JS object string."""
    parts = [
        f"username:'{kol['username']}'",
        f"tier:'{kol['tier']}'",
        f"platform:'TikTok'",
        f"category:'{kol['category']}'",
        f"followers:{kol['followers']}",
        f"views:{kol['views']}",
        f"likes:{kol['likes']}",
        f"shares:{kol['shares']}",
        f"comments:{kol['comments']}",
        f"saves:{kol['saves']}",
        f"posts:{kol['posts']}",
        f"kpi_views:{kol['kpi_views']}",
        f"posted:{'true' if kol['posted'] else 'false'}",
    ]
    if kol.get("link"):
        parts.append(f"link:'{kol['link']}'")
    parts.append(f"batch:'{kol['batch']}'")
    return "  {" + ",".join(parts) + "},"


def build_kol_data_js(kols):
    """Build the full let KOL_DATA = [...]; block."""
    now = datetime.now().strftime("%d %b %Y %H:%M")
    lines = [f"let KOL_DATA = [  // auto-updated {now}"]

    batches = {}
    for k in kols:
        b = k["batch"]
        batches.setdefault(b, []).append(k)

    for batch_name in BATCH_ORDER:
        if batch_name not in batches:
            continue
        lines.append(f"  // === {batch_name} ===")
        for k in batches[batch_name]:
            lines.append(kol_to_js(k))

    lines.append("];")
    return "\n".join(lines)


def read_existing_stats(html):
    """Read existing stats from current index.html as fallback."""
    existing = {}
    for m in re.finditer(
        r"\{username:'([^']+)',tier:'[^']*',platform:'[^']*',category:'[^']*',"
        r"followers:(\d+),views:(\d+),likes:(\d+),shares:(\d+),comments:(\d+),saves:(\d+),"
        r"posts:(\d+),kpi_views:(\d+),posted:(true|false)",
        html
    ):
        g = m.groups()
        existing[g[0]] = {
            "followers": int(g[1]), "views": int(g[2]), "likes": int(g[3]),
            "shares": int(g[4]), "comments": int(g[5]), "saves": int(g[6]),
            "posts": int(g[7]), "kpi_views": int(g[8]),
        }
    return existing


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 update_dashboard.py <scrape_results.json> <index.html>")
        sys.exit(1)

    json_path = sys.argv[1]
    html_path = sys.argv[2]

    # Load scrape results
    with open(json_path, "r", encoding="utf-8") as f:
        scrape_data = json.load(f)
    print(f"📊 Loaded scrape results: {len(scrape_data)} KOLs")

    # Load existing HTML
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Preserve CAMPAIGN_ACTUAL_USE_DEFAULT
    actual_use_match = re.search(r"const CAMPAIGN_ACTUAL_USE_DEFAULT\s*=\s*([\d.]+);", html)
    actual_use_value = actual_use_match.group(1) if actual_use_match else "430000.0"
    print(f"💰 Preserving Actual Use: {actual_use_value}")

    # Read existing stats as fallback
    existing_stats = read_existing_stats(html)

    # Build KOL list
    kols = []
    for username, meta in KOL_METADATA.items():
        scraped = scrape_data.get(username, {})
        existing = existing_stats.get(username, {})

        # Use scraped data if available and has views, else use existing, else 0
        views = scraped.get("views", 0) or existing.get("views", 0)
        likes = scraped.get("likes", 0) or existing.get("likes", 0)
        shares = scraped.get("shares", 0) or existing.get("shares", 0)
        comments = scraped.get("comments", 0) or existing.get("comments", 0)
        saves = scraped.get("saves", 0) or existing.get("saves", 0)
        # ALWAYS use metadata followers (from campaign brief), never scraped
        followers = meta["followers"]

        kol = {
            "username": username,
            "tier": meta["tier"],
            "category": meta["category"],
            "followers": followers,
            "views": views,
            "likes": likes,
            "shares": shares,
            "comments": comments,
            "saves": saves,
            "posts": 1 if meta["posted"] else 0,
            "kpi_views": existing.get("kpi_views", meta["kpi_views"]),
            "posted": meta["posted"],
            "link": meta["link"],
            "batch": meta["batch"],
        }
        kols.append(kol)

    # Build new KOL_DATA block
    new_block = build_kol_data_js(kols)

    # Replace in HTML
    pattern = r'let KOL_DATA = \[.*?\];'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        print("❌ Could not find KOL_DATA block in HTML")
        sys.exit(1)

    updated_html = html[:match.start()] + new_block + html[match.end():]

    # Restore actual use value
    updated_html = re.sub(
        r"const CAMPAIGN_ACTUAL_USE_DEFAULT\s*=\s*[\d.]+;",
        f"const CAMPAIGN_ACTUAL_USE_DEFAULT = {actual_use_value};",
        updated_html
    )

    # Write back
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(updated_html)

    posted = [k for k in kols if k["posted"]]
    total_views = sum(k["views"] for k in posted)
    print(f"✅ Dashboard updated: {len(kols)} KOLs ({len(posted)} posted)")
    print(f"   Total Views: {total_views:,}")


if __name__ == "__main__":
    main()
