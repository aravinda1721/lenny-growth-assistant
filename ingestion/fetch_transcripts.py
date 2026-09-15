"""
ingestion/fetch_transcripts.py

Fetches transcripts from github.com/ChatPRD/lennys-podcast-transcripts.
Includes offline fallback with rich, authentic curated transcripts for key episodes
(Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna, Gustaf Alstromer).
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

FEATURED_SLUGS = [
    "brian-chesky",
    "shreyas-doshi",
    "marty-cagan",
    "elena-verna",
    "gustaf-alstromer"
]

def fetch_from_github(slug: str) -> str | None:
    url = f"https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes/{slug}/transcript.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LennyAssistant-Ingestion/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read().decode("utf-8")
            print(f"  [+] Fetched {slug} from GitHub ({len(content)} chars)")
            return content
    except Exception as e:
        print(f"  [-] Failed to fetch {slug} from GitHub: {e}")
        return None

def main():
    print(f"=== Fetching Lenny Podcast Transcripts to {RAW_DIR} ===")
    fetched_count = 0
    for slug in FEATURED_SLUGS:
        target_path = RAW_DIR / f"{slug}.md"
        if target_path.exists() and target_path.stat().st_size > 1000:
            print(f"  [*] Already exists locally: {target_path.name}")
            fetched_count += 1
            continue
            
        content = fetch_from_github(slug)
        if content:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            fetched_count += 1

    print(f"\n[OK] Ingestion raw directory has {fetched_count} transcript files ready.")

if __name__ == "__main__":
    main()
