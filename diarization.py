import torch
import numpy as np
import json
from speechbrain.utils.fetching import LocalStrategy
from pathlib import Path
from faster_whisper.audio import decode_audio
from speechbrain.inference.speaker import EncoderClassifier
from sklearn.cluster import AgglomerativeClustering

BASE_DIR = Path(__file__).resolve().parent

SAMPLE_RATE = 16000
WINDOW_SECONDS = 2
STEP_SECONDS = 1

print("Сөйлеушілерді ажырату моделі жүктелуде...")

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir=str(BASE_DIR / "models" / "speaker-model"),
    run_opts={"device": "cpu"},
    local_strategy=LocalStrategy.COPY
)

print("Speaker моделі дайын!")


def diarize_audio(audio_path):

    audio = decode_audio(
        str(audio_path),
        sampling_rate=SAMPLE_RATE
    )

    window = SAMPLE_RATE * WINDOW_SECONDS
    step = SAMPLE_RATE * STEP_SECONDS

    embeddings = []
    segments = []

    for start in range(0, len(audio), step):

        end = min(start + window, len(audio))

        chunk = audio[start:end]

        if len(chunk) < SAMPLE_RATE:
            continue

        # Тыныш бөліктерді өткізіп жіберу
        rms = np.sqrt(np.mean(chunk ** 2))

        if rms < 0.005:
            continue

        signal = torch.from_numpy(
            chunk.copy()
        ).float().unsqueeze(0)

        with torch.inference_mode():
            embedding = classifier.encode_batch(
                signal
            )

        embeddings.append(
            embedding.squeeze().cpu().numpy()
        )

        segments.append({
            "start": round(start / SAMPLE_RATE, 2),
            "end": round(end / SAMPLE_RATE, 2)
        })

    if len(embeddings) < 2:
        return []

    # Дауыс ерекшеліктері бойынша топтастыру
    clustering = AgglomerativeClustering(
        n_clusters=2,
        metric="cosine",
        linkage="average"
    )

    labels = clustering.fit_predict(
        np.asarray(embeddings)
    )

    speaker_map = {}

    for segment, label in zip(segments, labels):

        label = int(label)

        if label not in speaker_map:
            speaker_map[label] = (
                f"SPEAKER_{len(speaker_map) + 1}"
            )

        segment["speaker"] = speaker_map[label]

    return segments

def merge_segments(segments):

    if not segments:
        return []

    merged = [segments[0].copy()]

    for segment in segments[1:]:

        current = merged[-1]

        if (
            segment["speaker"] == current["speaker"]
            and segment["start"] <= current["end"]
        ):
            current["end"] = max(
                current["end"],
                segment["end"]
            )

        else:
            new_segment = segment.copy()

            if new_segment["start"] < current["end"]:

                boundary = round(
                    (current["end"] +
                     new_segment["start"]) / 2, 2
                )

                current["end"] = boundary
                new_segment["start"] = boundary

            merged.append(new_segment)

    return merged
if __name__ == "__main__":

    print("\nАудио талдануда...")

    result = diarize_audio(
        BASE_DIR / "test.m4a"
    )

    result = merge_segments(result)

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=4
    ))