CREATE TABLE users (
    id SERIAL PRIMARY KEY,

    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);