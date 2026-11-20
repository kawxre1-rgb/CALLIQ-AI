
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "calliq.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 1. Тапсырмалар кестесін жасау
def init_tasks():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            budget TEXT,
            original_deadline TEXT,
            due_at TEXT,
            status TEXT DEFAULT 'review',
            created_at TEXT,
            completed_at TEXT
        )
    """)

    conn.commit()
    conn.close()

    print("TASK TRACKER дайын!")


# 2. AI нәтижесінен тапсырма жасау
def create_task(call_id, result):

    validation = result.get("validation", {})

    if not validation.get("promise_signal"):
        return None

    agreement = result.get("agreement")

    if not agreement or agreement in [
        "Нақтылау қажет",
        "Жоқ",
        "Міндеттеме алынбаған"
    ]:
        return None
    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO tasks (
            call_id,
            title,
            budget,
            original_deadline,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        call_id,
        agreement,
        result.get("budget"),
        result.get("deadline"),
        "review",
        datetime.now().isoformat(timespec="seconds")
    ))

    task = conn.execute(
        "SELECT id FROM tasks WHERE call_id = ?",
        (call_id,)
    ).fetchone()

    conn.commit()
    conn.close()

    return task["id"] if task else None


# 3. Менеджердің мерзімді растауы
def confirm_task(task_id, due_at):

    deadline = datetime.fromisoformat(due_at)

    if deadline.tzinfo is not None:
        deadline = deadline.astimezone().replace(
            tzinfo=None
        )

    conn = get_connection()

    cursor = conn.execute("""
        UPDATE tasks
        SET due_at = ?, status = 'pending'
        WHERE id = ? AND status = 'review'
    """, (
        deadline.isoformat(timespec="seconds"),
        task_id
    ))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return updated


# 4. Тапсырманың нақты мәртебесін анықтау
def calculate_status(task, now=None):

    now = now or datetime.now()

    if task["status"] == "completed":
        return "Орындалды"

    if task["status"] == "review":
        return "Растауды қажет етеді"

    if not task["due_at"]:
        return "Мерзімді нақтылау қажет"

    deadline = datetime.fromisoformat(
        task["due_at"]
    )

    if deadline <= now:
        return "Мерзімі өтті"

    if deadline - now <= timedelta(hours=1):
        return "Мерзімі жақындады"

    return "Орындалуда"


# 5. Барлық тапсырмаларды алу
def get_tasks():

    conn = get_connection()

    rows = conn.execute("""
        SELECT * FROM tasks
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    tasks = []

    for row in rows:

        task = dict(row)

        task["display_status"] = calculate_status(
            task
        )

        tasks.append(task)

    return tasks


# 6. Тапсырманы орындалды деп белгілеу
def complete_task(task_id):

    conn = get_connection()

    cursor = conn.execute("""
        UPDATE tasks
        SET status = 'completed',
            completed_at = ?
        WHERE id = ?
          AND status = 'pending'
    """, (
        datetime.now().isoformat(timespec="seconds"),
        task_id
    ))

    updated = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return updated


# 7. Қоңыраумен байланысты тапсырманы жою
def delete_task_by_call(call_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM tasks WHERE call_id = ?",
        (call_id,)
    )

    conn.commit()
    conn.close()


# 8. Автоматты тестілеу
if __name__ == "__main__":

    init_tasks()

    now = datetime.now()

    tests = [
        (
            {"status": "review", "due_at": None},
            "Растауды қажет етеді"
        ),
        (
            {
                "status": "pending",
                "due_at": (
                    now + timedelta(hours=3)
                ).isoformat()
            },
            "Орындалуда"
        ),
        (
            {
                "status": "pending",
                "due_at": (
                    now + timedelta(minutes=30)
                ).isoformat()
            },
            "Мерзімі жақындады"
        ),
        (
            {
                "status": "pending",
                "due_at": (
                    now - timedelta(hours=2)
                ).isoformat()
            },
            "Мерзімі өтті"
        ),
        (
            {"status": "completed", "due_at": None},
            "Орындалды"
        )
    ]

    passed = 0

    for i, (task, expected) in enumerate(tests, 1):

        result = calculate_status(task, now)

        success = result == expected

        if success:
            passed += 1

        print(f"\nТЕСТ {i}")
        print("Мәртебе:", result)
        print("Нәтиже:", "PASS" if success else "FAIL")

    print(f"\nЖалпы нәтиже: {passed}/{len(tests)}")
