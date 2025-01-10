CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_question TEXT NOT NULL,
    bot_answer TEXT NOT NULL,
    user_feedback TEXT,
    rate INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

