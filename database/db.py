import json
import os
import sqlite3
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "emotion.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表并补齐旧表字段。"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL,
            dominant_emotion TEXT,
            stress_score INTEGER,
            emotions_json TEXT,
            speech_text TEXT,
            chat_message TEXT,
            source TEXT DEFAULT 'manual'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(emotion_records)").fetchall()
    }
    if "username" not in columns:
        cursor.execute(
            "ALTER TABLE emotion_records ADD COLUMN username TEXT NOT NULL DEFAULT ''"
        )

    conn.commit()
    conn.close()
    print("数据库初始化完成")


def save_emotion(
    username: str,
    dominant_emotion: str,
    stress_score: int,
    emotions: dict,
    speech_text: str = "",
    chat_message: str = "",
    source: str = "manual",
):
    """保存一条情绪记录。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emotion_records
        (username, timestamp, dominant_emotion, stress_score, emotions_json, speech_text, chat_message, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        username,
        datetime.now().isoformat(),
        dominant_emotion,
        stress_score,
        json.dumps(emotions, ensure_ascii=False),
        speech_text,
        chat_message,
        source,
    ))
    conn.commit()
    conn.close()


def get_recent_emotions(username: str, days: int = 7) -> list:
    """获取指定用户最近 N 天的情绪记录。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM emotion_records
        WHERE username = ?
          AND timestamp >= datetime('now', 'localtime', ?)
        ORDER BY timestamp DESC
    """, (username, f"-{days} days"))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_emotion_stats(username: str, days: int = 7) -> dict:
    """统计指定用户最近 N 天各情绪的平均值。"""
    records = get_recent_emotions(username, days)
    if not records:
        return {}

    emotion_totals = {}
    count = len(records)

    for record in records:
        emotions = json.loads(record["emotions_json"])
        for emotion, value in emotions.items():
            emotion_totals[emotion] = emotion_totals.get(emotion, 0) + value

    return {k: round(v / count, 1) for k, v in emotion_totals.items()}


def get_emotion_stats_by_range(username: str, days: int = 7) -> list:
    """按时间范围获取指定用户每天的情绪统计。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            date(timestamp) as day,
            AVG(stress_score) as avg_stress,
            COUNT(*) as count
        FROM emotion_records
        WHERE username = ?
          AND timestamp >= datetime('now', 'localtime', ?)
        GROUP BY date(timestamp)
        ORDER BY day ASC
    """, (username, f"-{days} days"))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_user(username: str, password_hash: str) -> bool:
    """创建用户，返回是否成功。"""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
        """, (username, password_hash, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        if conn is not None:
            conn.close()


def get_user(username: str) -> dict | None:
    """查询用户。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_chat_message(username: str, role: str, content: str):
    """保存一条聊天记录。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_records (username, timestamp, role, content)
        VALUES (?, ?, ?, ?)
    """, (
        username,
        datetime.now().isoformat(),
        role,
        content,
    ))
    conn.commit()
    conn.close()


def get_chat_history(username: str, limit: int = 50) -> list:
    """获取指定用户最近的聊天记录。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, timestamp
        FROM chat_records
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (username, limit))
    rows = cursor.fetchall()
    conn.close()
    return list(reversed([dict(row) for row in rows]))


def clear_chat_history(username: str):
    """清空指定用户聊天记录。"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_records WHERE username = ?", (username,))
    conn.commit()
    conn.close()
