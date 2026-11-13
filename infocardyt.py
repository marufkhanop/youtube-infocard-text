#!/usr/bin/env python3
"""
YouTube Info Cards Extractor (fixed version)
Works on Termux / systems without tkinter.
"""

import re
import json
import sys
from urllib.parse import urlparse, parse_qs
import requests

# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    url = url.strip()
    if not url:
        return None
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0].split("/")[0][:11]
    parsed = urlparse(url)
    if parsed.hostname and ("youtube.com" in parsed.hostname or "youtube-nocookie.com" in parsed.hostname):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0][:11]
        path = parsed.path.strip("/")
        for part in path.split("/"):
            if len(part) == 11 and part.isalnum():
                return part
    return None


def extract_json_object(text: str, marker: str) -> str | None:
    """Properly extract a balanced JSON object that starts after the marker."""
    start = text.find(marker)
    if start == -1:
        return None
    start = text.find("{", start)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\" and in_string:
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def get_page_data(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    text = resp.text

    # Prefer ytInitialData (this is where cards usually live)
    raw = extract_json_object(text, "ytInitialData")
    if not raw:
        raise RuntimeError("Could not find ytInitialData")
    return json.loads(raw)


def get_title_and_channel(data: dict) -> tuple[str, str]:
    title = "N/A"
    channel = "N/A"
    try:
        contents = (
            data.get("contents", {})
            .get("twoColumnWatchNextResults", {})
            .get("results", {})
            .get("results", {})
            .get("contents", [])
        )
        for block in contents:
            if "videoPrimaryInfoRenderer" in block:
                t = block["videoPrimaryInfoRenderer"].get("title", {})
                if "runs" in t:
                    title = "".join(r.get("text", "") for r in t["runs"])
                elif "simpleText" in t:
                    title = t["simpleText"]
            if "videoSecondaryInfoRenderer" in block:
                owner = (
                    block["videoSecondaryInfoRenderer"]
                    .get("owner", {})
                    .get("videoOwnerRenderer", {})
                )
                ch = owner.get("title", {})
                if "runs" in ch:
                    channel = "".join(r.get("text", "") for r in ch["runs"])
                elif "simpleText" in ch:
                    channel = ch["simpleText"]
    except Exception:
        pass
    return title, channel


def extract_cards(data: dict) -> list[dict]:
    """Return a clean list of info cards with timing + teaser text."""
    results = []
    cards = (
        data.get("cards", {})
        .get("cardCollectionRenderer", {})
        .get("cards", [])
    )
    for card_wrapper in cards:
        card = card_wrapper.get("cardRenderer", {})
        teaser = (
            card.get("teaser", {})
            .get("simpleCardTeaserRenderer", {})
            .get("message", {})
            .get("simpleText", "")
        )
        cues = card.get("cueRanges", [])
        start_s = end_s = None
        if cues:
            start_s = int(cues[0].get("startCardActiveMs", 0)) // 1000
            end_ms = int(cues[0].get("endCardActiveMs", 0))
            end_s = end_ms // 1000 if end_ms else None

        results.append({
            "teaser": teaser,
            "start": start_s,
            "end": end_s,
        })
    return results


# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────

def main():
    print("YouTube Info Cards Extractor")
    print("-" * 40)

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Paste YouTube URL: ").strip()

    if not url:
        print("No URL provided.")
        return

    video_id = extract_video_id(url)
    if not video_id:
        print("Could not extract a valid video ID.")
        return

    print(f"\nFetching data for: {video_id} ...\n")

    try:
        data = get_page_data(video_id)
        title, channel = get_title_and_channel(data)
        cards = extract_cards(data)

        print(f"Title  : {title}")
        print(f"Channel: {channel}")
        print(f"ID     : {video_id}")
        print()

        if not cards:
            print("No info cards found on this video.")
        else:
            print(f"Found {len(cards)} info card(s):\n")
            for i, c in enumerate(cards, 1):
                timing = f"@ {c['start']}s" if c["start"] is not None else ""
                if c["end"]:
                    timing += f" → {c['end']}s"
                print(f"  Card #{i}  {timing}")
                print(f"     → {c['teaser']}")
                print()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()