"""User and session repository."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from aguia.db import get_connection, init_db
from aguia.auth.schema import USERS_TABLE, SESSIONS_TABLE, AUTH_INDEXES
from aguia.auth.utils import normalize_email, now_iso, iso_from_dt, hash_token


class UserRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def _init_auth(self, conn: sqlite3.Connection):
        conn.execute(USERS_TABLE)
        conn.execute(SESSIONS_TABLE)
        for idx in AUTH_INDEXES:
            conn.execute(idx)
        conn.commit()

    def create_user(
        self,
        display_name: str,
        email_original: str,
        email_normalized: str,
        age: int,
        password_hash: str,
        password_algo: str,
        password_params: Optional[str] = None,
        avatar_blob: Optional[bytes] = None,
        avatar_mime: Optional[str] = None,
    ) -> Dict[str, Any]:
        init_db(self.db_path)
        user_id = str(uuid.uuid4())
        created_at = now_iso()
        updated_at = created_at
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._init_auth(conn)
            try:
                conn.execute(
                    """INSERT INTO users (id, display_name, email_original, email_normalized, age,
                                         password_hash, password_algo, password_params,
                                         avatar_blob, avatar_mime, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        user_id,
                        display_name.strip(),
                        email_original.strip(),
                        email_normalized,
                        int(age),
                        password_hash,
                        password_algo,
                        password_params,
                        avatar_blob,
                        avatar_mime,
                        created_at,
                        updated_at,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else {"id": user_id}

    def get_user_by_email_norm(self, email_normalized: str) -> Optional[Dict[str, Any]]:
        init_db(self.db_path)
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._init_auth(conn)
            cur = conn.execute("SELECT * FROM users WHERE email_normalized = ?", (email_normalized,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        init_db(self.db_path)
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._init_auth(conn)
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_profile(self, user_id: str, display_name: Optional[str] = None, age: Optional[int] = None, 
                        avatar_blob: Optional[bytes] = None, avatar_mime: Optional[str] = None,
                        clear_avatar: bool = False) -> Optional[Dict[str, Any]]:
        init_db(self.db_path)
        updated_at = now_iso()
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._init_auth(conn)
            fields = []
            params = []
            if display_name is not None:
                fields.append("display_name = ?")
                params.append(display_name.strip())
            if age is not None:
                fields.append("age = ?")
                params.append(int(age))
            if clear_avatar:
                fields.append("avatar_blob = NULL")
                fields.append("avatar_mime = NULL")
            elif avatar_blob is not None:
                fields.append("avatar_blob = ?")
                params.append(avatar_blob)
                if avatar_mime is not None:
                    fields.append("avatar_mime = ?")
                    params.append(avatar_mime)
            fields.append("updated_at = ?")
            params.append(updated_at)
            params.append(user_id)
            if not fields:
                cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cur.fetchone()
                return dict(row) if row else None
            sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
            conn.execute(sql, params)
            conn.commit()
            cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def update_password(self, user_id: str, password_hash: str, password_algo: str, password_params: Optional[str] = None) -> bool:
        init_db(self.db_path)
        updated_at = now_iso()
        with get_connection(self.db_path) as conn:
            self._init_auth(conn)
            cur = conn.execute(
                "UPDATE users SET password_hash=?, password_algo=?, password_params=?, updated_at=? WHERE id=?",
                (password_hash, password_algo, password_params, updated_at, user_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def revoke_user_sessions(self, user_id: str) -> int:
        init_db(self.db_path)
        now = now_iso()
        with get_connection(self.db_path) as conn:
            self._init_auth(conn)
            cur = conn.execute("UPDATE sessions SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL", (now, user_id))
            conn.commit()
            return cur.rowcount


class SessionRepository:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def create_session(self, user_id: str, ttl_days: int = 7) -> Tuple[str, str, str]:
        init_db(self.db_path)
        from aguia.auth.utils import generate_token
        session_id = str(uuid.uuid4())
        token = generate_token()
        t_hash = hash_token(token)
        csrf = generate_token()
        csrf_hash = hash_token(csrf)
        now = now_iso()
        expires = iso_from_dt(datetime.now(timezone.utc) + timedelta(days=ttl_days))
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            # ensure tables
            conn.execute(USERS_TABLE)
            conn.execute(SESSIONS_TABLE)
            for idx in AUTH_INDEXES:
                conn.execute(idx)
            conn.execute(
                """INSERT INTO sessions (id, user_id, token_hash, csrf_token_hash, created_at, expires_at, last_used_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (session_id, user_id, t_hash, csrf_hash, now, expires, now),
            )
            conn.commit()
        return token, csrf, expires

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        init_db(self.db_path)
        t_hash = hash_token(token)
        now = now_iso()
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                """SELECT s.*, u.display_name, u.email_original, u.email_normalized, u.age, u.avatar_mime
                   FROM sessions s
                   JOIN users u ON u.id = s.user_id
                   WHERE s.token_hash = ? AND s.revoked_at IS NULL""",
                (t_hash,),
            )
            row = cur.fetchone()
            if not row:
                return None
            # check expiry
            exp = row["expires_at"]
            # simple string compare works for Z format
            if exp < now:
                return None
            # update last used
            try:
                conn.execute("UPDATE sessions SET last_used_at = ? WHERE id = ?", (now, row["id"]))
                conn.commit()
            except Exception:
                pass
            return dict(row)

    def revoke_session(self, token: str) -> bool:
        if not token:
            return False
        init_db(self.db_path)
        t_hash = hash_token(token)
        now = now_iso()
        with get_connection(self.db_path) as conn:
            cur = conn.execute("UPDATE sessions SET revoked_at = ? WHERE token_hash = ?", (now, t_hash))
            conn.commit()
            return cur.rowcount > 0
