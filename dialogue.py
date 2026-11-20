import json
import wave
import tempfile
import numpy as np

from pathlib import Path
from faster_whisper.audio import decode_audio

from diarization import (
    diarize_audio,
    merge_segments
)

from transcription_kk import transcribe_audio

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_RATE = 16000


def transcribe_dialogue(audio_path):

    print("Сөйлеушілер анықталуда...")

    segments = merge_segments(
        diarize_audio(audio_path)
    )

    audio = decode_audio(
        str(audio_path),
        sampling_rate=SAMPLE_RATE
    )

    dialogue = []

    with tempfile.TemporaryDirectory() as temp:

        for i, segment in enumerate(segments):

            start = int(segment["start"] * SAMPLE_RATE)
            end = int(segment["end"] * SAMPLE_RATE)

            chunk = audio[start:end]

            if len(chunk) == 0:
                continue

            segment_path = Path(temp) / f"part_{i}.wav"

            pcm = (
                np.clip(chunk, -1, 1) * 32767
            ).astype("<i2")

            with wave.open(str(segment_path), "wb") as f:

                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(SAMPLE_RATE)
                f.writeframes(pcm.tobytes())

            print(
                f"{segment['speaker']} өңделуде..."
            )

            result = transcribe_audio(segment_path)

            dialogue.append({
                "speaker": segment["speaker"],
                "start": segment["start"],
                "end": segment["end"],
                "text": result["text"]
            })

    return dialogue


if __name__ == "__main__":

    result = transcribe_dialogue(
        BASE_DIR / "test.m4a"
    )

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=4
    ))

    print("\nБӨЛІНГЕН ДИАЛОГ:\n")

    for item in result:

        print(
            f"{item['speaker']}: {item['text']}"
        )