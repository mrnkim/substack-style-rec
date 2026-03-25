"""
Update Twelve Labs video user_metadata with creator/category info from videos_metadata.csv.
Matches TL videos to CSV by normalizing filenames to titles.

Usage:
    python scripts/update_tl_metadata.py
"""

import csv
import json
import os
import re
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_CSV = os.path.join(SCRIPT_DIR, "videos_metadata.csv")

API_KEY = os.environ.get("TWELVELABS_API_KEY", "tlk_1EE5XJH3RGEG61293581G2FKC5MS")
INDEX_ID = os.environ.get("TWELVELABS_INDEX_ID", "69c37b6708cd679f8afbd748")
BASE_URL = "https://api.twelvelabs.io/v1.3"


def api_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"x-api-key": API_KEY},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_put(path: str, data: dict) -> int:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status


def normalize_title(filename: str) -> str:
    """Strip extension and normalize unicode punctuation for matching."""
    # Remove file extension
    name = re.sub(r"\.(mp4|webm|mkv|mov)$", "", filename, flags=re.IGNORECASE)
    # Normalize fullwidth punctuation to ASCII
    replacements = {
        "\uff1a": ":",  # fullwidth colon
        "\uff5c": "|",  # fullwidth vertical bar
        "\uff1f": "?",  # fullwidth question mark
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return name.strip().lower()


def load_csv_metadata() -> dict[str, dict]:
    """Load CSV and index by normalized title."""
    result = {}
    with open(VIDEOS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row["title"].strip().lower()
            result[title] = row
    return result


def main():
    # Load CSV metadata indexed by normalized title
    csv_data = load_csv_metadata()
    print(f"Loaded {len(csv_data)} videos from CSV\n")

    # Fetch all videos from TL index
    tl_videos = []
    page = 1
    while True:
        resp = api_get(f"/indexes/{INDEX_ID}/videos?page={page}&page_limit=50")
        tl_videos.extend(resp["data"])
        if page >= resp["page_info"]["total_page"]:
            break
        page += 1

    print(f"Found {len(tl_videos)} videos in TL index\n")

    matched = 0
    unmatched = []

    for v in tl_videos:
        tl_id = v["_id"]
        filename = v["system_metadata"]["filename"]
        normalized = normalize_title(filename)

        # Find matching CSV row
        csv_row = csv_data.get(normalized)
        if not csv_row:
            # Try partial matching
            for csv_title, row in csv_data.items():
                if csv_title in normalized or normalized in csv_title:
                    csv_row = row
                    break

        if not csv_row:
            unmatched.append(filename)
            print(f"  [SKIP] No CSV match: {filename}")
            continue

        user_metadata = {
            "youtubeId": csv_row["video_id"].strip(),
            "creatorId": csv_row["creator_id"].strip(),
            "creatorName": csv_row["creator_name"].strip(),
            "category": csv_row["category"].strip(),
            "uploadDate": csv_row["upload_date"].strip(),
        }

        status = api_put(
            f"/indexes/{INDEX_ID}/videos/{tl_id}",
            {"user_metadata": user_metadata},
        )
        matched += 1
        print(f"  [OK] {csv_row['creator_name']} — {csv_row['title'][:50]}")

    print(f"\n{'='*50}")
    print(f"Updated: {matched}")
    print(f"Unmatched: {len(unmatched)}")
    if unmatched:
        print("\nUnmatched files:")
        for f in unmatched:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
