import os
from contextlib import contextmanager
from typing import List, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

engine = create_engine(f'postgresql+psycopg2://{os.getenv("DB_NAME")}:{os.getenv("DB_PASSWORD")}' +
                       f'@{os.getenv("DB_HOST")}:{5432}/{os.getenv("DB_NAME")}')
Session = sessionmaker(bind=engine)


@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    with get_session() as session:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS ratings (
                id SERIAL PRIMARY KEY,
                rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id SERIAL PRIMARY KEY,
                user_question TEXT NOT NULL,
                bot_answer TEXT NOT NULL,
                user_feedback TEXT,
                rate INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        session.commit()  # Фиксируем создание таблиц


def save_rating(rating: int):
    with get_session() as session:
        session.execute(
            text("INSERT INTO ratings (rating) VALUES (:rating)"),
            {"rating": rating}
        )
        session.commit()


def save_feedback(user_question: str, bot_answer: str, user_feedback: str, rate: int):
    with get_session() as session:
        session.execute(
            text("""
                INSERT INTO feedbacks (user_question, bot_answer, user_feedback, rate)
                VALUES (:user_question, :bot_answer, :user_feedback, :rate)
            """),
            {
                "user_question": user_question,
                "bot_answer": bot_answer,
                "user_feedback": user_feedback,
                "rate": rate
            }
        )
        session.commit()


def get_all_ratings() -> List[Tuple]:
    with get_session() as session:
        result = session.execute(text("SELECT id, rating, created_at FROM ratings"))
        rows = result.fetchall()
        return rows


def get_all_feedbacks() -> List[Tuple]:
    with get_session() as session:
        result = session.execute(
            text("""
                SELECT id, user_question, bot_answer, user_feedback, rate, created_at 
                FROM feedbacks
            """)
        )
        rows = result.fetchall()
        return rows


def clear_ratings():
    with get_session() as session:
        session.execute(text("TRUNCATE TABLE ratings RESTART IDENTITY CASCADE;"))
        session.commit()


def clear_feedbacks():
    with get_session() as session:
        session.execute(text("TRUNCATE TABLE feedbacks RESTART IDENTITY CASCADE;"))
        session.commit()
