import json
from argparse import ArgumentParser, BooleanOptionalAction
import os
from pathlib import Path

from lib import (
    compose_voice_message_file_name,
    filter_dict,
    get_voice_message_transcription,
    read_jsonl_with_messages,
)


def main(args):
    if not os.path.isfile(args.input_jsonl_file):
        print('Input JSONL file not found')
        return

    input_dir = Path(args.input_jsonl_file).parent

    input_data = read_jsonl_with_messages(args.input_jsonl_file)

    for message in input_data.values():
        process_message(message, input_dir, args)

        for reply in message.get('reply_messages', []):
            process_message(reply, input_dir, args)

    with open(args.output_jsonl_file, 'w') as fp:
        for message in input_data.values():
            line = json.dumps(message, ensure_ascii=False)
            fp.write(line + "\n")


def process_message(message: dict, input_dir: Path, args) -> None:
    clean_message_fields(message)
    process_reply_to(message)
    process_reactions(message)
    process_standard_replies(message)

    process_media(message, input_dir)

    process_peer_ref(message, "from_id")
    process_peer_ref(message, "peer_id")

    if args.remove_media:
        filter_dict(message, {"media"})
    if args.remove_reply_messages:
        filter_dict(message, {"reply_messages"})


def clean_message_fields(message: dict) -> None:
    filter_dict(message, {
        "_",
        "out",
        "mentioned",
        "media_unread",
        "silent",
        "post",
        "from_scheduled",
        "legacy",
        "edit_hide",
        "pinned",
        "noforwards",
        "invert_media",
        "offline",
        "video_processing_pending",
        "from_boosts_applied",
        "saved_peer_id",
        "via_bot_id",
        "via_business_bot_id",
        "reply_markup",
        "entities",
        "edit_date",
        "grouped_id",
        "restriction_reason",
        "ttl_period",
        "quick_reply_shortcut_id",
        "effect",
        "factcheck",
    })


def process_reply_to(message: dict) -> None:
    if "reply_to" not in message or message["reply_to"] is None:
        return

    message["reply_to"] = message["reply_to"]["reply_to_msg_id"]


def process_peer_ref(message: dict, field: str) -> None:
    if field not in message or not message[field]:
        return

    if message[field]["_"] == 'PeerUser':
        message[field] = message[field]["user_id"]
    elif message[field]["_"] == 'PeerChannel':
        message[field] = message[field]["channel_id"]
    else:
        raise ValueError(f"Unknown peer type: {message[field]['_']}")


def process_reactions(message: dict) -> None:
    if "reactions" not in message or message["reactions"] is None:
        return

    result = {}
    for reaction_model in message["reactions"]["results"]:
        if reaction_model["reaction"]["_"] == "ReactionEmoji":
            result[reaction_model["reaction"]["emoticon"]] = reaction_model["count"]
        elif reaction_model["reaction"]["_"] == "ReactionCustomEmoji":
            result[reaction_model["reaction"]["document_id"]] = reaction_model["count"]

    message["reactions"] = result


def process_standard_replies(message: dict) -> None:
    if "replies" not in message or not message["replies"]:
        return

    message["replies"] = message["replies"]["replies"]


def process_media(message: dict, input_dir: Path) -> None:
    if "media" not in message or not message["media"] or message["media"]["_"] != "MessageMediaDocument":
        return

    media = message["media"]
    filter_dict(media, {"_", "alt_documents", "nopremium", "round", "spoiler", "ttl_seconds"})

    process_document(media)

    if media.get("voice", False):
        substitute_voice_transcript(message, input_dir / "audio_files")


def process_document(media: dict) -> None:
    if "document" not in media or not media["document"]:
        return

    filter_dict(media["document"], {"_", "access_hash", "dc_id", "file_reference", "thumbs", "video_thumbs"})

    for attr in media["document"]["attributes"]:
        if attr["_"] == "DocumentAttributeAudio":
            filter_dict(attr, {"_", "waveform"})


def substitute_voice_transcript(message: dict, input_dir: Path) -> None:
    file_name = compose_voice_message_file_name(message)

    audio_path = input_dir / file_name
    transcription = get_voice_message_transcription(audio_path)

    if not transcription:
        return

    message["message"] = transcription


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert messages JSONL dump to a simple JSON format file.")
    parser.add_argument(
        "input_jsonl_file",
        help="input JSONL file with messages",
    )
    parser.add_argument(
        "output_jsonl_file",
        help="output JSONL file of text messages",
    )
    parser.add_argument(
        "--remove-media",
        help="don't add data of media field to output",
        action=BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--remove-reply-messages",
        help="don't add data of reply_messages field to output",
        action=BooleanOptionalAction,
        default=False,
    )

    args = parser.parse_args()

    main(args)
