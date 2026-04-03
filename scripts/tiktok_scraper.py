#!/usr/bin/env python3
"""
TikTok KOL Scraper — JELE SODA 2026 (GitHub Actions Edition)
=============================================================
ใช้แค่ Python stdlib (urllib, json, re, ssl) — ไม่ต้องติดตั้งอะไรเพิ่ม
ดึง views, likes, shares, comments จาก TikTok video page

Usage:
  python3 tiktok_scraper.py [output_path]
  python3 tiktok_scraper.py ../scrape_results.json
"""

import json
import re
import sys
import ssl
import time
import urllib.request
from datetime import datetime

# ── KOL Links (47 posted KOLs) ──────────────────────────────
KOL_LINKS = {
    # Main
    "biw_songkran":    "https://vt.tiktok.com/ZSm7UqSxm/",
    "fasin22052545":   "https://vt.tiktok.com/ZSmcaAb2h/",
    "ovapachannel":    "https://vt.tiktok.com/ZSmcm17pD/",
    "nophuwanet":      "https://vt.tiktok.com/ZSHdU6PSb/",
    # Batch 1
    "plugsweden":      "https://vt.tiktok.com/ZSukQWcn8/",
    "pakkaput17":      "https://vt.tiktok.com/ZSmcaGQy3/",
    "kuanpuantiew":    "https://vt.tiktok.com/ZSmcato1w/",
    "pexjakkajee":     "https://vt.tiktok.com/ZSm7yUL5N/",
    "puwanaipison":    "https://vt.tiktok.com/ZSmcaTqdj/",
    "gotarm65":        "https://vt.tiktok.com/ZSm7MXU59/",
    "tikbadai":        "https://vt.tiktok.com/ZSmcW2HWK/",
    "patpaladmuang":   "https://vt.tiktok.com/ZSmcaqqea/",
    # Batch 2
    "saokrungthep":    "https://vt.tiktok.com/ZSuYdxpWe/",
    "ll0499":          "https://vt.tiktok.com/ZSuY6uqJd/",
    "pooliepraew":     "https://vt.tiktok.com/ZSuFppTeB/",
    "f_u_i_":          "https://vt.tiktok.com/ZSuYMC3Qs/",
    "coochamp":        "https://vt.tiktok.com/ZSuY8vRRb/",
    "aodbom2":         "https://vt.tiktok.com/ZSuYMrAnR/",
    "wootza5555":      "https://vt.tiktok.com/ZSuYhbTuQ/",
    "royver_th":       "https://vt.tiktok.com/ZSuY89A6a/",
    # Batch 3
    "bookteerapat":    "https://vt.tiktok.com/ZSumsVbBW/",
    "bunyaporn_2009":  "https://vt.tiktok.com/ZSumseLjA/",
    "thebellchanel":   "https://vt.tiktok.com/ZSumN9avE/",
    "tan_slaz19":      "https://vt.tiktok.com/ZSumNqjHt/",
    "armgoodsunday":   "https://vt.tiktok.com/ZSuaEAwaB/",
    "biggesttha":      "https://vt.tiktok.com/ZSuasTfRG/",
    "bosck999":        "https://vt.tiktok.com/ZSumpv8TU/",
    "juno55555":       "https://vt.tiktok.com/ZSubjckjm/",
    # Batch 4
    "tkpst2":          "https://vt.tiktok.com/ZSHdUqfAp/",
    "pupemaipriaw":    "https://vt.tiktok.com/ZSHdUJ4Sh/",
    "jekkabot5555":    "https://vt.tiktok.com/ZSHdUYT3T/",
    "lenpaither":      "https://vt.tiktok.com/ZSHdUxosg/",
    "apirak2539ice":   "https://vt.tiktok.com/ZSHdUaKFY/",
    # Batch 5 (Mixology)
    "kayshomebar":     "https://vt.tiktok.com/ZSuuWoyee/",
    "raa_reun_core":   "https://vt.tiktok.com/ZSum5tCCk/",
    "maxk_litt":       "https://vt.tiktok.com/ZSugeG1XM/",
    "maoaowfeel":      "https://vt.tiktok.com/ZSHdU2F7o/",
    "how.to.mao":      "https://vt.tiktok.com/ZSHdURQkp/",
    "arpo_story":      "https://vt.tiktok.com/ZSHdUhKR9/",
    "yod_121098":      "https://vt.tiktok.com/ZSHdUMfWS/",
    "tatatomang":      "https://vt.tiktok.com/ZSHdUQjKV/",
    "taloncamp_sg":    "https://vt.tiktok.com/ZSHdU4owX/",
    "gowithgoldd":     "https://vt.tiktok.com/ZSHdUGT5j/",
    "maww_shabu":      "https://vt.tiktok.com/ZSHdULuXB/",
    "tenitbrk":        "https://vt.tiktok.com/ZSHdU7Xfh/",
    "biibuaaastory":   "https://vt.tiktok.com/ZSHdUeHRa/",
    "snicker_nts":     "https://vt.tiktok.com/ZSHdUnfPB/",
}

# ── SSL context (skip verification for CI) ───────────────────
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
    "Accept-Encoding": "identity",
}


def resolve_short_url(short_url, max_redirects=5):
    """Follow redirects from vt.tiktok.com to get the real video URL."""
    url = short_url
    for _ in range(max_redirects):
        try:
            req = urllib.request.Request(url, headers=HEADERS, method='HEAD')
            resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
            return resp.url
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                url = e.headers.get('Location', url)
                continue
            return url
        except Exception:
            # Try GET if HEAD fails
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
                # Check if there's a redirect in meta tag or JS
                body = resp.read(50000).decode('utf-8', errors='ignore')
                meta = re.search(r'<meta[^>]*http-equiv="refresh"[^>]*url=(["\'])([^"\']+)\1', body, re.I)
                if meta:
                    url = meta.group(2)
                    continue
                # Check for canonical URL
                canon = re.search(r'"canonicalUrl"\s*:\s*"(https://www\.tiktok\.com/@[^"]+)"', body)
                if canon:
                    return canon.group(1)
                return resp.url
            except Exception:
                return url
    return url


def fetch_page(url, retries=3):
    """Fetch a URL and return the HTML body."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=20)
            return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
            else:
                print(f"      ❌ fetch failed: {e}")
                return None


def extract_stats_from_html(html):
    """Try multiple methods to extract video stats from TikTok page HTML."""
    stats = {"views": 0, "likes": 0, "shares": 0, "comments": 0, "saves": 0, "followers": 0}

    # Method 1: __UNIVERSAL_DATA_FOR_REHYDRATION__ (most reliable)
    m = re.search(r'<script\s+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            # Navigate: __DEFAULT_SCOPE__ → webapp.video-detail → itemInfo → itemStruct → stats
            scope = data.get("__DEFAULT_SCOPE__", {})
            detail = scope.get("webapp.video-detail", {})
            item = detail.get("itemInfo", {}).get("itemStruct", {})
            s = item.get("stats", {})
            if s:
                stats["views"] = int(s.get("playCount", 0))
                stats["likes"] = int(s.get("diggCount", 0))
                stats["shares"] = int(s.get("shareCount", 0))
                stats["comments"] = int(s.get("commentCount", 0))
                stats["saves"] = int(s.get("collectCount", 0))
            author = item.get("author", {})
            author_stats = detail.get("itemInfo", {}).get("itemStruct", {}).get("authorStats", {})
            if author_stats:
                stats["followers"] = int(author_stats.get("followerCount", 0))
            if any(v > 0 for v in stats.values()):
                return stats
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    # Method 2: SIGI_STATE (older TikTok pages)
    m = re.search(r'<script\s+id="SIGI_STATE"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            items = data.get("ItemModule", {})
            for vid_id, item in items.items():
                s = item.get("stats", {})
                if s:
                    stats["views"] = int(s.get("playCount", 0))
                    stats["likes"] = int(s.get("diggCount", 0))
                    stats["shares"] = int(s.get("shareCount", 0))
                    stats["comments"] = int(s.get("commentCount", 0))
                    stats["saves"] = int(s.get("collectCount", 0))
                author_stats = item.get("authorStats", {})
                if author_stats:
                    stats["followers"] = int(author_stats.get("followerCount", 0))
                if any(v > 0 for v in stats.values()):
                    return stats
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    # Method 3: JSON-LD
    for m in re.finditer(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            if isinstance(data, list):
                data = data[0] if data else {}
            ic = data.get("interactionStatistic", [])
            if isinstance(ic, list):
                for stat in ic:
                    t = stat.get("interactionType", "")
                    c = int(stat.get("userInteractionCount", 0))
                    if "Watch" in t:
                        stats["views"] = c
                    elif "Like" in t:
                        stats["likes"] = c
                    elif "Share" in t:
                        stats["shares"] = c
                    elif "Comment" in t:
                        stats["comments"] = c
            if any(v > 0 for v in stats.values()):
                return stats
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    # Method 4: Regex fallback (look for stat numbers in various patterns)
    patterns = {
        "views": [r'"playCount"\s*:\s*(\d+)', r'"play_count"\s*:\s*(\d+)'],
        "likes": [r'"diggCount"\s*:\s*(\d+)', r'"like_count"\s*:\s*(\d+)'],
        "shares": [r'"shareCount"\s*:\s*(\d+)', r'"share_count"\s*:\s*(\d+)'],
        "comments": [r'"commentCount"\s*:\s*(\d+)', r'"comment_count"\s*:\s*(\d+)'],
        "saves": [r'"collectCount"\s*:\s*(\d+)', r'"collect_count"\s*:\s*(\d+)'],
        "followers": [r'"followerCount"\s*:\s*(\d+)'],
    }
    for key, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, html)
            if m:
                stats[key] = int(m.group(1))
                break

    return stats


def scrape_kol(username, url):
    """Scrape a single KOL's video stats."""
    print(f"   🔗 Resolving short URL...")
    real_url = resolve_short_url(url)
    print(f"   📄 Fetching: {real_url[:80]}...")

    html = fetch_page(real_url)
    if not html:
        # Try the short URL directly
        html = fetch_page(url)
    if not html:
        return None

    stats = extract_stats_from_html(html)
    return stats


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "scrape_results.json"
    results = {}

    total = len(KOL_LINKS)
    success = 0
    failed = 0

    print(f"🚀 JELE SODA TikTok Scraper")
    print(f"   {total} KOLs to scrape")
    print(f"   Output: {output_path}")
    print("=" * 50)

    for i, (username, url) in enumerate(KOL_LINKS.items(), 1):
        print(f"\n[{i}/{total}] @{username}")
        try:
            stats = scrape_kol(username, url)
            if stats and stats.get("views", 0) > 0:
                results[username] = stats
                print(f"   ✅ views={stats['views']:,}  likes={stats['likes']:,}  shares={stats['shares']}  comments={stats['comments']}")
                success += 1
            else:
                print(f"   ⚠️  No data retrieved (views=0)")
                results[username] = {"views": 0, "likes": 0, "shares": 0, "comments": 0, "saves": 0, "followers": 0}
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[username] = {"views": 0, "likes": 0, "shares": 0, "comments": 0, "saves": 0, "followers": 0}
            failed += 1

        # Rate limiting
        if i < total:
            time.sleep(2)

    # Write results
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"✅ Done! Success: {success}  |  Failed: {failed}  |  Total: {total}")
    print(f"📁 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
