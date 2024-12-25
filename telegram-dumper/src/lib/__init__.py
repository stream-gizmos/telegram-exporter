import json
from pathlib import Path

from telethon.tl.patched import Message


def read_jsonl_with_messages(file_path: str | Path) -> dict[int, dict]:
    result = {}
    try:
        with open(file_path, "r") as fp:
            for line in fp.readlines():
                record = json.loads(line)
                result[record["id"]] = record
    except FileNotFoundError:
        pass

    return result


def save_jsonl_with_messages(file_path: str | Path, messages: dict[int, dict] | list[dict]) -> None:
    if isinstance(messages, dict):
        messages = messages.values()

    with open(file_path, "w") as fp:
        for message in messages:
            line = json.dumps(message, ensure_ascii=False)
            fp.write(line + "\n")


def data_get(d: dict, path: str) -> any:
    path_list = path.split(".")

    result = d
    for path in path_list:
        if result is None or not isinstance(result, dict):
            return None

        result = result.get(path)

    return result


def filter_dict(d: dict, fields_to_remove: set | list) -> None:
    for field in fields_to_remove:
        if field in d:
            del d[field]

    for field in list(d.keys()):
        if d[field] is None:
            del d[field]


def compose_voice_message_file_name(message: Message | dict) -> str:
    if not isinstance(message, dict):
        message = message.to_dict()

    return f"{_message_peer_to_string_id(message)}_msg_{message['id']}.oga"


def _message_peer_to_string_id(message: dict) -> str | None:
    if "channel_id" in message["peer_id"]:
        return f"channel_{message['peer_id']['channel_id']}"
    if "chat_id" in message["peer_id"]:
        return f"chat_{message['peer_id']['chat_id']}"
    if "user_id" in message["peer_id"]:
        return f"user_{message['peer_id']['user_id']}"

    return None


def get_voice_message_transcription(audio_path: Path) -> str | None:
    transcript_path = audio_path.with_suffix(".txt")

    if not audio_path.exists() or not transcript_path.exists():
        return

    with open(transcript_path, 'r') as fp:
        transcription = fp.read()

    transcription = transcription.strip()

    if len(transcription) == 0:
        return

    return transcription
