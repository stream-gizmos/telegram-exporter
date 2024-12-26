import asyncio
import json
from argparse import ArgumentParser, BooleanOptionalAction
from datetime import datetime, timedelta
import logging
from os import getenv
from pathlib import Path

from telethon import TelegramClient
from telethon.hints import Entity
from telethon.tl.patched import Message

from lib import (
    compose_voice_message_file_name,
    data_get,
    read_jsonl_with_messages,
    save_jsonl_with_messages,
)

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

        output_path = compose_entity_messages_path(entity_info, output_dir)
        print(f"Use '{output_path}' file as output")

        old_messages = read_jsonl_with_messages(output_path) \
            if args.preserve_old_data else {}

        messages: list[Message] = await client.get_messages(
            entity=entity_info,
            reverse=True,
            offset_date=offset_date,
        )
        print(f"Total {len(messages)} messages fetched")

        messages_replies = await fetch_replies(client, entity_info, messages, old_messages) \
            if args.fetch_replies else {}

        messages_data = []
        for message in messages:
            message_data = json.loads(message.to_json())

            if message.id in messages_replies:
                message_data["reply_messages"] = [
                    json.loads(reply.to_json())
                    for reply in messages_replies[message.id]
                ]

            messages_data.append(message_data)

        messages_data = merge_messages_with_old(messages_data, old_messages, args.fetch_replies)
        save_jsonl_with_messages(output_path, messages_data)

        if args.fetch_voice_messages:
            flat_replies = [reply for replies in messages_replies.values() for reply in replies]
            audio_messages = find_audio_messages(messages) + find_audio_messages(flat_replies)
            await download_audio_messages(audio_messages, audio_files_dir)


async def fetch_replies(
        client,
        entity_info: Entity,
        current_messages: list[Message],
        old_messages: dict[int, dict],
) -> dict[int, list[Message]]:
    all_replies = []

    messages_with_replies = len(list(filter(None, [is_message_have_replies(message) for message in current_messages])))
    print(f"Total {messages_with_replies} messages with replies to fetch")

    result: dict[int, list[Message]] = {}
    process_counter = 0
    for message in current_messages:
        old_message = old_messages.get(message.id)
        is_fetch_required = is_replies_fetch_required(message, old_message)

        if is_fetch_required:
            replies: list[Message] = await client.get_messages(entity=entity_info, reply_to=message.id, reverse=True)
            all_replies.extend(replies)
            result[message.id] = replies

            process_counter += 1
            if process_counter % max(int(messages_with_replies * .05), 5) == 0:
                print(f"Fetched replies to {process_counter}/{messages_with_replies} of messages")
                await asyncio.sleep(1)

    return result


def is_message_have_replies(message: dict | Message) -> bool:
    if not isinstance(message, dict):
        message = message.to_dict()

    replies_count = data_get(message, 'replies.replies')
    replies_count = int(replies_count) if replies_count else 0

    return replies_count > 0


def is_replies_fetch_required(current_message: Message, old_message: dict | None) -> bool:
    if not is_message_have_replies(current_message):
        return False

    old_channel_id = data_get(old_message, "replies.channel_id")
    old_max_id = data_get(old_message, "replies.max_id")
    old_count = data_get(old_message, "replies.replies")

    return old_channel_id != current_message.replies.channel_id \
        or old_max_id != current_message.replies.max_id \
        or old_count != current_message.replies.replies \
        or len(old_message.get("reply_messages", [])) != current_message.replies.replies


def save_entity_info(entity_info: Entity, output_dir: Path) -> None:
    file_name = f"entity_{entity_info.id}.json"
    with open(output_dir / file_name, "w") as fp:
        entity_info.to_json(fp, ensure_ascii=False, indent=2)


def merge_messages_with_old(
        messages_data: list[dict],
        old_messages: dict[int, dict],
        fetch_replies_mode: bool,
) -> list[dict]:
    result = old_messages.copy()

    for fresh_message in messages_data:
        message_id = fresh_message["id"]

        if message_id not in result:
            result[message_id] = fresh_message
            continue

        are_actual_replies_known = "reply_messages" in fresh_message or not is_message_have_replies(fresh_message)
        if not fetch_replies_mode or not are_actual_replies_known:
            old_replies = result[message_id].get("reply_messages", [])
            fresh_message["reply_messages"] = old_replies

        if "reply_messages" in fresh_message and len(fresh_message["reply_messages"]) == 0:
            del fresh_message["reply_messages"]

        result[message_id] = fresh_message

    return sorted(result.values(), key=lambda m: m["id"])


def compose_entity_messages_path(entity_info: Entity, output_dir: Path) -> Path:
    return output_dir / f"entity_{entity_info.id}_messages.jsonl"


def find_audio_messages(messages: list[Message]) -> list[tuple[str, Message]]:
    result = []

    for message in messages:
        if message.document is None or message.document.mime_type != "audio/ogg":
            continue

        file_name = compose_voice_message_file_name(message)
        result.append((file_name, message,))

    return result


async def download_audio_messages(audio_messages, audio_files_dir: Path) -> None:
    print(f"Total {len(audio_messages)} voice messages to download")

    for file_name, message in audio_messages:
        file_path = audio_files_dir / file_name

        if file_path.exists():
            continue

        print(f"Downloading {file_name=}...")
        await message.download_media(file_path, progress_callback=create_download_progress())


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
    parser = ArgumentParser(description="Export messages from a Telegram channel, with replies and audio.")
    parser.add_argument(
        "chat_name",
        help="channel name to extract messages from",
    )
    parser.add_argument(
        "output_dir",
        help="directory to dump results",
    )
    parser.add_argument(
        "--preserve-old-data",
        help="merge new data with old data or fully override it",
        action=BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--fetch-replies",
        help="add data about replies to posts in channels",
        action=BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--fetch-voice-messages",
        help="download voice message files",
        action=BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--from-date",
        help="export messages from this date only (including)",
    )

    args = parser.parse_args()

    asyncio.run(main(args))
