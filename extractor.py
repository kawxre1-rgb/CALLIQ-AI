
import re

NUMBERS = {
    "нөл": 0,
    "бір": 1,
    "екі": 2,
    "үш": 3,
    "төрт": 4,
    "бес": 5,
    "алты": 6,
    "жеті": 7,
    "сегіз": 8,
    "тоғыз": 9,
    "он": 10,
    "жиырма": 20,
    "отыз": 30,
    "қырық": 40,
    "елу": 50,
    "алпыс": 60,
    "жетпіс": 70,
    "сексен": 80,
    "тоқсан": 90
}

SCALES = {
    "мың": 1000,
    "миллион": 1000000
}

UNKNOWN = "Нақтылау қажет"


# 1. Қазақша сандарды цифрға айналдыру
def parse_number(text):

    text = text.strip().lower()

    total = 0
    current = 0

    if not text:
        return None

    for word in text.split():

        if word.isdigit():
            current += int(word)

        elif word in NUMBERS:
            current += NUMBERS[word]

        elif word == "жүз":
            current = (current or 1) * 100

        elif word in SCALES:
            total += (current or 1) * SCALES[word]
            current = 0

        else:
            return None

    return total + current


# 2. Бюджетті анықтау
def extract_budget(text):

    text = text.lower()

    matches = re.findall(
        r"бюджет\w*\s*[:—,-]?\s*"
        r"([\w\s]+?)\s*(?:теңге|₸)",
        text
    )

    amounts = set()

    for phrase in matches:

        phrase = re.sub(
            r"(?<=\d)\s+(?=\d)", "", phrase
        )

        amount = parse_number(phrase)

        if amount is not None:
            amounts.add(amount)

    if len(amounts) == 1:

        amount = amounts.pop()

        return (
            f"{amount:,}".replace(",", " ")
            + " теңге"
        )

    return UNKNOWN


# 3. Сөздің жалғауын алып тастау
def normalize_number_word(word):

    if word in NUMBERS or word.isdigit():
        return word

    endings = [
        "ке", "ге", "қа", "ға",
        "те", "та", "де", "да"
    ]

    for ending in endings:

        if word.endswith(ending):

            base = word[:-len(ending)]

            if base in NUMBERS:
                return base

    return word


# 4. Уақытты анықтау
def extract_deadline(text):

    text = text.lower()

    pattern = (
        r"(?:(бүгін|ертең|бүрсігүні)\s+)?"
        r"сағат\s+"
        r"([\w\s:-]{1,35}?)\s+дейін"
    )

    deadlines = set()

    for match in re.finditer(pattern, text):

        day = match.group(1) or ""
        phrase = match.group(2).strip()

        if re.fullmatch(
            r"\d{1,2}:\d{2}(?:-ге|-ке)?",
            phrase
        ):
            clock = phrase.split("-")[0]
            hour, minute = map(int, clock.split(":"))

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                deadlines.add(
                    f"{day} сағат {clock}-ге дейін".strip()
                )

            continue

        phrase = re.sub(
            r"(?<=\d)-(ге|ке|қа|ға)$", "", phrase
        )

        words = phrase.split()

        words[-1] = normalize_number_word(words[-1])

        hour = parse_number(" ".join(words))

        if hour is not None and 1 <= hour <= 24:

            suffix = (
                "ке" if hour in [3, 4, 5, 13, 14, 15, 23, 24]
                else "ға" if hour in [6, 9, 10, 16, 19, 20]
                else "ге"
            )

            deadlines.add(
                f"{day} сағат {hour}-{suffix} дейін".strip()
            )

    if len(deadlines) == 1:
        return deadlines.pop()

    if "бүгін кешке дейін" in text:
        return "Бүгін кешке дейін"

    if "ертең кешке дейін" in text:
        return "Ертең кешке дейін"

    return UNKNOWN


# 5. Негізгі функция
def extract_data(text):

    return {
        "budget": extract_budget(text),
        "deadline": extract_deadline(text)
    }


# 6. Автоматты тестілеу
if __name__ == "__main__":

    tests = [
        (
            "Бюджетім жетпіс мың теңге. "
            "Бүгін сағат төртке дейін жіберемін.",
            "70 000 теңге",
            "бүгін сағат 4-ке дейін"
        ),
        (
            "Бюджетіміз бес жүз мың теңге. "
            "Ертең сағат он екіге дейін жіберемін.",
            "500 000 теңге",
            "ертең сағат 12-ге дейін"
        ),
        (
            "Бюджетім жүз елу мың теңге. "
            "Ертең сағат үшке дейін хабарласамын.",
            "150 000 теңге",
            "ертең сағат 3-ке дейін"
        ),
        (
            "Бюджетім 250 000 теңге.",
            "250 000 теңге",
            UNKNOWN
        ),
        (
            "Маған ас үйге бояу керек.",
            UNKNOWN,
            UNKNOWN
        ),
        (
            "Бүгін сағат 15:30-ге дейін жіберемін.",
            UNKNOWN,
            "бүгін сағат 15:30-ге дейін"
        ),
        (
            "Бюджетім елу мың теңге. "
            "Бюджетім жетпіс мың теңге.",
            UNKNOWN,
            UNKNOWN
        )
    ]

    passed = 0

    for i, (text, budget, deadline) in enumerate(tests, 1):

        result = extract_data(text)

        success = (
            result["budget"] == budget
            and result["deadline"] == deadline
        )

        if success:
            passed += 1

        print(f"\nТЕСТ {i}")
        print("Мәтін:", text)
        print("Бюджет:", result["budget"])
        print("Мерзім:", result["deadline"])
        print("Нәтиже:", "PASS" if success else "FAIL")

    print(f"\nЖалпы нәтиже: {passed}/{len(tests)}")
