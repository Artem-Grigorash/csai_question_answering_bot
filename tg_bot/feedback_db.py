import sqlite3

def init_db():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()

    # Таблица для оценок (1–5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Таблица для письменного фидбэка
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            bot_answer TEXT NOT NULL,
            user_feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

    conn.commit()
    conn.close()

def save_rating(rating: int):
    """Сохраняем оценку в таблицу ratings."""
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ratings (rating) VALUES (?)
    """, (rating,))
    conn.commit()
    conn.close()


def save_feedback(user_question, bot_answer, user_feedback):
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedbacks (user_question, bot_answer, user_feedback)
        VALUES (?, ?, ?)
    """, (user_question, bot_answer, user_feedback))
    conn.commit()
    conn.close()

