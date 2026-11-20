
import json
import time

from pathlib import Path

from transcription_kk import transcribe_audio
from dialogue import transcribe_dialogue
from role_detector import detect_roles
from analysis import analyze_call
from extractor import extract_data
from validation import validate_result


# ========================================
# ӨҢДЕУ УАҚЫТЫН ӨЛШЕУ
# ========================================

def measure_time(name, start, timings):

    elapsed = round(
        time.perf_counter() - start, 2
    )

    timings[name] = elapsed

    print(f"{name}: {elapsed} секунд")


# ========================================
# НЕГІЗГІ PIPELINE
# ========================================

def process_call(audio_path):

    start_time = time.perf_counter()

    timings = {}

    dialogue = []
    dialogue_error = None

    text = ""
    language = "kk"

    transcription_mode = "dialogue"

    # ====================================
    # 1. СӨЙЛЕУШІЛЕР ЖӘНЕ ТРАНСКРИПЦИЯ
    # ====================================

    print("\n1. Диалогты анықтау және транскрипция...")

    stage_start = time.perf_counter()

    try:

        dialogue = transcribe_dialogue(audio_path)

        if dialogue:

            dialogue = sorted(
                dialogue,
                key=lambda item: item["start"]
            )

            text = " ".join(
                item.get("text", "").strip()
                for item in dialogue
                if item.get("text", "").strip()
            )

    except Exception as error:

        dialogue_error = str(error)

        print("Диалог модулінің қатесі:", error)

        dialogue = []
        text = ""

    measure_time(
        "Диалог және Whisper",
        stage_start,
        timings
    )

    # ====================================
    # 2. РЕЗЕРВТІК ТРАНСКРИПЦИЯ
    # ====================================

    if not text.strip():

        print("\nРезервтік транскрипция...")

        stage_start = time.perf_counter()

        transcription = transcribe_audio(audio_path)

        text = transcription["text"]

        language = transcription.get(
            "language", "kk"
        )

        transcription_mode = "full_audio"

        measure_time(
            "Резервтік Whisper",
            stage_start,
            timings
        )

    if not text.strip():

        raise ValueError(
            "Аудиодан мәтін анықталмады"
        )

    print("\nТОЛЫҚ МӘТІН:")

    print(text)

    # ====================================
    # 3. КЛИЕНТ ПЕН МЕНЕДЖЕР РӨЛДЕРІ
    # ====================================
    print("\n2. Бірыңғай AI талдау...")

    stage_start = time.perf_counter()

    result = analyze_call(text, dialogue)

    roles = result.pop("roles", {})

    for item in dialogue:

        item["role"] = roles.get(
            item["speaker"],
            "Нақтылау қажет"
        )

        item["review_required"] = True

    measure_time(
        "Unified AI Engine",
        stage_start,
        timings
    )

    # ====================================
    # 6. ВАЛИДАЦИЯ
    # ====================================

    print("\n5. Ақпаратты тексеру...")

    stage_start = time.perf_counter()

    result = validate_result(text, result)

  

    measure_time(
        "Validation",
        stage_start,
        timings
    )

    # ====================================
    # 7. ҚОРЫТЫНДЫ НӘТИЖЕ
    # ====================================

    result["transcription"] = text

    result["language"] = language

    result["dialogue"] = dialogue

    result["dialogue_error"] = dialogue_error

    result["speaker_count"] = len({

        item["speaker"]

        for item in dialogue

    })

    result["transcription_mode"] = transcription_mode

    result["timings"] = timings

    result["processing_time"] = round(

        time.perf_counter() - start_time, 2

    )

    # ====================================
    # ӨҢДЕУ СТАТИСТИКАСЫ
    # ====================================

    print("\n" + "=" * 45)

    print("ӨҢДЕУ УАҚЫТЫ")

    print("=" * 45)

    for name, seconds in timings.items():

        print(f"{name}: {seconds} секунд")

    print("-" * 45)

    print(
        f"Жалпы уақыт: "
        f"{result['processing_time']} секунд"
    )

    print(
        f"Транскрипция режимі: "
        f"{transcription_mode}"
    )

    print("=" * 45)

    return result


# ========================================
# ЖЕКЕ ТЕСТІЛЕУ
# ========================================

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent

    result = process_call(

        BASE_DIR / "test.m4a"

    )

    print("\nCALLIQ AI НӘТИЖЕСІ:\n")

    print(json.dumps(

        result,

        ensure_ascii=False,

        indent=4

    ))
