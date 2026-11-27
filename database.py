import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ko'rilgan yangiliklar (bir xil yangilik qayta taklif qilinmasligi uchun)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link TEXT UNIQUE,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Rejalashtirilgan postlar (AI yangilik yoki qo'lda kiritilgan postlar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_type TEXT, -- 'ai_news' yoki 'manual'
        caption TEXT,
        media_type TEXT, -- 'none', 'photo', 'video', 'animation' (gif), 'document'
        media_file_id TEXT,
        schedule_time TEXT, -- 'YYYY-MM-DD HH:MM'
        status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def is_news_processed(link: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM processed_news WHERE link = ?", (link,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_news_processed(link: str, title: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO processed_news (link, title) VALUES (?, ?)", (link, title))
        conn.commit()
    finally:
        conn.close()

def add_scheduled_post(post_type: str, caption: str, media_type: str, media_file_id: str, schedule_time: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO scheduled_posts (post_type, caption, media_type, media_file_id, schedule_time, status)
    VALUES (?, ?, ?, ?, ?, 'pending')
    """, (post_type, caption, media_type, media_file_id, schedule_time))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_due_posts(current_time_str: str):
    """Belgilangan vaqti yetib kelgan (yoki o'tib ketgan) yuborilmagan postlarni oladi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM scheduled_posts 
    WHERE status = 'pending' AND schedule_time <= ?
    ORDER BY schedule_time ASC
    """, (current_time_str,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_post_status(post_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE scheduled_posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()

def get_upcoming_posts(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM scheduled_posts 
    WHERE status = 'pending'
    ORDER BY schedule_time ASC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_scheduled_post(post_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
