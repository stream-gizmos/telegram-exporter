from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
import subprocess
from tempfile import NamedTemporaryFile

import librosa


def main(args):
    model, processor = prepare_stt_model(args.model_size)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"Prepared: model_size={args.model_size} {device=}")

    for file_path in args.audio_files:
        file_path = Path(file_path)
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
            if "array is too big" not in str(e):
                raise

            print("Cannot read the file! Trying to convert it to WAV by ffmpeg...")
            with convert_to_temporary_wav_file(
                    str(file_path),
                    processor.feature_extractor.sampling_rate
            ) as temp_file_path:
                data, samplerate = librosa.load(
                    str(temp_file_path),
                    sr=processor.feature_extractor.sampling_rate,
                )

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


@contextmanager
def convert_to_temporary_wav_file(input_audio_file: str, sampling_rate: int):
    temp_file = NamedTemporaryFile(suffix=".wav").name

    try:
        cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", input_audio_file, "-ar", str(sampling_rate), "-y", temp_file]
        return_code = subprocess.call(cmd)

        if return_code != 0:
            raise RuntimeError(f"ffmpeg failed with return code {return_code}")

        yield temp_file
    finally:
        import os
        os.remove(temp_file)


if __name__ == "__main__":
    parser = ArgumentParser(description="Transcribe audio files to text by the Whisper Model.")
    parser.add_argument(
        "--model-size",
        help="model size (check Whisper model variants on Hugging Face)",
        default="large-v3-turbo",
    )
    parser.add_argument(
        "audio_files",
        nargs="+",
        help="path to audio files with mask (like ../data/*.ogg)",
    )

    args = parser.parse_args()

    import torch
    from transformers import WhisperProcessor, WhisperForConditionalGeneration

    main(args)
