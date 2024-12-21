import asyncio
from argparse import ArgumentParser
from datetime import datetime, timedelta
import logging
from os import getenv
from pathlib import Path

from telethon import TelegramClient
from telethon.hints import Entity
from telethon.tl.patched import Message

logging.basicConfig(format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.INFO)

API_ID = int(getenv("TELEGRAM_API_ID"))
API_HASH = getenv("TELEGRAM_API_HASH")


async def main(args):
    offset_date = None
    if args.from_date:
        from_date = datetime.fromisoformat(args.from_date)
        offset_date = from_date - timedelta(seconds=1)

    output_dir = Path(args.output_dir)
    audio_files_dir = output_dir / 'audio_files'

    session_path = "../sessions/anon"
    async with TelegramClient(session_path, API_ID, API_HASH) as client:
        entity_info = await client.get_entity(args.chat_name)
        save_entity_info(entity_info, output_dir)

        messages = await client.get_messages(
            entity=args.chat_name,
            reverse=True,
            offset_date=offset_date,
        )
        print(f"Totally {len(messages)} messages fetched")

        messages_with_audio = find_messages_with_audio(messages)

        for file_name, message in messages_with_audio:
            file_path = audio_files_dir / file_name

            if file_path.exists():
                continue

            print(f"Downloading {file_name=}...")
            await message.download_media(file_path, progress_callback=create_download_progress())


def save_entity_info(entity_info: Entity, output_dir: Path) -> None:
    file_name = f"entity_{entity_info.id}.json"
    with open(output_dir / file_name, "w") as fp:
        entity_info.to_json(fp, ensure_ascii=False, indent=2)


def find_messages_with_audio(messages: list[Message]) -> list[tuple[str, Message]]:
    result = []

    for message in messages:
        if message.document is None or message.document.mime_type != "audio/ogg":
            continue

        file_name = f"{message_peer_to_string_id(message)}_msg_{message.id}.oga"

        result.append((file_name, message,))

    return result


def message_peer_to_string_id(message: Message) -> str | None:
    if hasattr(message.peer_id, "channel_id"):
        return f"channel_{message.peer_id.channel_id}"
    if hasattr(message.peer_id, "chat_id"):
        return f"chat_{message.peer_id.chat_id}"
    if hasattr(message.peer_id, "user_id"):
        return f"user_{message.peer_id.user_id}"

    return None


def create_download_progress(notice_step: float = .1):
    prev_notice: float | None = None

    def func(current: int, total: int):
        nonlocal prev_notice

        percent = current / total

        if prev_notice is None or percent - prev_notice >= notice_step:
            print(f'Downloaded {current} out of {total} bytes: {percent:.2%}')
            prev_notice = percent

    return func


if __name__ == "__main__":
    parser = ArgumentParser(description="Export messages from a Telegram channel, with audio.")
    parser.add_argument(
        "chat_name",
        help="channel name to extract messages from",
    )
    parser.add_argument(
        "output_dir",
        help="directory to dump results",
    )
    parser.add_argument(
        "--from_date",
        help="export messages from this date only (including)",
    )

    args = parser.parse_args()

    asyncio.run(main(args))
