
import torch
from pathlib import Path
from faster_whisper.audio import decode_audio

from transformers import (
    WhisperProcessor,
    WhisperForConditionalGeneration
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "whisper-kazakh"

print("Қазақша Whisper моделі іске қосылуда...")

processor = WhisperProcessor.from_pretrained(
    str(MODEL_PATH),
    local_files_only=True
)

model = WhisperForConditionalGeneration.from_pretrained(
    str(MODEL_PATH),
    local_files_only=True
)

model.eval()

print("Қазақша модель дайын!")


def transcribe_audio(audio_path):

    print("Аудио өңделуде...")

    audio = decode_audio(
        str(audio_path),
        sampling_rate=16000
    )

    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt",
        return_attention_mask=True
    )

    with torch.inference_mode():
        predicted_ids = model.generate(
            input_features=inputs.input_features,
            attention_mask=inputs.attention_mask,
            language="kk",
            task="transcribe",
            max_new_tokens=256,
            num_beams=5
        )

    text = processor.batch_decode(
        predicted_ids,
        skip_special_tokens=True
    )[0]

    return {
        "text": text.strip(),
        "language": "kk"
    }


if __name__ == "__main__":

    result = transcribe_audio(
        BASE_DIR / "test.m4a"
    )

    print("\nАнықталған тіл:", result["language"])
    print("\nӘңгіме мәтіні:")
    print(result["text"])