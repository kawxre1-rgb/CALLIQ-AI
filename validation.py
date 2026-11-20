
import re
from extractor import extract_data

UNKNOWN = "Нақтылау қажет"


def validate_result(text, result):

    result = result.copy()
    text_lower = text.lower()

    warnings = []

    # 1. Бюджет пен мерзімді қайта тексеру
    extracted = extract_data(text)

    for field in ["budget", "deadline"]:

        if result.get(field) != extracted[field]:
            warnings.append(
                f"{field}: AI нәтижесі түзетілді"
            )

        result[field] = extracted[field]

    # 2. Шағым белгілерін іздеу
    complaint_words = [
        "кешігіп",
        "кешікті",
        "келген жоқ",
        "жеткізілмеді",
        "көңілім толмай",
        "шағым",
        "сапасыз",
        "ақаулы",
        "дұрыс емес",
        "наразымын"
    ]

    has_complaint_signal = any(
        word in text_lower
        for word in complaint_words
    )

    complaint = str(result.get("complaint") or "")

    if has_complaint_signal:

        if complaint in [
            "", UNKNOWN, "Шағым айтылмады"
        ]:
            result["complaint"] = UNKNOWN
            warnings.append(
                "Мәтінде ықтимал шағым бар"
            )

    elif complaint not in [
        "", UNKNOWN, "Шағым айтылмады"
    ]:
        result["complaint"] = UNKNOWN
        warnings.append(
            "Шағымды қолмен тексеру қажет"
        )

    # 3. Міндеттеме белгілерін анықтау
    promise_words = [
        "жіберемін",
        "жібереміз",
        "хабарласамын",
        "хабарласамыз",
        "тексеремін",
        "тексереміз",
        "дайындаймын",
        "дайындаймыз",
        "жеткіземіз",
        "жеткіземін",
        "қайтарамын"
    ]

    has_promise_signal = any(
        word in text_lower
        for word in promise_words
    )

    if not has_promise_signal:

        if result.get("agreement") not in [
           None, "", UNKNOWN, "Жоқ", "Міндеттеме алынбаған"
        ]:
            result["agreement"] = UNKNOWN
            warnings.append(
                "Міндеттемені растау қажет"
            )

    # 4. AI бақылау ұсынысын қайта құру
    flags = []

    if has_complaint_signal:
        flags.append(
            "Ықтимал клиент шағымын тексеру"
        )

    if has_promise_signal:
        flags.append(
            "Міндеттемені орындауды бақылау"
        )

    if has_promise_signal and result["deadline"] == UNKNOWN:
        flags.append(
            "Орындау мерзімін нақтылау"
        )

    result["flag"] = (
        "; ".join(flags)
        if flags
        else "Қосымша тексеру қажет"
    )

    # 5. Нәтиженің тексеру мәртебесі
    result["validation"] = {
        "warnings": warnings,
        "warning_count": len(warnings),
        "review_required": True,
        "complaint_signal": has_complaint_signal,
        "promise_signal": has_promise_signal
    }

    return result


if __name__ == "__main__":

    import json

    text = """
    Маған қонақ бөлмеге арналған жуылатын
    бояу керек. Бюджетім елу мың теңге.
    Бүгін сағат беске дейін бағасын жіберемін.
    Жақсы, жауабыңызды күтемін.
    """

    ai_result = {
        "topic": "Қонақ бөлмеге бояу",
        "summary": "Клиент жуылатын бояу іздейді",
        "customer_request": "Жуылатын бояу",
        "budget": "1000 теңге",
        "deadline": "5 сағат",
        "agreement": "Бояудың бағасын жіберу",
        "status": "Жауап күтілуде",
        "complaint": "Жеткізу кешікті",
        "flag": "Жеткізу мәселесін тексеру"
    }

    result = validate_result(text, ai_result)

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=4
    ))
