#!/usr/bin/env python3
"""
Telegram stock chart fetcher + analyzer.
Downloads images from a Telegram group and generates Claude-powered chart analysis.
"""

import asyncio
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")
GROUP = os.getenv("TELEGRAM_GROUP", "")
FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", "200"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))

ANALYSIS_PROMPT = """\
You are a technical analyst reviewing a stock chart screenshot shared in a trading group.

Analyze this chart and provide:
1. **Ticker / Instrument** — if visible on the chart
2. **Timeframe** — candle interval shown (1m, 5m, 1h, daily, etc.)
3. **Trend** — bullish / bearish / sideways, with brief reasoning
4. **Key Levels** — notable support and resistance prices visible
5. **Chart Pattern** — any recognizable pattern (breakout, consolidation, flag, wedge, H&S, etc.)
6. **Indicators** — any visible indicators (MA, RSI, MACD, volume, Bollinger Bands, etc.) and what they suggest
7. **Summary** — one or two sentence overall take on what this chart is showing

Be concise and specific. If something is not visible or unclear, say so rather than guessing.\
"""


def get_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def analyze_chart(image_path: Path, caption: str, ac: anthropic.Anthropic) -> str:
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode()
    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": get_media_type(image_path),
                "data": image_data,
            },
        },
        {"type": "text", "text": ANALYSIS_PROMPT},
    ]
    if caption:
        content.append({"type": "text", "text": f"\nOriginal caption from the group: {caption}"})

    response = ac.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": content}],
    )
    return response.content[0].text


def save_analysis(image_path: Path, message_date: datetime, caption: str, analysis: str):
    md_path = image_path.with_suffix(".md")
    lines = [
        "# Chart Analysis\n",
        f"**Date:** {message_date.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Image:** {image_path.name}  ",
    ]
    if caption:
        lines.append(f"**Caption:** {caption}  ")
    lines += ["\n---\n", analysis, ""]
    md_path.write_text("\n".join(lines))
    return md_path


async def fetch(limit: int = FETCH_LIMIT):
    if not all([API_ID, API_HASH, PHONE, GROUP]):
        sys.exit(
            "Missing config. Copy .env.example to .env and fill in your credentials."
        )

    ac = anthropic.Anthropic()
    client = TelegramClient("session", API_ID, API_HASH)

    await client.start(phone=PHONE)
    print(f"Connected. Fetching up to {limit} messages from {GROUP} ...\n")

    try:
        entity = await client.get_entity(GROUP)
    except Exception as e:
        sys.exit(f"Could not find group '{GROUP}': {e}")

    downloaded = 0
    analyzed = 0

    async for msg in client.iter_messages(entity, limit=limit):
        if not msg.media:
            continue

        is_photo = isinstance(msg.media, MessageMediaPhoto)
        is_image_doc = (
            isinstance(msg.media, MessageMediaDocument)
            and hasattr(msg.media.document, "mime_type")
            and msg.media.document.mime_type.startswith("image/")
        )

        if not (is_photo or is_image_doc):
            continue

        date_folder = OUTPUT_DIR / msg.date.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        timestamp = msg.date.strftime("%H%M%S")
        base_name = f"{timestamp}_{msg.id}"
        dest = date_folder / base_name

        # Skip if this message ID already has an image + analysis
        existing_any = list(date_folder.glob(f"*_{msg.id}.*"))
        existing_images = [f for f in existing_any if f.suffix.lower() != ".md"]
        existing_md = [f for f in existing_any if f.suffix.lower() == ".md"]
        if existing_images and existing_md:
            print(f"[skip] {base_name} already done")
            analyzed += 1
            downloaded += 1
            continue

        image_path = Path(await client.download_media(msg, file=str(dest)))

        downloaded += 1
        caption = (msg.message or "").strip()
        print(f"[{downloaded}] {image_path.relative_to(OUTPUT_DIR)}", end="")
        if caption:
            print(f"  — \"{caption[:60]}{'...' if len(caption)>60 else ''}\"", end="")
        print()

        try:
            analysis = analyze_chart(image_path, caption, ac)
            md_path = save_analysis(image_path, msg.date, caption, analysis)
            print(f"     Analysis → {md_path.name}")
            analyzed += 1
        except Exception as e:
            print(f"     Analysis failed: {e}")

    await client.disconnect()
    print(f"\nDone. {downloaded} images downloaded, {analyzed} analyzed.")
    print(f"Output folder: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(fetch())
