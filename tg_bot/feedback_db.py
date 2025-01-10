import sqlite3


def init_db():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

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


def get_all_ratings():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, rating, created_at FROM ratings")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_feedbacks():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_question, bot_answer, user_feedback, created_at FROM feedbacks")
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_ratings():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ratings;")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='ratings';")
    conn.commit()
    conn.close()

def clear_feedbacks():
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedbacks;")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='feedbacks';")
    conn.commit()
    conn.close()