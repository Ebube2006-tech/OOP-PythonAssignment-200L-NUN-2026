from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "study_assistant.db"

GRADE_POINTS = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "E": 1,
    "F": 0,
}


class Database:
    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    last_study_date TEXT,
                    total_study_minutes INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS gpa_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    credit_units REAL NOT NULL,
                    grade TEXT NOT NULL,
                    grade_point REAL NOT NULL,
                    total_points REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    session_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    # ---------- auth ----------
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        salt = salt or os.urandom(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100_000
        )
        return salt.hex(), pwd_hash.hex()

    @staticmethod
    def verify_password(password: str, salt_hex: str, stored_hash_hex: str) -> bool:
        salt = bytes.fromhex(salt_hex)
        _, test_hash = Database.hash_password(password, salt)
        return test_hash == stored_hash_hex

    def create_user(self, username: str, password: str) -> Tuple[bool, str]:
        username = username.strip()
        if not username or not password:
            return False, "Username and password are required."
        salt, pwd_hash = self.hash_password(password)
        created_at = datetime.now().isoformat(timespec="seconds")
        try:
            with self.connect() as conn:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, password_salt, created_at) VALUES (?, ?, ?, ?)",
                    (username, pwd_hash, salt, created_at),
                )
                user_id = cur.lastrowid
                conn.execute(
                    "INSERT INTO user_stats (user_id, current_streak, last_study_date, total_study_minutes, updated_at) VALUES (?, 0, NULL, 0, ?)",
                    (user_id, created_at),
                )
            return True, "Account created successfully."
        except sqlite3.IntegrityError:
            return False, "Username already exists."
        except Exception as exc:
            return False, f"Could not create account: {exc}"

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        if not self.verify_password(password, row["password_salt"], row["password_hash"]):
            return None
        return dict(row)

    # ---------- helpers ----------
    @staticmethod
    def now_text() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def today_text() -> str:
        return date.today().isoformat()

    # ---------- dashboard / stats ----------
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        with self.connect() as conn:
            task_counts = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_tasks,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
                    SUM(CASE WHEN status != 'Completed' THEN 1 ELSE 0 END) AS pending_tasks,
                    SUM(CASE WHEN due_date = ? THEN 1 ELSE 0 END) AS due_today,
                    SUM(CASE WHEN due_date BETWEEN ? AND ? THEN 1 ELSE 0 END) AS due_7_days
                FROM tasks
                WHERE user_id = ?
                """,
                (
                    self.today_text(),
                    self.today_text(),
                    (date.today() + timedelta(days=7)).isoformat(),
                    user_id,
                ),
            ).fetchone()

            note_count = conn.execute(
                "SELECT COUNT(*) AS count FROM notes WHERE user_id = ?",
                (user_id,),
            ).fetchone()["count"]

            gpa_row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(total_points), 0) AS total_points,
                    COALESCE(SUM(credit_units), 0) AS total_credits
                FROM gpa_records
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

            stats_row = conn.execute(
                "SELECT current_streak, total_study_minutes, last_study_date FROM user_stats WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        total_points = float(gpa_row["total_points"] or 0)
        total_credits = float(gpa_row["total_credits"] or 0)
        gpa = round(total_points / total_credits, 2) if total_credits else 0.0

        return {
            "total_tasks": int(task_counts["total_tasks"] or 0),
            "completed_tasks": int(task_counts["completed_tasks"] or 0),
            "pending_tasks": int(task_counts["pending_tasks"] or 0),
            "due_today": int(task_counts["due_today"] or 0),
            "due_7_days": int(task_counts["due_7_days"] or 0),
            "notes_count": int(note_count or 0),
            "total_study_minutes": int(stats_row["total_study_minutes"] or 0),
            "current_streak": int(stats_row["current_streak"] or 0),
            "last_study_date": stats_row["last_study_date"],
            "gpa": gpa,
            "total_credits": total_credits,
        }

    # ---------- tasks ----------
    def add_task(self, user_id: int, title: str, description: str, due_date: str, priority: str, status: str = "Pending") -> Tuple[bool, str]:
        if not title.strip():
            return False, "Task title is required."
        created_at = self.now_text()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (user_id, title, description, due_date, priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title.strip(), description.strip(), due_date or None, priority, status, created_at, created_at),
            )
        return True, "Task added successfully."

    def update_task(self, task_id: int, user_id: int, title: str, description: str, due_date: str, priority: str, status: str) -> Tuple[bool, str]:
        if not title.strip():
            return False, "Task title is required."
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, due_date = ?, priority = ?, status = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (title.strip(), description.strip(), due_date or None, priority, status, self.now_text(), task_id, user_id),
            )
        return True, "Task updated successfully."

    def delete_task(self, task_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))

    def set_task_status(self, task_id: int, user_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (status, self.now_text(), task_id, user_id),
            )

    def fetch_tasks(self, user_id: int, search: str = "", status: str = "All", priority: str = "All") -> List[Dict[str, Any]]:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params: List[Any] = [user_id]
        if search:
            query += " AND (title LIKE ? OR description LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        if status and status != "All":
            query += " AND status = ?"
            params.append(status)
        if priority and priority != "All":
            query += " AND priority = ?"
            params.append(priority)
        query += " ORDER BY CASE WHEN due_date IS NULL OR due_date = '' THEN 1 ELSE 0 END, due_date ASC, priority DESC, id DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ---------- notes ----------
    def add_note(self, user_id: int, title: str, content: str) -> Tuple[bool, str]:
        if not title.strip():
            return False, "Note title is required."
        now = self.now_text()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO notes (user_id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, title.strip(), content.strip(), now, now),
            )
        return True, "Note saved successfully."

    def update_note(self, note_id: int, user_id: int, title: str, content: str) -> Tuple[bool, str]:
        if not title.strip():
            return False, "Note title is required."
        with self.connect() as conn:
            conn.execute(
                "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (title.strip(), content.strip(), self.now_text(), note_id, user_id),
            )
        return True, "Note updated successfully."

    def delete_note(self, note_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))

    def fetch_notes(self, user_id: int, search: str = "") -> List[Dict[str, Any]]:
        query = "SELECT * FROM notes WHERE user_id = ?"
        params: List[Any] = [user_id]
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like])
        query += " ORDER BY updated_at DESC, id DESC"
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    # ---------- gpa ----------
    def add_gpa_record(self, user_id: int, course_name: str, credit_units: float, grade: str) -> Tuple[bool, str]:
        if not course_name.strip():
            return False, "Course name is required."
        if grade not in GRADE_POINTS:
            return False, "Select a valid grade."
        try:
            credit_units = float(credit_units)
            if credit_units <= 0:
                return False, "Credit units must be greater than zero."
        except ValueError:
            return False, "Credit units must be a number."
        grade_point = float(GRADE_POINTS[grade])
        total_points = credit_units * grade_point
        now = self.now_text()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO gpa_records (user_id, course_name, credit_units, grade, grade_point, total_points, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, course_name.strip(), credit_units, grade, grade_point, total_points, now),
            )
        return True, "Course saved successfully."

    def delete_gpa_record(self, record_id: int, user_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM gpa_records WHERE id = ? AND user_id = ?", (record_id, user_id))

    def fetch_gpa_records(self, user_id: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM gpa_records WHERE user_id = ? ORDER BY id DESC",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def calculate_gpa(self, user_id: int) -> Tuple[float, float, float]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(total_points), 0) AS total_points,
                       COALESCE(SUM(credit_units), 0) AS total_credits
                FROM gpa_records WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        total_points = float(row["total_points"] or 0)
        total_credits = float(row["total_credits"] or 0)
        gpa = round(total_points / total_credits, 2) if total_credits else 0.0
        return gpa, total_credits, total_points

    # ---------- study sessions / streak ----------
    def log_study_session(self, user_id: int, duration_minutes: int, session_type: str = "Pomodoro") -> None:
        duration_minutes = int(duration_minutes)
        now = self.now_text()
        today = self.today_text()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO study_sessions (user_id, session_date, duration_minutes, session_type, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, today, duration_minutes, session_type, now),
            )
            stats = conn.execute(
                "SELECT current_streak, last_study_date, total_study_minutes FROM user_stats WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if stats is None:
                conn.execute(
                    "INSERT INTO user_stats (user_id, current_streak, last_study_date, total_study_minutes, updated_at) VALUES (?, 1, ?, ?, ?)",
                    (user_id, today, duration_minutes, now),
                )
                return

            last_date = stats["last_study_date"]
            streak = int(stats["current_streak"] or 0)
            total_minutes = int(stats["total_study_minutes"] or 0) + duration_minutes
            if last_date == today:
                streak = streak or 1
            elif last_date == (date.today() - timedelta(days=1)).isoformat():
                streak += 1
            else:
                streak = 1

            conn.execute(
                """
                UPDATE user_stats
                SET current_streak = ?, last_study_date = ?, total_study_minutes = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (streak, today, total_minutes, now, user_id),
            )

    def get_recent_study_sessions(self, user_id: int, limit: int = 7) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_study_summary(self, user_id: int) -> Dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) AS total_minutes, COUNT(*) AS total_sessions FROM study_sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            stats = conn.execute(
                "SELECT current_streak, last_study_date, total_study_minutes FROM user_stats WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return {
            "total_minutes": int(row["total_minutes"] or 0),
            "total_sessions": int(row["total_sessions"] or 0),
            "current_streak": int(stats["current_streak"] or 0) if stats else 0,
            "last_study_date": stats["last_study_date"] if stats else None,
            "tracked_minutes": int(stats["total_study_minutes"] or 0) if stats else 0,
        }
