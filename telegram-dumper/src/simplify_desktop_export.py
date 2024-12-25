import json
from argparse import ArgumentParser, BooleanOptionalAction
import os
from pathlib import Path

from lib import get_voice_message_transcription


def main(args):
    if not os.path.isfile(args.input_json_file):
        print('Input file not found')
        return

    input_dir = Path(args.input_json_file).parent

    with open(args.input_json_file, 'r') as fp:
        input_data = fp.read()

    input_json = json.loads(input_data)

    messages = input_json['messages']
    for message in messages:
        clean_message_fields(message)
        message["text"] = flat_text_array(message["text"])
        substitute_audio_transcript(message, input_dir)

        if args.skip_text_entities and "text_entities" in message:
            del message["text_entities"]

    with open(args.output_jsonl_file, 'w') as fp:
        for message in messages:
            line = json.dumps(message, ensure_ascii=False)
            fp.write(line + "\n")


def clean_message_fields(message: dict) -> None:
    fields_to_remove = {"date_unixtime", "edited_unixtime"}

    for field in fields_to_remove:
        if field in message:
            del message[field]


def flat_text_array(text_array: str | list[str | dict]) -> str:
    if isinstance(text_array, list):
        flat_result = []
        for piece in text_array:
            if isinstance(piece, dict) and "text" in piece:
                flat_result.append(piece["text"])
            else:
                flat_result.append(piece)

        return "".join(flat_result)

    return text_array


def substitute_audio_transcript(message: dict, input_dir) -> None:
    if "media_type" not in message or message["media_type"] != "voice_message":
        return

    audio_path = Path(input_dir) / message["file"]
    transcription = get_voice_message_transcription(audio_path)

    if not transcription:
        return

    message["text_entities"] = [{
        "type": "plain",
        "text": transcription,
    }]
    message["text"] = flat_text_array(message["text_entities"])


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert Telegram Desktop export-JSON to a simple JSON format file.")
    parser.add_argument(
        "input_json_file",
        help="input JSON file of Telegram Desktop export",
    )
    parser.add_argument(
        "output_jsonl_file",
        help="output JSONL file of text messages",
    )
    parser.add_argument(
        "--skip-text-entities",
        help="don't add `text_entities` field to output",
        default=False,
        action=BooleanOptionalAction,
    )

    args = parser.parse_args()

    main(args)
