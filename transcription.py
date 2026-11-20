
from faster_whisper import WhisperModel
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

print("Whisper моделі іске қосылуда...")

model = WhisperModel(
    str(BASE_DIR / "models" / "whisper-medium"),
    device="cpu",
    compute_type="int8",
    local_files_only=True
)

print("Модель дайын!")


def transcribe_audio(audio_path):

    print("Аудио мәтінге айналдырылуда...")

    segments, info = model.transcribe(
        str(audio_path),
        language="kk",
        task="transcribe",
        beam_size=10,
        temperature=0,
        vad_filter=True,
        condition_on_previous_text=False,
        repetition_penalty=1.1,
        initial_prompt=(
            "Қазақ тіліндегі клиент пен менеджердің "
            "құрылыс және интерьер бояулары туралы әңгімесі."
        ),
        hotwords=(
            "бояу, интерьер, қонақ бөлме, жуылатын, "
            "бюджет, теңге, баға, тапсырыс, жеткізу, "
            "тауар, тізім, менеджер, клиент, мерзім"
        )
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return {
        "text": text,
        "language": info.language
    }


if __name__ == "__main__":
    result = transcribe_audio(BASE_DIR / "test.m4a")

    print("Анықталған тіл:", result["language"])
    print("Әңгіме мәтіні:")
    print(result["text"])
