#!/usr/bin/env python3
"""
Run this once to list all your Telegram chats/groups.
Copy the exact name of your stock group, then paste it into .env as TELEGRAM_GROUP.
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE = os.getenv("TELEGRAM_PHONE", "")


async def list_chats():
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("\nYour Telegram groups and channels:\n")
    print(f"{'ID':<15} {'Type':<10} Name")
    print("-" * 60)
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, (Chat, Channel)):
            kind = "Channel" if isinstance(dialog.entity, Channel) else "Group"
            print(f"{dialog.id:<15} {kind:<10} {dialog.name}")
    await client.disconnect()
    print("\nCopy the exact Name into your .env as TELEGRAM_GROUP=<name>")


if __name__ == "__main__":
    asyncio.run(list_chats())
