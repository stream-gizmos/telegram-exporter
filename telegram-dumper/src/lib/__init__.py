import json
from pathlib import Path


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
