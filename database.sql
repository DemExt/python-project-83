-- Таблица urls
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица url_checks
CREATE TABLE url_checks (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    status_code INTEGER,
    h1 TEXT,
    title TEXT,
    description VARCHAR(255),  -- единообразно: description
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);