"""
Download YouTube videos + collect metadata (video + creator).
Reads video_id list from curate_videos.csv, downloads via yt-dlp,
and outputs two enriched CSVs:
  - videos_metadata.csv  (video-level: title, duration, upload_date, channel, etc.)
  - creators_metadata.csv (unique creators: channel name, description, avatar)

Usage:
    python scripts/download_and_collect.py
"""

import subprocess
import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(SCRIPT_DIR, "curate_videos.csv")
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "downloads")
VIDEOS_OUT = os.path.join(SCRIPT_DIR, "videos_metadata.csv")
CREATORS_OUT = os.path.join(SCRIPT_DIR, "creators_metadata.csv")


def get_video_metadata(video_id: str) -> dict | None:
    """Use yt-dlp --dump-json to extract metadata without downloading."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-playlist",
        "--cookies-from-browser", "chrome",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        if result.returncode != 0:
            print(f"  [WARN] metadata fetch failed for {video_id}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"  [ERROR] {video_id}: {e}")
        return None


def download_video(video_id: str) -> bool:
    """Download video file via yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--cookies-from-browser", "chrome",
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/worst",
        "-o", f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "--no-playlist",
        "--extractor-retries", "3",
        "--fragment-retries", "3",
        "--skip-unavailable-fragments",
        "--ignore-errors",
        url,
    ]
    try:
        result = subprocess.run(cmd, check=False, timeout=600)
        return result.returncode == 0
    except Exception as e:
        print(f"  [ERROR] download {video_id}: {e}")
        return False


def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Read input CSV
    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vid = row.get("video_id", "").strip()
            if vid:
                rows.append(row)

    if not rows:
        print("No video IDs found in curate_videos.csv. Add video_id values and retry.")
        return

    print(f"Found {len(rows)} videos in curate_videos.csv\n")

    # Collect metadata + download
    video_records = []
    creators_seen = {}

    for i, row in enumerate(rows, 1):
        video_id = row["video_id"]
        category = row.get("category", "").strip()
        notes = row.get("notes", "").strip()

        print(f"[{i}/{len(rows)}] {video_id}")

        # Step 1: Get metadata
        print("  Fetching metadata...")
        meta = get_video_metadata(video_id)
        if not meta:
            print("  Skipping (no metadata)")
            continue

        # Extract video fields
        title = meta.get("title", "")
        duration = meta.get("duration", 0)
        upload_date_raw = meta.get("upload_date", "")  # YYYYMMDD
        upload_date = f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]}" if len(upload_date_raw) == 8 else ""
        thumbnail = meta.get("thumbnail", "")

        # Extract creator fields
        channel = meta.get("channel", "")
        channel_id = meta.get("channel_id", "")
        channel_url = meta.get("channel_url", "")
        uploader = meta.get("uploader", channel)

        # Creator description — yt-dlp doesn't always include this,
        # but channel_follower_count is available
        follower_count = meta.get("channel_follower_count", 0)

        video_records.append({
            "video_id": video_id,
            "title": title,
            "creator_id": channel_id,
            "creator_name": channel or uploader,
            "category": category,
            "duration": duration,
            "upload_date": upload_date,
            "thumbnail_url": thumbnail,
            "notes": notes,
        })

        # Collect unique creators
        if channel_id and channel_id not in creators_seen:
            creators_seen[channel_id] = {
                "creator_id": channel_id,
                "name": channel or uploader,
                "channel_url": channel_url,
                "follower_count": follower_count,
                "description": "",  # yt-dlp doesn't provide channel description
            }

        print(f"  Title: {title}")
        print(f"  Creator: {channel} ({channel_id})")
        print(f"  Duration: {duration}s")

        # Step 2: Download
        print("  Downloading...")
        if download_video(video_id):
            print("  Done!")
        else:
            print("  Download failed, metadata still saved")

    # Write videos CSV
    if video_records:
        with open(VIDEOS_OUT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "video_id", "title", "creator_id", "creator_name",
                "category", "duration", "upload_date", "thumbnail_url", "notes",
            ])
            writer.writeheader()
            writer.writerows(video_records)
        print(f"\nWrote {len(video_records)} videos to {VIDEOS_OUT}")

    # Write creators CSV
    if creators_seen:
        with open(CREATORS_OUT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "creator_id", "name", "channel_url", "follower_count", "description",
            ])
            writer.writeheader()
            writer.writerows(creators_seen.values())
        print(f"Wrote {len(creators_seen)} creators to {CREATORS_OUT}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Videos:   {len(video_records)}")
    print(f"Creators: {len(creators_seen)}")
    print(f"Downloads: {DOWNLOAD_DIR}/")
    print(f"\nNext steps:")
    print(f"  1. Review creators_metadata.csv — add descriptions manually")
    print(f"  2. Run upload_to_twelvelabs.py to index videos")
    print(f"  3. Run setup_pixeltable.py to seed PixelTable")


if __name__ == "__main__":
    main()
