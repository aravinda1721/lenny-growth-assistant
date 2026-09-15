"""
ingestion/chunk.py

Parses Lenny Podcast markdown transcripts, extracting YAML frontmatter,
speaker turns, timestamps, and calculates exact YouTube jump-links.
Produces rich, structured JSON chunks ready for embedding and retrieval.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

RAW_DIR = Path(__file__).parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SPEAKER_TURN_REGEX = re.compile(r"^([A-Za-z\s\.\'\-]+?)\s*\(((\d{1,2}:)?\d{2}:\d{2})\):\s*(.*)$", re.MULTILINE)

def parse_time_to_seconds(time_str: str) -> int:
    parts = [int(p) for p in time_str.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0

def parse_frontmatter(content: str) -> tuple[dict, str]:
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.splitlines():
                if ":" in line and not line.strip().startswith("-"):
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip().strip("'\"")
    return metadata, body

def chunk_transcript(file_path: Path) -> List[Dict[str, Any]]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    metadata, body = parse_frontmatter(content)
    episode_slug = file_path.stem
    guest = metadata.get("guest", episode_slug.replace("-", " ").title())
    title = metadata.get("title", f"Lenny's Podcast with {guest}")
    video_id = metadata.get("video_id", "")
    base_youtube = metadata.get("youtube_url", f"https://www.youtube.com/watch?v={video_id}" if video_id else "")

    # Find all speaker turns
    matches = list(SPEAKER_TURN_REGEX.finditer(body))
    turns = []
    
    if matches:
        for i, match in enumerate(matches):
            speaker = match.group(1).strip()
            time_str = match.group(2).strip()
            # Turn text is from end of match header to start of next match (or end of text)
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            turn_text = (match.group(4) + " " + body[start_pos:end_pos]).strip()
            turn_text = re.sub(r"\s+", " ", turn_text)
            
            if turn_text:
                turns.append({
                    "speaker": speaker,
                    "timestamp": time_str,
                    "seconds": parse_time_to_seconds(time_str),
                    "text": turn_text
                })
    else:
        # Fallback to paragraph splitting if speaker regex didn't match
        paragraphs = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 60]
        for i, p in enumerate(paragraphs):
            turns.append({
                "speaker": guest,
                "timestamp": "00:00:00",
                "seconds": 0,
                "text": p
            })

    # Group turns into cohesive chunks (~600 - 1200 characters)
    chunks = []
    chunk_index = 0
    current_turns = []
    current_len = 0

    for turn in turns:
        current_turns.append(turn)
        current_len += len(turn["text"])

        if current_len >= 800:
            first_turn = current_turns[0]
            speaker_summary = ", ".join(list(dict.fromkeys(t["speaker"] for t in current_turns)))
            chunk_body = "\n".join(f"{t['speaker']} ({t['timestamp']}): {t['text']}" for t in current_turns)
            
            # Generate YouTube timestamp URL
            yt_link = f"https://youtu.be/{video_id}?t={first_turn['seconds']}" if video_id else base_youtube
            
            content_hash = hashlib.sha256(chunk_body.encode("utf-8")).hexdigest()
            chunk_id = f"{episode_slug}_{chunk_index:04d}"

            chunks.append({
                "id": chunk_id,
                "source_file": file_path.name,
                "episode_slug": episode_slug,
                "episode_title": title,
                "guest": guest,
                "timestamp": first_turn["timestamp"],
                "timestamp_seconds": first_turn["seconds"],
                "youtube_url": yt_link,
                "speaker": speaker_summary,
                "chunk_index": chunk_index,
                "text": chunk_body,
                "content_hash": content_hash,
                "char_count": len(chunk_body)
            })

            chunk_index += 1
            # Keep last turn for smooth context overlap
            current_turns = [current_turns[-1]]
            current_len = len(current_turns[0]["text"])

    # Flush remaining turns
    if current_turns:
        first_turn = current_turns[0]
        speaker_summary = ", ".join(list(dict.fromkeys(t["speaker"] for t in current_turns)))
        chunk_body = "\n".join(f"{t['speaker']} ({t['timestamp']}): {t['text']}" for t in current_turns)
        yt_link = f"https://youtu.be/{video_id}?t={first_turn['seconds']}" if video_id else base_youtube
        content_hash = hashlib.sha256(chunk_body.encode("utf-8")).hexdigest()
        chunk_id = f"{episode_slug}_{chunk_index:04d}"

        chunks.append({
            "id": chunk_id,
            "source_file": file_path.name,
            "episode_slug": episode_slug,
            "episode_title": title,
            "guest": guest,
            "timestamp": first_turn["timestamp"],
            "timestamp_seconds": first_turn["seconds"],
            "youtube_url": yt_link,
            "speaker": speaker_summary,
            "chunk_index": chunk_index,
            "text": chunk_body,
            "content_hash": content_hash,
            "char_count": len(chunk_body)
        })

    return chunks

def main():
    print("=== Chunking Transcripts ===")
    total_chunks = 0
    all_chunks = []
    
    raw_files = list(RAW_DIR.glob("*.md"))
    print(f"Found {len(raw_files)} raw transcript files.")

    for rf in raw_files:
        chunks = chunk_transcript(rf)
        all_chunks.extend(chunks)
        total_chunks += len(chunks)
        print(f"  [+] {rf.name} -> {len(chunks)} chunks")

    output_file = PROCESSED_DIR / "chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Processed {total_chunks} chunks written to {output_file}")

if __name__ == "__main__":
    main()
