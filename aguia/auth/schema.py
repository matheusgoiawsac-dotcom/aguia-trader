"""Auth schema for users and sessions."""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    email_original TEXT NOT NULL,
    email_normalized TEXT NOT NULL UNIQUE,
    age INTEGER NOT NULL,
    password_hash TEXT NOT NULL,
    password_algo TEXT NOT NULL DEFAULT 'argon2id',
    password_params TEXT,
    avatar_blob BLOB,
    avatar_mime TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    csrf_token_hash TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_used_at TEXT,
    revoked_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

AUTH_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email_norm ON users(email_normalized);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);",
]
