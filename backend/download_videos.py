"""Download video files for Pixeltable pxt.Video embedding.

Two sources:
  - YouTube via yt-dlp (default, works locally)
  - Cloudflare R2 mirror via --r2 (use on cloud hosts where YouTube blocks yt-dlp)

Usage:
    uv run download_videos.py              # 3 quick-start videos from YouTube
    uv run download_videos.py --full       # all 30 videos from YouTube
    uv run download_videos.py --r2         # 3 quick-start videos from R2
    uv run download_videos.py --r2 --full  # all 25 indexed videos from R2
"""

import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUICK_YOUTUBE_IDS = {"sO4te2QNsHY", "ntPGl8UyIq4", "QpKypvDjiPM"}

SCRIPT_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = SCRIPT_DIR / "video_files"
VIDEOS_CSV = SCRIPT_DIR.parent / "scripts" / "videos_metadata.csv"

# ---------------------------------------------------------------------------
# YouTube (yt-dlp)
# ---------------------------------------------------------------------------

YDL_OPTS = {
    "format": "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]",
    "merge_output_format": "mp4",
    "noplaylist": True,
    "socket_timeout": 30,
    "quiet": True,
    "no_warnings": True,
}


def _download_youtube(youtube_id: str, output_dir: Path) -> Path | None:
    output_path = output_dir / f"{youtube_id}.mp4"
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("  Already downloaded: %s", output_path.name)
        return output_path

    url = f"https://www.youtube.com/watch?v={youtube_id}"
    opts = {**YDL_OPTS, "outtmpl": str(output_path)}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        if output_path.exists() and output_path.stat().st_size > 0:
            size_mb = output_path.stat().st_size / 1e6
            logger.info("  Downloaded: %s (%.1f MB)", output_path.name, size_mb)
            return output_path
        logger.warning("  Download produced empty file for %s", youtube_id)
        return None
    except yt_dlp.utils.DownloadError as e:
        logger.warning("  Failed to download %s: %s", youtube_id, str(e)[:200])
        return None
    except Exception as e:
        logger.warning("  Error downloading %s: %s", youtube_id, e)
        return None


# ---------------------------------------------------------------------------
# Cloudflare R2 mirror
# YouTube blocks yt-dlp from datacenter IPs (Render, AWS, GCP, etc.).
# Upload video files to an R2 bucket and use --r2 to download from there.
# ---------------------------------------------------------------------------

R2_BASE = "https://pub-3d90ba141b2a453d9ada94f279c78419.r2.dev"

R2_FILES: dict[str, str] = {
    "j9Qm6_lEdcQ": "Dakota Johnson Is Not Okay While Eating Spicy Wings \uff5c Hot Ones.webm",
    "5DDB_DNWGYE": "KPop Demon Hunters \uff5c Hot Ones Versus.webm",
    "d5uhih_I7Jw": "Madison Beer Lives Out Her Dream While Eating Spicy Wings \uff5c Hot Ones.webm",
    "Ed9OqOQAfBs": "Lessons from $80M CEO on Building a Strong Personal Brand.mp4",
    "sO4te2QNsHY": "What Is Branding 4 Minute Crash Course.mp4",
    "y7rvDA3MARk": "We interviewed the Mozart of Gen Z.mp4",
    "d18ud-4epP8": "Why the Biggest YouTube Family Just Went to Netflix\uff1a Jordan Matter.webm",
    "BFU1OCkhBwo": "AI Expert Here Is What The World Looks Like In 2 Years! Tristan Harris.mp4",
    "fpETS6q1Hww": "Daniel Priestley AI Will Make Plumbers Earn More Than Lawyers! (2029 PREDICTION).mp4",
    "Xm_PHZXGe-w": "Theyre Lying About Healthy Foods Sugar! Shocking New Research Thats Harming You.mp4",
    "WcHWQnoE95w": "Why You Don\u2019t Trust Tap Water.mp4",
    "WYQxG4KEzvo": "The Problem With Elon Musk.mp4",
    "jITKnb0tYaM": "How to legislate AI.webm",
    "_Ux13UEqIYo": "Yikes.webm",
    "shB7wRZ2h5Y": "Are We Really Ready for AI Coding\uff1f.mp4",
    "ntPGl8UyIq4": "The Metaverse Only Has 900 Users.webm",
    "TBDWomgRgWU": "How smooth jazz took over the \u201890s.webm",
    "8A1Aj1_EF9Y": "The sound that connects Stravinsky to Bruno Mars.mp4",
    "QpKypvDjiPM": "Why more pop songs should end with a fade out.mp4",
    "j4KlMiMgVLM": "30 years fine-tuning micro-homestead oasis nothing missing little extra.webm",
    "dG2b_Klf5R4": "Couples traditional underground home hides in magical Nordic forest.webm",
    "LPUMrjwJgGs": "Nordic homestead near Russian border couples no-bank no-phone life.mp4",
    "wjZofJX0v4M": "Transformers, the tech behind LLMs \uff5c Deep Learning Chapter 5.mp4",
    "IQqtsm-bBRU": "This open problem taught me what topology is.webm",
    "BHdbsHFs2P0": "The Hairy Ball Theorem.webm",
    "RRHU-fvsNo0": "5 Rules That Will Change Your Life Immediately.mp4",
    "AjwaE0WozfE": "Do THIS to Boost Your Metabolism, Lose Fat, & Feel Better Now With Dr. William Li.webm",
    "XhBp6GZzH6k": "How To Handle Difficult People & Take Back Your Peace and Power.mp4",
    "LB01v___wO4": "BTS\uff1a The ARIRANG Interview with Zane Lowe \uff5c Apple Music.mp4",
    "jV_RuCyRCjs": "Olivia Dean\uff1a On Recent Success, The Art of Loving, and Being Vulnerable \uff5c Zane Lowe Interview.mp4",
}


def _download_r2(youtube_id: str, output_dir: Path) -> Path | None:
    output_path = output_dir / f"{youtube_id}.mp4"
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("  Already exists: %s", output_path.name)
        return output_path

    r2_filename = R2_FILES.get(youtube_id)
    if not r2_filename:
        logger.warning("  No R2 mapping for %s — skipping", youtube_id)
        return None

    url = f"{R2_BASE}/{quote(r2_filename)}"
    is_webm = r2_filename.endswith(".webm")
    dl_path = output_dir / f"{youtube_id}{'.webm' if is_webm else '.mp4'}"

    try:
        logger.info("  Downloading from R2: %s", r2_filename)
        result = subprocess.run(
            ["curl", "-fSL", "-o", str(dl_path), url],
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            logger.warning("  curl failed: %s", result.stderr[:200])
            dl_path.unlink(missing_ok=True)
            return None

        if not dl_path.exists() or dl_path.stat().st_size == 0:
            logger.warning("  Empty download for %s", youtube_id)
            dl_path.unlink(missing_ok=True)
            return None

        if is_webm:
            logger.info("  Converting webm → mp4 (stream copy)...")
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(dl_path), "-c", "copy", str(output_path)],
                capture_output=True, text=True, timeout=300,
            )
            dl_path.unlink(missing_ok=True)
            if result.returncode != 0:
                logger.warning("  ffmpeg failed: %s", result.stderr[:200])
                output_path.unlink(missing_ok=True)
                return None

        size_mb = output_path.stat().st_size / 1e6
        logger.info("  Ready: %s (%.1f MB)", output_path.name, size_mb)
        return output_path

    except Exception as e:
        logger.warning("  Error: %s", e)
        dl_path.unlink(missing_ok=True)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Download video files")
    parser.add_argument("--full", action="store_true", help="Download all videos")
    parser.add_argument(
        "--r2", action="store_true",
        help="Download from Cloudflare R2 mirror instead of YouTube "
             "(use on cloud hosts where yt-dlp is blocked)",
    )
    args = parser.parse_args()

    if not VIDEOS_CSV.exists():
        logger.error("videos_metadata.csv not found at %s", VIDEOS_CSV)
        sys.exit(1)

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with open(VIDEOS_CSV) as f:
        youtube_ids = [r["video_id"].strip() for r in csv.DictReader(f) if r.get("video_id")]

    if not args.full:
        youtube_ids = [yt_id for yt_id in youtube_ids if yt_id in QUICK_YOUTUBE_IDS]

    source = "R2" if args.r2 else "YouTube"
    mode = "full" if args.full else "quick-start"
    logger.info("%s mode: downloading %d videos from %s", mode.capitalize(), len(youtube_ids), source)

    download_fn = _download_r2 if args.r2 else _download_youtube
    success, failed = 0, 0
    for i, yt_id in enumerate(youtube_ids, 1):
        logger.info("[%d/%d] %s", i, len(youtube_ids), yt_id)
        if download_fn(yt_id, DOWNLOAD_DIR):
            success += 1
        else:
            failed += 1

    logger.info("Done: %d downloaded, %d failed", success, failed)

    downloaded = list(DOWNLOAD_DIR.glob("*.mp4"))
    total_gb = sum(f.stat().st_size for f in downloaded) / 1e9
    logger.info("Video files in %s: %d (%.1f GB)", DOWNLOAD_DIR, len(downloaded), total_gb)


if __name__ == "__main__":
    main()
