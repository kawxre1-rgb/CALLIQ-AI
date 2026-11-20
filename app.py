from tasks import (
    init_tasks,
    create_task,
    get_tasks,
    confirm_task,
    complete_task,
    delete_task_by_call
)
from flask import (
    Flask, render_template, request,
    jsonify, send_from_directory
)

from pathlib import Path
from werkzeug.utils import secure_filename
from uuid import uuid4

from pipeline import process_call
from database import (
    init_db, save_call,
    get_calls, get_call, delete_call
)

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True
app.json.ensure_ascii = False

UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

print("Жоба папкасы:", BASE_DIR)
print("HTML папкасы:", app.template_folder)
print("HTML файл:", BASE_DIR / "templates" / "index.html")

app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "mp3", "m4a", "wav", "ogg", "webm"
}

init_db()
init_tasks()

# Басты бет
@app.route("/")
def index():

    html_path = BASE_DIR / "templates" / "index.html"

    html = html_path.read_text(encoding="utf-8")

    print("HTML файлы:", html_path)
    print("Жаңа модуль бар:", "recordConsent" in html)

    return app.response_class(
        html,
        mimetype="text/html",
        headers={"Cache-Control": "no-store"}
    )


# Аудионы қабылдау және талдау
@app.route("/api/analyze", methods=["POST"])
def analyze():

    if request.form.get("consent") != "true":
        return jsonify({
            "error": "Қатысушылардың келісімі қажет"
        }), 400

    audio = request.files.get("audio")

    if not audio or not audio.filename:
        return jsonify({
            "error": "Аудиофайл таңдалмаған"
        }), 400

    extension = Path(audio.filename).suffix.lower()[1:]

    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": "Аудиоформат қолдау таппайды"
        }), 400

    filename = f"{uuid4().hex}.{extension}"
    audio_path = UPLOAD_FOLDER / filename

    try:

        audio.save(audio_path)

        result = process_call(audio_path)

        call_id = save_call(filename, result)
        task_id = create_task(call_id, result)

        print("Құрылған тапсырма ID:", task_id)

        return jsonify({
            "success": True,
            "call": get_call(call_id)
        })

    except Exception as error:

        audio_path.unlink(missing_ok=True)
        app.logger.error(str(error))

        return jsonify({
            "error": "Аудионы өңдеу кезінде қате шықты"
        }), 500


# Барлық қоңыраулар
@app.route("/api/calls")
def calls():

    return jsonify(get_calls())


# Бір қоңыраудың карточкасы
@app.route("/api/calls/<int:call_id>")
def call_detail(call_id):

    call = get_call(call_id)

    if call is None:
        return jsonify({
            "error": "Қоңырау табылмады"
        }), 404

    return jsonify(call)


# Аудионы тыңдау
@app.route("/audio/<filename>")
def play_audio(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# Қоңырауды және аудионы өшіру
@app.route(
    "/api/calls/<int:call_id>",
    methods=["DELETE"]
)
def remove_call(call_id):

    call = get_call(call_id)

    if call is None:
        return jsonify({
            "error": "Қоңырау табылмады"
        }), 404

    filename = secure_filename(call["filename"])

    audio_path = UPLOAD_FOLDER / filename
    audio_path.unlink(missing_ok=True)
    delete_task_by_call(call_id)

    delete_call(call_id)

    return jsonify({"success": True})


# Статистика
@app.route("/api/stats")
def statistics():

    data = get_calls()

    return jsonify({
        "total_calls": len(data),

        "agreements": sum(
            c["agreement"] not in (
                "", "Нақтылау қажет", None
            )
            for c in data
        ),

        "waiting": sum(
            "күтілуде" in (c["status"] or "").lower()
            for c in data
        ),

        "complaints": sum(
            c["complaint"] not in (
                "",
                "Шағым айтылмады",
                "Нақтылау қажет",
                None
            )
            for c in data
        )
    })


# Барлық тапсырмаларды алу
@app.route("/api/tasks", methods=["GET"])
def api_tasks():

    return jsonify(get_tasks())


# Тапсырманың мерзімін растау
@app.route(
    "/api/tasks/<int:task_id>/confirm",
    methods=["POST"]
)
def api_confirm_task(task_id):

    data = request.get_json(silent=True) or {}
    due_at = data.get("due_at")

    if not isinstance(due_at, str) or "T" not in due_at:
        return jsonify({
            "success": False,
            "error": "Күн мен уақытты енгізіңіз"
        }), 400

    try:
        success = confirm_task(task_id, due_at)

        return jsonify({
            "success": success
        }), 200 if success else 409

    except ValueError:
        return jsonify({
            "success": False,
            "error": "Мерзім форматы дұрыс емес"
        }), 400


# Тапсырманы орындалды деп белгілеу
@app.route(
    "/api/tasks/<int:task_id>/complete",
    methods=["POST"]
)
def api_complete_task(task_id):

    success = complete_task(task_id)

    return jsonify({
        "success": success
    }), 200 if success else 409

if __name__ == "__main__":

    print("CALLIQ AI сервері іске қосылуда...")
    print(app.url_map)

    app.run(
        host="127.0.0.1",
        port=5002,
        debug=False
    )