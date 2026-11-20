import sqlite3
import json

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "calliq.db"


# ==============================
# ДЕРЕКТЕР БАЗАСЫНА ҚОСЫЛУ
# ==============================

def get_connection():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


# ==============================
# ДЕРЕКТЕР БАЗАСЫН ҚҰРУ
# ==============================

def init_db():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            created_at TEXT,
            topic TEXT,
            summary TEXT,
            customer_request TEXT,
            budget TEXT,
            agreement TEXT,
            deadline TEXT,
            status TEXT,
            complaint TEXT,
            flag TEXT,
            transcription TEXT,
            language TEXT,
            processing_time REAL,
            reviewed INTEGER DEFAULT 0,
            dialogue TEXT DEFAULT '[]',
            speaker_count INTEGER DEFAULT 0,
            validation TEXT DEFAULT '{}',
            dialogue_error TEXT
        )
    """)

    conn.commit()
    conn.close()

    migrate_database()

    print("CALLIQ деректер базасы дайын!")


# ==============================
# БҰРЫНҒЫ БАЗАНЫ ЖАҢАРТУ
# ==============================

def migrate_database():

    conn = get_connection()

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(calls)"
        ).fetchall()
    }

    new_columns = {
        "dialogue": "TEXT DEFAULT '[]'",
        "speaker_count": "INTEGER DEFAULT 0",
        "validation": "TEXT DEFAULT '{}'",
        "dialogue_error": "TEXT"
    }

    for name, definition in new_columns.items():

        if name not in columns:

            conn.execute(
                f"ALTER TABLE calls "
                f"ADD COLUMN {name} {definition}"
            )

            print(f"Жаңа баған қосылды: {name}")

    conn.commit()
    conn.close()


# ==============================
# ҚОҢЫРАУДЫ САҚТАУ
# ==============================

def save_call(filename, result):

    conn = get_connection()

    cursor = conn.execute("""
        INSERT INTO calls (
            filename,
            created_at,
            topic,
            summary,
            customer_request,
            budget,
            agreement,
            deadline,
            status,
            complaint,
            flag,
            transcription,
            language,
            processing_time,
            dialogue,
            speaker_count,
            validation,
            dialogue_error
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?
        )
    """, (
        filename,

        datetime.now().strftime("%Y-%m-%d %H:%M"),

        result.get("topic", ""),
        result.get("summary", ""),
        result.get("customer_request", ""),
        result.get("budget", ""),
        result.get("agreement", ""),
        result.get("deadline", ""),
        result.get("status", ""),
        result.get("complaint", ""),
        result.get("flag", ""),
        result.get("transcription", ""),
        result.get("language", "kk"),
        result.get("processing_time", 0),

        json.dumps(
            result.get("dialogue", []),
            ensure_ascii=False
        ),

        result.get("speaker_count", 0),

        json.dumps(
            result.get("validation", {}),
            ensure_ascii=False
        ),

        result.get("dialogue_error")
    ))

    call_id = cursor.lastrowid

    conn.commit()
    conn.close()

    print(f"Қоңырау базаға сақталды. ID: {call_id}")

    return call_id


# ==============================
# JSON ДЕРЕКТЕРІН ҚАЛПЫНА КЕЛТІРУ
# ==============================

def decode_call(row):

    if row is None:
        return None

    call = dict(row)

    try:

        call["dialogue"] = json.loads(
            call.get("dialogue") or "[]"
        )

    except (json.JSONDecodeError, TypeError):

        call["dialogue"] = []

    try:

        call["validation"] = json.loads(
            call.get("validation") or "{}"
        )

    except (json.JSONDecodeError, TypeError):

        call["validation"] = {}

    return call


# ==============================
# БАРЛЫҚ ҚОҢЫРАУЛАРДЫ АЛУ
# ==============================

def get_calls():

    conn = get_connection()

    calls = conn.execute("""
        SELECT * FROM calls
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [
        decode_call(call)
        for call in calls
    ]


# ==============================
# БІР ҚОҢЫРАУДЫ АЛУ
# ==============================

def get_call(call_id):

    conn = get_connection()

    call = conn.execute(
        "SELECT * FROM calls WHERE id = ?",
        (call_id,)
    ).fetchone()

    conn.close()

    return decode_call(call)


# ==============================
# ҚОҢЫРАУДЫ ӨШІРУ
# ==============================

def delete_call(call_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM calls WHERE id = ?",
        (call_id,)
    )

    conn.commit()
    conn.close()


# ==============================
# БАЗАНЫ ТЕКСЕРУ
# ==============================

if __name__ == "__main__":

    init_db()

    print("\nДеректер базасының құрылымы:\n")

    conn = get_connection()

    columns = conn.execute(
        "PRAGMA table_info(calls)"
    ).fetchall()

    for column in columns:

        print(
            f"{column['name']} — {column['type']}"
        )

    conn.close()

    print("\nДеректер базасын тексеру аяқталды!")