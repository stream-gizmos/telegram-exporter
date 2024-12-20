from pathlib import Path

import librosa
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration


# TODO Move model_size to arguments
def main():
    # model_size = "medium"
    # model_size = "large-v2"
    model_size = "large-v3-turbo"
    model, processor = prepare_stt_model(model_size)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Prepared: {model_size=} {device=}")

    for file_path in Path.cwd().iterdir():
        if not file_path.match("*.ogg"):
            continue

        output_file_name = file_path.with_suffix(".txt")

        if output_file_name.exists():
            continue

        print(f"Processing {file_path.name}...")
        try:
            data, samplerate = librosa.load(
                str(file_path),
                sr=processor.feature_extractor.sampling_rate,
            )
        except ValueError as e:
            if "array is too big" in str(e):
                print("File is too big! Skipping.")
                continue
            else:
                raise

        inputs = processor(
            data,
            return_tensors="pt",
            truncation=False,
            # padding="longest",
            return_attention_mask=True,
            sampling_rate=samplerate,
        )
        inputs = inputs.to(device, torch.float32)

        text = extract_text_from_features(model, processor, inputs)
        print(f"{text=}")

        with open(output_file_name, "w") as fp:
            fp.writelines(f"{text}\n")

    print("Done")


def prepare_stt_model(model_size: str) -> tuple:
    processor = WhisperProcessor.from_pretrained(f"openai/whisper-{model_size}")
    model = WhisperForConditionalGeneration.from_pretrained(f"openai/whisper-{model_size}")
    model.config.forced_decoder_ids = None

    return model, processor


def extract_text_from_features(model, processor, inputs: dict) -> str:
    # generate token ids
    predicted_ids = model.generate(
        **inputs,
        return_timestamps=True,
    )
    # decode token ids to text
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)

    return " ".join(transcription).strip()


if __name__ == "__main__":
    main()
