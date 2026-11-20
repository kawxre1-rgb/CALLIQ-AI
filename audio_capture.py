import requests

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CAPTURE_DIR = BASE_DIR / "captures"

API_URL = "http://127.0.0.1:5001/api/analyze"

ALLOWED_EXTENSIONS = {
    ".wav", ".m4a", ".mp3", ".ogg", ".webm"
}

CAPTURE_DIR.mkdir(exist_ok=True)


def send_audio(audio_path):

    audio_path = Path(audio_path)

    if not audio_path.is_file():
        print("Аудиофайл табылмады!")
        return

    if audio_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        print("Аудио форматы қолдау таппайды!")
        return

    print("Аудио:", audio_path.name)

    consent = input(
        "Барлық қатысушы жазбаға және "
        "AI талдауына келісім берді ме? (yes/no): "
    )

    if consent.strip().lower() != "yes":
        print("Аудио жіберілмеді.")
        return

    print("CALLIQ AI жүйесіне жіберілуде...")

    try:

        with open(audio_path, "rb") as audio:

            response = requests.post(
                API_URL,
                files={
                    "audio": (audio_path.name, audio)
                },
                data={"consent": "true"},
                timeout=600
            )

        response.raise_for_status()

        result = response.json()

        if result.get("success"):

            call = result["call"]

            print("\nТАЛДАУ АЯҚТАЛДЫ!")
            print("Қоңырау ID:", call["id"])
            print("Тақырыбы:", call["topic"])
            print("Бюджет:", call["budget"])
            print("Мерзім:", call["deadline"])

        else:

            print("Талдау сәтсіз аяқталды.")

    except requests.RequestException as error:

        print("Сервер қатесі:", error)


if __name__ == "__main__":

    files = [
        path for path in CAPTURE_DIR.iterdir()
        if path.is_file()
        and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    if not files:

        print("captures папкасында аудио жоқ.")

    else:

        for index, path in enumerate(files, 1):

            print(f"{index}. {path.name}")

        try:

            number = int(input("Аудио нөмірін таңдаңыз: "))

            if 1 <= number <= len(files):

                send_audio(files[number - 1])

            else:

                print("Қате нөмір!")

        except ValueError:

            print("Сан енгізіңіз!")