#!/usr/bin/env python3
"""
TikTok KOL Data Scraper — JELE SODA 2026
==========================================
ดึงข้อมูลสาธารณะจาก TikTok โดยไม่ต้องใช้ Official API

มี 2 โหมด:
  1. Profile Mode  — ดึง followers, total likes จากหน้า profile
  2. Link Post Mode — ดึง views, likes, shares, comments, saves จาก link post โดยตรง
     → Export เป็น JSON ที่ import เข้า Dashboard ได้ทันที

วิธีใช้:
  pip install requests playwright
  playwright install chromium

  # โหมดปกติ (ดึง profile ทุกคน)
  python tiktok_scraper.py

  # โหมด link post (ดึงยอดจากโพสต์จริง → export JSON สำหรับ dashboard)
  python tiktok_scraper.py --linkpost

  # ดึง link post แบบ requests (ไม่ต้อง playwright)
  python tiktok_scraper.py --linkpost --method requests
"""

import json
import csv
import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path

# ==================== CONFIG ====================

# ใส่ username ของ KOLs ที่ต้องการดึงข้อมูล (ไม่ต้องใส่ @)
# === JELE SODA 2026 Campaign ===
KOLS = [
    # Mega & Macro (Main x5)
    "biw_songkran",       # บิวบอง — ภาคอีสาน 1.9M
    "jack.ittiphon",      # jack.ittiphon — ภาคกลาง 1.9M
    "fasin22052545",      # พี่บังจับไมค์ — ภาคใต้ 297.9K
    "ovapachannel",       # OVAPA CHANNEL — ภาคเหนือ 397.2K
    "nophuwanet",         # เซียนหรั่ง — ภาคอีสาน 1.7M

    # Batch 1 [Post Date 1 Mar]
    "plugsweden",         # plugsweden — ภาคกลาง 198.8K
    "pakkaput17",         # pakkaput17 — ภาคกลาง 369.7K
    "kuanpuantiew",       # กวนป่วนเที่ยว — ภาคกลาง 1.1M
    "pexjakkajee",        # เป๊กจั๊กกะจี้ — ภาคกลาง 1.4M
    "puwanaipison",       # ไพซอล — ภาคกลาง 335.9K
    "gotarm65",           # gotarm65 — ภาคเหนือ 563K
    "tikbadai",           # อ้ายติ๊กบะดาย — ภาคเหนือ 680.8K
    "patpaladmuang",      # patpaladmuang — ภาคเหนือ 243.7K

    # Batch 2 [Post Date 8 Mar]
    "saokrungthep",       # สาวกรุงเทพ — ภาคกลาง 235.2K
    "ll0499",             # MY K ME KEN — ภาคกลาง 248K
    "pooliepraew",        # pooliepraew — ภาคกลาง 1.2M
    "f_u_i_",             # f_u_i_ — ภาคกลาง 212.2K
    "coochamp",           # แช้มกับทีวีคู่ใจ — ภาคเหนือ 639.1K
    "aodbom2",            # ปุณณภพ เฟรนลี่ — ภาคอีสาน 1.7M
    "wootza5555",         # wootza5555 — ภาคอีสาน 985.1K
    "royver_th",          # royver_th — ภาคใต้ 793.3K

    # Batch 3 [Post Date 15 Mar]
    "bookteerapat",       # บุ๊ค ธีร์ — ภาคอีสาน 694.7K
    "juno55555",          # บักจูโน่ — ภาคอีสาน 2.6M
    "bunyaporn_2009",     # พาย คอนเฟลก — ภาคใต้ 5.9M
    "thebellchanel",      # The Bell channel — ภาคใต้ 331.4K
    "tan_slaz19",         # อินฟลูน้ำตาลตก — ภาคกลาง 143.8K

    # Batch 5 [Post Date 29 Mar] — Mixology
    "kayshomebar",        # kayshomebar — Mixology 39.1K
    "raa_reun_core",      # raa_reun_core — Mixology 424K
    "maxk_litt",          # maxk_litt — Mixology 703.6K
]

# === Link Posts (โพสต์จริงของแคมเปญ JELE SODA) ===
# username → TikTok post URL
LINK_POSTS = {
    "biw_songkran":  "https://vt.tiktok.com/ZSm7UqSxm/",
    "fasin22052545":  "https://vt.tiktok.com/ZSmcaAb2h/",
    "ovapachannel":   "https://vt.tiktok.com/ZSmcm17pD/",
    "plugsweden":     "https://vt.tiktok.com/ZSmcapBu1/",
    "pakkaput17":     "https://vt.tiktok.com/ZSmcaGQy3/",
    "kuanpuantiew":   "https://vt.tiktok.com/ZSmcato1w/",
    "pexjakkajee":    "https://vt.tiktok.com/ZSm7yUL5N/",
    "puwanaipison":   "https://vt.tiktok.com/ZSmcaTqdj/",
    "gotarm65":       "https://vt.tiktok.com/ZSm7MXU59/",
    "tikbadai":       "https://vt.tiktok.com/ZSmcW2HWK/",
    "patpaladmuang":  "https://vt.tiktok.com/ZSmcaqqea/",
}

# Output file
OUTPUT_CSV = "kol_tiktok_data.csv"
OUTPUT_JSON = "kol_tiktok_data.json"
OUTPUT_LINKPOST_JSON = "kol_linkpost_data.json"  # สำหรับ import เข้า dashboard

# Lark Base Config (ถ้าต้องการเขียนเข้า Lark Base โดยตรง)
LARK_APP_ID = ""        # ใส่ App ID จาก Lark Developer Console
LARK_APP_SECRET = ""    # ใส่ App Secret
LARK_BASE_APP_TOKEN = ""  # ใส่ Base App Token (จาก URL ของ Base)
LARK_TABLE_ID = ""      # ใส่ Table ID

# ==================== METHOD 1: Playwright (แนะนำ) ====================

def scrape_with_playwright(usernames):
    """ดึงข้อมูล TikTok ด้วย Playwright (headless browser)"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ ต้องติดตั้ง playwright ก่อน:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return None

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        for i, username in enumerate(usernames):
            print(f"\n[{i+1}/{len(usernames)}] กำลังดึงข้อมูล: @{username}")
            page = context.new_page()

            try:
                url = f"https://www.tiktok.com/@{username}"
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)  # รอให้โหลดเสร็จ

                data = extract_profile_data(page, username)
                if data:
                    results.append(data)
                    print(f"   ✅ {username}: {data['followers']:,} followers, {data['total_likes']:,} likes")
                else:
                    print(f"   ⚠️ ไม่สามารถดึงข้อมูล {username} ได้")
                    results.append(empty_record(username))

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append(empty_record(username))
            finally:
                page.close()

            # หน่วงเวลาเพื่อไม่ให้โดน rate limit
            if i < len(usernames) - 1:
                delay = 3 + (i % 3)  # 3-5 วินาที
                print(f"   ⏳ รอ {delay} วินาที...")
                time.sleep(delay)

        browser.close()

    return results


def extract_profile_data(page, username):
    """ดึงข้อมูลจากหน้า profile TikTok"""
    try:
        # วิธีที่ 1: ดึงจาก JSON-LD / script tag
        data = extract_from_script_tag(page)
        if data:
            return data

        # วิธีที่ 2: ดึงจาก DOM elements
        data = extract_from_dom(page, username)
        if data:
            return data

    except Exception as e:
        print(f"   ⚠️ extract error: {e}")

    return None


def extract_from_script_tag(page):
    """ดึงข้อมูลจาก __UNIVERSAL_DATA_FOR_REHYDRATION__ script tag"""
    try:
        script_content = page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script#__UNIVERSAL_DATA_FOR_REHYDRATION__');
                for (const s of scripts) {
                    try { return s.textContent; } catch(e) {}
                }
                // ลองหา SIGI_STATE
                const sigi = document.querySelectorAll('script#SIGI_STATE');
                for (const s of sigi) {
                    try { return s.textContent; } catch(e) {}
                }
                return null;
            }
        """)

        if not script_content:
            return None

        json_data = json.loads(script_content)

        # Parse __DEFAULT_SCOPE__
        if "__DEFAULT_SCOPE__" in json_data:
            scope = json_data["__DEFAULT_SCOPE__"]
            user_detail = scope.get("webapp.user-detail", {})
            user_info = user_detail.get("userInfo", {})
            user = user_info.get("user", {})
            stats = user_info.get("stats", {})

            if user and stats:
                return {
                    "username": user.get("uniqueId", ""),
                    "nickname": user.get("nickname", ""),
                    "bio": user.get("signature", ""),
                    "verified": user.get("verified", False),
                    "avatar": user.get("avatarLarger", ""),
                    "followers": int(stats.get("followerCount", 0)),
                    "following": int(stats.get("followingCount", 0)),
                    "total_likes": int(stats.get("heartCount", 0)),
                    "total_videos": int(stats.get("videoCount", 0)),
                    "platform": "TikTok",
                    "scraped_at": datetime.now().isoformat(),
                }

        # Parse SIGI_STATE format
        if "UserModule" in json_data:
            users = json_data["UserModule"].get("users", {})
            stats_all = json_data["UserModule"].get("stats", {})
            for uid, udata in users.items():
                ustats = stats_all.get(uid, {})
                return {
                    "username": udata.get("uniqueId", uid),
                    "nickname": udata.get("nickname", ""),
                    "bio": udata.get("signature", ""),
                    "verified": udata.get("verified", False),
                    "avatar": udata.get("avatarLarger", ""),
                    "followers": int(ustats.get("followerCount", 0)),
                    "following": int(ustats.get("followingCount", 0)),
                    "total_likes": int(ustats.get("heartCount", 0)),
                    "total_videos": int(ustats.get("videoCount", 0)),
                    "platform": "TikTok",
                    "scraped_at": datetime.now().isoformat(),
                }

    except Exception as e:
        print(f"   ⚠️ script parse error: {e}")

    return None


def extract_from_dom(page, username):
    """ดึงข้อมูลจาก DOM elements โดยตรง"""
    try:
        data = page.evaluate("""
            () => {
                const getText = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.textContent.trim() : '';
                };

                // ลองหาจาก data-e2e attributes
                const followers = getText('[data-e2e="followers-count"]');
                const following = getText('[data-e2e="following-count"]');
                const likes = getText('[data-e2e="likes-count"]');
                const bio = getText('[data-e2e="user-bio"]');
                const nickname = getText('[data-e2e="user-subtitle"]') || getText('h1');
                const videos = getText('[data-e2e="video-count"]');

                return { followers, following, likes, bio, nickname, videos };
            }
        """)

        if data and data.get("followers"):
            return {
                "username": username,
                "nickname": data.get("nickname", ""),
                "bio": data.get("bio", ""),
                "verified": False,
                "avatar": "",
                "followers": parse_count(data["followers"]),
                "following": parse_count(data.get("following", "0")),
                "total_likes": parse_count(data.get("likes", "0")),
                "total_videos": parse_count(data.get("videos", "0")),
                "platform": "TikTok",
                "scraped_at": datetime.now().isoformat(),
            }
    except Exception as e:
        print(f"   ⚠️ DOM parse error: {e}")

    return None


def parse_count(text):
    """แปลง '1.5M', '10.2K' เป็นตัวเลข"""
    if not text:
        return 0
    text = text.strip().replace(",", "")

    multipliers = {"K": 1000, "M": 1000000, "B": 1000000000}
    for suffix, mult in multipliers.items():
        if text.upper().endswith(suffix):
            try:
                return int(float(text[:-1]) * mult)
            except ValueError:
                return 0

    try:
        return int(float(text))
    except ValueError:
        return 0


def empty_record(username):
    """สร้าง record ว่างสำหรับ username ที่ดึงไม่ได้"""
    return {
        "username": username,
        "nickname": "",
        "bio": "",
        "verified": False,
        "avatar": "",
        "followers": 0,
        "following": 0,
        "total_likes": 0,
        "total_videos": 0,
        "platform": "TikTok",
        "scraped_at": datetime.now().isoformat(),
    }


# ==================== METHOD 2: Requests (เบากว่า แต่อาจโดน block) ====================

def scrape_with_requests(usernames):
    """ดึงข้อมูลด้วย requests (ไม่ต้อง browser แต่อาจถูก block ง่ายกว่า)"""
    import requests

    results = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    })

    for i, username in enumerate(usernames):
        print(f"\n[{i+1}/{len(usernames)}] ดึงข้อมูล: @{username}")

        try:
            url = f"https://www.tiktok.com/@{username}"
            resp = session.get(url, timeout=15)

            if resp.status_code == 200:
                data = parse_html_for_data(resp.text, username)
                if data:
                    results.append(data)
                    print(f"   ✅ {username}: {data['followers']:,} followers")
                else:
                    print(f"   ⚠️ ไม่เจอข้อมูลใน HTML")
                    results.append(empty_record(username))
            else:
                print(f"   ❌ HTTP {resp.status_code}")
                results.append(empty_record(username))

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(empty_record(username))

        if i < len(usernames) - 1:
            time.sleep(5)

    return results


def parse_html_for_data(html, username):
    """Parse ข้อมูลจาก HTML ของ TikTok"""
    # หา __UNIVERSAL_DATA_FOR_REHYDRATION__
    pattern = r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)

    if not match:
        # ลอง SIGI_STATE
        pattern = r'<script id="SIGI_STATE"[^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)

    if not match:
        return None

    try:
        json_data = json.loads(match.group(1))

        if "__DEFAULT_SCOPE__" in json_data:
            scope = json_data["__DEFAULT_SCOPE__"]
            user_info = scope.get("webapp.user-detail", {}).get("userInfo", {})
            user = user_info.get("user", {})
            stats = user_info.get("stats", {})

            if stats:
                return {
                    "username": user.get("uniqueId", username),
                    "nickname": user.get("nickname", ""),
                    "bio": user.get("signature", ""),
                    "verified": user.get("verified", False),
                    "avatar": user.get("avatarLarger", ""),
                    "followers": int(stats.get("followerCount", 0)),
                    "following": int(stats.get("followingCount", 0)),
                    "total_likes": int(stats.get("heartCount", 0)),
                    "total_videos": int(stats.get("videoCount", 0)),
                    "platform": "TikTok",
                    "scraped_at": datetime.now().isoformat(),
                }
    except json.JSONDecodeError:
        pass

    return None


# ==================== EXPORT ====================

def export_to_csv(results, filename):
    """Export เป็น CSV"""
    if not results:
        print("❌ ไม่มีข้อมูลให้ export")
        return

    # คำนวณ tier และ engagement
    for r in results:
        f = r["followers"]
        r["tier"] = "Nano" if f < 10000 else "Micro" if f < 50000 else "Mid" if f < 100000 else "Macro" if f < 1000000 else "Mega"
        r["category"] = ""  # ต้องใส่เอง
        r["total_engagement"] = r["total_likes"]  # likes เป็น engagement หลักที่ดึงได้จาก profile
        r["er_followers"] = f"{(r['total_likes'] / r['followers'] * 100):.1f}%" if r["followers"] > 0 else "0%"

    headers = [
        "KOL_Username", "Nickname", "KOL_tier", "Platform", "Category",
        "Total_Followers_max", "Following", "Total_likes_max", "Total_Videos",
        "Total_Engagement", "ER%_Followers", "Bio", "Verified", "Scraped_At"
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in results:
            writer.writerow([
                r["username"], r["nickname"], r["tier"], r["platform"], r["category"],
                r["followers"], r["following"], r["total_likes"], r["total_videos"],
                r["total_engagement"], r["er_followers"], r["bio"], r["verified"], r["scraped_at"]
            ])

    print(f"\n✅ บันทึก CSV: {filename} ({len(results)} KOLs)")


def export_to_json(results, filename):
    """Export เป็น JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ บันทึก JSON: {filename}")


# ==================== LARK BASE API ====================

def get_lark_token():
    """ขอ Tenant Access Token จาก Lark"""
    import requests

    if not LARK_APP_ID or not LARK_APP_SECRET:
        print("❌ ยังไม่ได้ใส่ LARK_APP_ID / LARK_APP_SECRET")
        return None

    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET,
    })

    data = resp.json()
    if data.get("code") == 0:
        return data["tenant_access_token"]
    else:
        print(f"❌ Lark Auth Error: {data}")
        return None


def write_to_lark_base(results):
    """เขียนข้อมูลเข้า Lark Base"""
    import requests

    token = get_lark_token()
    if not token:
        return

    if not LARK_BASE_APP_TOKEN or not LARK_TABLE_ID:
        print("❌ ยังไม่ได้ใส่ LARK_BASE_APP_TOKEN / LARK_TABLE_ID")
        return

    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{LARK_BASE_APP_TOKEN}/tables/{LARK_TABLE_ID}/records/batch_create"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    records = []
    for r in results:
        f = r["followers"]
        tier = "Nano" if f < 10000 else "Micro" if f < 50000 else "Mid" if f < 100000 else "Macro" if f < 1000000 else "Mega"

        records.append({
            "fields": {
                "KOL_Username": r["username"],
                "Nickname": r.get("nickname", ""),
                "KOL_tier": tier,
                "Platform": r["platform"],
                "Total_Followers_max": r["followers"],
                "Total_likes_max": r["total_likes"],
                "Total_Videos": r["total_videos"],
                "Bio": r.get("bio", ""),
                "Verified": r.get("verified", False),
                "Scraped_At": r["scraped_at"],
            }
        })

    # Batch create (max 500 per request)
    batch_size = 500
    total_created = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        resp = requests.post(url, headers=headers, json={"records": batch})
        data = resp.json()

        if data.get("code") == 0:
            created = len(data.get("data", {}).get("records", []))
            total_created += created
            print(f"   ✅ เขียน Lark Base: {created} records")
        else:
            print(f"   ❌ Lark Base Error: {data.get('msg', 'Unknown error')}")

    print(f"\n✅ เขียนเข้า Lark Base สำเร็จ: {total_created} records")


# ==================== LINK POST SCRAPER ====================

def scrape_linkposts_playwright(link_posts):
    """ดึงยอด views/likes/shares/comments/saves จาก TikTok link posts ด้วย Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ ต้องติดตั้ง playwright ก่อน:")
        print("   pip install playwright && playwright install chromium")
        return None

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        for i, (username, url) in enumerate(link_posts.items()):
            print(f"\n[{i+1}/{len(link_posts)}] ดึงยอดโพสต์: @{username}")
            print(f"   URL: {url}")
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)

                data = extract_video_stats(page, username)
                if data:
                    data["link"] = url
                    results.append(data)
                    print(f"   ✅ views={data['views']:,}  likes={data['likes']:,}  comments={data['comments']:,}  shares={data['shares']:,}  saves={data['saves']:,}")
                else:
                    print(f"   ⚠️ ไม่สามารถดึงข้อมูลโพสต์ได้")
                    results.append({"username": username, "link": url, "views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "error": True})

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({"username": username, "link": url, "views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "error": True})
            finally:
                page.close()

            if i < len(link_posts) - 1:
                delay = 3 + (i % 3)
                print(f"   ⏳ รอ {delay} วินาที...")
                time.sleep(delay)

        browser.close()

    return results


def extract_video_stats(page, username):
    """ดึง stats จากหน้า TikTok video"""
    try:
        # วิธี 1: จาก __UNIVERSAL_DATA_FOR_REHYDRATION__
        script_content = page.evaluate("""
            () => {
                const el = document.querySelector('script#__UNIVERSAL_DATA_FOR_REHYDRATION__');
                return el ? el.textContent : null;
            }
        """)

        if script_content:
            json_data = json.loads(script_content)
            scope = json_data.get("__DEFAULT_SCOPE__", {})
            video_detail = scope.get("webapp.video-detail", {})
            item_info = video_detail.get("itemInfo", {}).get("itemStruct", {})
            stats = item_info.get("stats", {})

            if stats:
                return {
                    "username": username,
                    "views": int(stats.get("playCount", 0)),
                    "likes": int(stats.get("diggCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "shares": int(stats.get("shareCount", 0)),
                    "saves": int(stats.get("collectCount", 0)),
                }

        # วิธี 2: จาก DOM
        data = page.evaluate("""
            () => {
                const getText = (sel) => {
                    const el = document.querySelector(sel);
                    return el ? el.textContent.trim() : '0';
                };
                return {
                    views: getText('[data-e2e="video-views"]') || getText('[data-e2e="browse-video-count"]'),
                    likes: getText('[data-e2e="like-count"]') || getText('[data-e2e="browse-like-count"]'),
                    comments: getText('[data-e2e="comment-count"]') || getText('[data-e2e="browse-comment-count"]'),
                    shares: getText('[data-e2e="share-count"]'),
                    saves: getText('[data-e2e="undefined-count"]') || '0',
                };
            }
        """)

        if data:
            return {
                "username": username,
                "views": parse_count(data.get("views", "0")),
                "likes": parse_count(data.get("likes", "0")),
                "comments": parse_count(data.get("comments", "0")),
                "shares": parse_count(data.get("shares", "0")),
                "saves": parse_count(data.get("saves", "0")),
            }

    except Exception as e:
        print(f"   ⚠️ extract video error: {e}")

    return None


def scrape_linkposts_requests(link_posts):
    """ดึงยอดจาก link posts ด้วย requests (ไม่ต้อง playwright)"""
    import requests as req

    results = []
    session = req.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    })

    for i, (username, url) in enumerate(link_posts.items()):
        print(f"\n[{i+1}/{len(link_posts)}] ดึงยอดโพสต์: @{username}")

        try:
            resp = session.get(url, timeout=15, allow_redirects=True)
            if resp.status_code == 200:
                # หา __UNIVERSAL_DATA_FOR_REHYDRATION__
                match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
                if match:
                    json_data = json.loads(match.group(1))
                    scope = json_data.get("__DEFAULT_SCOPE__", {})
                    video_detail = scope.get("webapp.video-detail", {})
                    item = video_detail.get("itemInfo", {}).get("itemStruct", {})
                    stats = item.get("stats", {})

                    if stats:
                        data = {
                            "username": username,
                            "link": url,
                            "views": int(stats.get("playCount", 0)),
                            "likes": int(stats.get("diggCount", 0)),
                            "comments": int(stats.get("commentCount", 0)),
                            "shares": int(stats.get("shareCount", 0)),
                            "saves": int(stats.get("collectCount", 0)),
                        }
                        results.append(data)
                        print(f"   ✅ views={data['views']:,}  likes={data['likes']:,}")
                        continue

                print(f"   ⚠️ ไม่เจอข้อมูลใน HTML")
            else:
                print(f"   ❌ HTTP {resp.status_code}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

        results.append({"username": username, "link": url, "views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "error": True})

        if i < len(link_posts) - 1:
            time.sleep(5)

    return results


def export_linkpost_json(results, filename):
    """Export link post data เป็น JSON ที่ import เข้า Dashboard ได้เลย"""
    # แปลงเป็นฟอร์แมตที่ dashboard รู้จัก
    dashboard_data = []
    for r in results:
        # ดึง follower/tier/category จาก KOLS_META ถ้ามี
        meta = KOLS_META.get(r["username"], {})
        dashboard_data.append({
            "username": r["username"],
            "tier": meta.get("tier", "Macro"),
            "platform": "TikTok",
            "category": meta.get("category", ""),
            "followers": meta.get("followers", 0),
            "views": r["views"],
            "likes": r["likes"],
            "shares": r["shares"],
            "comments": r["comments"],
            "saves": r["saves"],
            "posts": 1,
            "kpi_views": meta.get("kpi", 0),
            "posted": True,
            "link": r["link"],
            "batch": meta.get("batch", ""),
        })

    # เพิ่ม KOL ที่ยังไม่มี link post (posted=false)
    posted_usernames = {r["username"] for r in results}
    for username in KOLS:
        if username not in posted_usernames:
            meta = KOLS_META.get(username, {})
            dashboard_data.append({
                "username": username,
                "tier": meta.get("tier", "Macro"),
                "platform": "TikTok",
                "category": meta.get("category", ""),
                "followers": meta.get("followers", 0),
                "views": 0, "likes": 0, "shares": 0, "comments": 0, "saves": 0,
                "posts": 0,
                "kpi_views": meta.get("kpi", 0),
                "posted": False,
                "batch": meta.get("batch", ""),
            })

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    # สรุป
    ok = [r for r in results if not r.get("error")]
    total_views = sum(r["views"] for r in ok)
    total_eng = sum(r["likes"] + r["comments"] + r["shares"] + r["saves"] for r in ok)
    print(f"\n{'='*60}")
    print(f"📊 สรุปยอด Link Post")
    print(f"   ดึงสำเร็จ: {len(ok)}/{len(results)} โพสต์")
    print(f"   Total Views: {total_views:,}")
    print(f"   Total Engagement: {total_eng:,}")
    print(f"\n✅ บันทึก JSON: {filename}")
    print(f"   → เปิด Dashboard → กด 'Import JSON' → เลือกไฟล์นี้")
    print(f"{'='*60}")


# === KOL Metadata (สำหรับ export เข้า dashboard) ===
KOLS_META = {
    "biw_songkran":   {"tier":"Mega","category":"ภาคอีสาน","followers":1900000,"kpi":10000000,"batch":"Main"},
    "jack.ittiphon":  {"tier":"Mega","category":"ภาคกลาง","followers":1900000,"kpi":0,"batch":"Main"},
    "fasin22052545":  {"tier":"Macro","category":"ภาคใต้","followers":297900,"kpi":0,"batch":"Main"},
    "ovapachannel":   {"tier":"Macro","category":"ภาคเหนือ","followers":397200,"kpi":0,"batch":"Main"},
    "nophuwanet":     {"tier":"Mega","category":"ภาคอีสาน","followers":1700000,"kpi":0,"batch":"Main"},
    "plugsweden":     {"tier":"Macro","category":"ภาคกลาง","followers":198800,"kpi":0,"batch":"Batch 1"},
    "pakkaput17":     {"tier":"Macro","category":"ภาคกลาง","followers":369700,"kpi":0,"batch":"Batch 1"},
    "kuanpuantiew":   {"tier":"Mega","category":"ภาคกลาง","followers":1100000,"kpi":0,"batch":"Batch 1"},
    "pexjakkajee":    {"tier":"Mega","category":"ภาคกลาง","followers":1400000,"kpi":0,"batch":"Batch 1"},
    "puwanaipison":   {"tier":"Macro","category":"ภาคกลาง","followers":335900,"kpi":0,"batch":"Batch 1"},
    "gotarm65":       {"tier":"Macro","category":"ภาคเหนือ","followers":563000,"kpi":0,"batch":"Batch 1"},
    "tikbadai":       {"tier":"Macro","category":"ภาคเหนือ","followers":680800,"kpi":0,"batch":"Batch 1"},
    "patpaladmuang":  {"tier":"Macro","category":"ภาคเหนือ","followers":243700,"kpi":0,"batch":"Batch 1"},
    "saokrungthep":   {"tier":"Macro","category":"ภาคกลาง","followers":235200,"kpi":0,"batch":"Batch 2"},
    "ll0499":         {"tier":"Macro","category":"ภาคกลาง","followers":248000,"kpi":0,"batch":"Batch 2"},
    "pooliepraew":    {"tier":"Mega","category":"ภาคกลาง","followers":1200000,"kpi":0,"batch":"Batch 2"},
    "f_u_i_":         {"tier":"Macro","category":"ภาคกลาง","followers":212200,"kpi":0,"batch":"Batch 2"},
    "coochamp":       {"tier":"Macro","category":"ภาคเหนือ","followers":639100,"kpi":0,"batch":"Batch 2"},
    "aodbom2":        {"tier":"Mega","category":"ภาคอีสาน","followers":1700000,"kpi":0,"batch":"Batch 2"},
    "wootza5555":     {"tier":"Macro","category":"ภาคอีสาน","followers":985100,"kpi":0,"batch":"Batch 2"},
    "royver_th":      {"tier":"Macro","category":"ภาคใต้","followers":793300,"kpi":0,"batch":"Batch 2"},
    "bookteerapat":   {"tier":"Macro","category":"ภาคอีสาน","followers":694700,"kpi":0,"batch":"Batch 3"},
    "juno55555":      {"tier":"Mega","category":"ภาคอีสาน","followers":2600000,"kpi":0,"batch":"Batch 3"},
    "bunyaporn_2009": {"tier":"Mega","category":"ภาคใต้","followers":5900000,"kpi":0,"batch":"Batch 3"},
    "thebellchanel":  {"tier":"Macro","category":"ภาคใต้","followers":331400,"kpi":0,"batch":"Batch 3"},
    "tan_slaz19":     {"tier":"Macro","category":"ภาคกลาง","followers":143800,"kpi":0,"batch":"Batch 3"},
    "kayshomebar":    {"tier":"Micro","category":"Mixology","followers":39100,"kpi":0,"batch":"Batch 5"},
    "raa_reun_core":  {"tier":"Macro","category":"Mixology","followers":424000,"kpi":0,"batch":"Batch 5"},
    "maxk_litt":      {"tier":"Macro","category":"Mixology","followers":703600,"kpi":0,"batch":"Batch 5"},
}


# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("  TikTok KOL Data Scraper — JELE SODA 2026")
    print("=" * 60)

    # ตรวจ args
    args = sys.argv[1:]
    linkpost_mode = "--linkpost" in args
    use_requests = "--method" in args and "requests" in args

    # ==================== โหมด Link Post ====================
    if linkpost_mode:
        print(f"\n🔗 โหมด Link Post — ดึงยอดจากโพสต์จริง")
        print(f"   จำนวนโพสต์: {len(LINK_POSTS)}")
        method = "requests" if use_requests else "playwright"
        print(f"   วิธี: {method}")

        if use_requests:
            results = scrape_linkposts_requests(LINK_POSTS)
        else:
            results = scrape_linkposts_playwright(LINK_POSTS)

        if not results:
            print("\n❌ ไม่สามารถดึงข้อมูลได้")
            return

        export_linkpost_json(results, OUTPUT_LINKPOST_JSON)

        print(f"\n📋 ขั้นตอนต่อไป:")
        print(f"   1. เปิด kol-overview-dashboard.html ใน browser")
        print(f"   2. กดปุ่ม '📤 Import JSON'")
        print(f"   3. เลือกไฟล์ {OUTPUT_LINKPOST_JSON}")
        print(f"   4. ข้อมูลจะอัปเดตทันที!")
        return

    # ==================== โหมดปกติ (Profile) ====================
    if not KOLS:
        print("\n❌ ยังไม่ได้ใส่ username ใน KOLS list")
        return

    print(f"\n📋 จำนวน KOLs: {len(KOLS)}")
    print(f"   {', '.join(KOLS[:5])}{'...' if len(KOLS) > 5 else ''}")

    # เลือกวิธีดึงข้อมูล
    print("\n🔧 วิธีดึงข้อมูล:")
    print("   1. Playwright (แนะนำ — แม่นยำกว่า)")
    print("   2. Requests (เร็วกว่า แต่อาจถูก block)")

    choice = input("\nเลือก (1/2) [default=1]: ").strip() or "1"

    if choice == "2":
        results = scrape_with_requests(KOLS)
    else:
        results = scrape_with_playwright(KOLS)

    if not results:
        print("\n❌ ไม่สามารถดึงข้อมูลได้")
        return

    # Export
    print("\n" + "=" * 60)
    print("📤 Export ข้อมูล")
    export_to_csv(results, OUTPUT_CSV)
    export_to_json(results, OUTPUT_JSON)

    # ถาม Lark Base
    if LARK_APP_ID and LARK_APP_SECRET:
        write_lark = input("\n📤 เขียนข้อมูลเข้า Lark Base ด้วย? (y/n) [default=n]: ").strip().lower()
        if write_lark == "y":
            write_to_lark_base(results)
    else:
        print("\n💡 เคล็ดลับ: ใส่ LARK_APP_ID + LARK_APP_SECRET ในไฟล์นี้เพื่อเขียนข้อมูลเข้า Lark Base โดยตรง")

    # สรุป
    print("\n" + "=" * 60)
    print("📊 สรุป")
    print(f"   ดึงสำเร็จ: {sum(1 for r in results if r['followers'] > 0)}/{len(results)} KOLs")
    print(f"   ไฟล์ CSV: {OUTPUT_CSV}")
    print(f"   ไฟล์ JSON: {OUTPUT_JSON}")
    print(f"\n💡 นำ CSV ไป import ใน KOL Dashboard หรือ Lark Base ได้เลย!")
    print(f"💡 ใช้ --linkpost เพื่อดึงยอดจากโพสต์จริงของแคมเปญ")
    print("=" * 60)


if __name__ == "__main__":
    main()
