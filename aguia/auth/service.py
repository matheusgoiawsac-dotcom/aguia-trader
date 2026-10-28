"""Auth service."""

from __future__ import annotations

import io
from typing import Any, Dict, Optional

from aguia.auth.password import PasswordHasher
from aguia.auth.repo import UserRepository, SessionRepository
from aguia.auth.utils import normalize_email, validate_email, now_iso


ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_BYTES = 1024 * 1024  # 1MB


class AuthService:
    def __init__(self, db_path=None):
        self.users = UserRepository(db_path)
        self.sessions = SessionRepository(db_path)
        self.hasher = PasswordHasher()

    def register(self, display_name: str, email: str, age: int = None, password: str = "", 
                 avatar_blob: Optional[bytes] = None, avatar_mime: Optional[str] = None,
                 birth_date: str = None) -> Dict[str, Any]:
        if not display_name or not display_name.strip():
            raise ValueError("Nome inválido")
        if not validate_email(email):
            raise ValueError("E-mail inválido")
        calculated_age = None
        if birth_date:
            try:
                from datetime import date
                bd = birth_date.strip()
                if len(bd) == 10 and bd[4] == '-' and bd[7] == '-':
                    y, m, d = bd.split('-')
                    nasc = date(int(y), int(m), int(d))
                elif '/' in bd:
                    parts = bd.split('/')
                    if len(parts) == 3:
                        d, m, y = parts[0], parts[1], parts[2]
                        nasc = date(int(y), int(m), int(d))
                    else:
                        raise ValueError("Data inválida")
                else:
                    raise ValueError("Data inválida")
                hoje = date.today()
                if nasc > hoje:
                    raise ValueError("Data inválida")
                calculated_age = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
            except ValueError:
                raise ValueError("Data inválida")
            except Exception:
                raise ValueError("Data inválida")
        if age is not None and birth_date is None:
            try:
                calculated_age = int(age)
            except Exception:
                raise ValueError("Idade inválida")
        if calculated_age is None and age is not None:
            try:
                calculated_age = int(age)
            except Exception:
                raise ValueError("Idade inválida")
        if calculated_age is None:
            raise ValueError("Idade inválida")
        if calculated_age < 0 or calculated_age > 120:
            raise ValueError("Idade inválida")
        if not password or len(password) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        if len(password) > 256:
            raise ValueError("Senha muito longa")
        if avatar_blob is not None:
            if len(avatar_blob) > MAX_AVATAR_BYTES:
                raise ValueError("Imagem muito grande")
            if avatar_mime not in ALLOWED_IMAGE_MIMES:
                raise ValueError("Formato de imagem não suportado")
        email_norm = normalize_email(email)
        existing = self.users.get_user_by_email_norm(email_norm)
        if existing:
            raise ValueError("E-mail já cadastrado")
        pwd_hash, pwd_algo, pwd_params = self.hasher.hash_password(password)
        user = self.users.create_user(
            display_name=display_name,
            email_original=email.strip(),
            email_normalized=email_norm,
            age=int(calculated_age),
            password_hash=pwd_hash,
            password_algo=pwd_algo,
            password_params=pwd_params,
            avatar_blob=avatar_blob,
            avatar_mime=avatar_mime,
        )
        token, csrf, expires = self.sessions.create_session(user["id"])
        # remove sensitive
        user_out = dict(user)
        user_out.pop("password_hash", None)
        user_out.pop("password_params", None)
        user_out.pop("avatar_blob", None)
        return {"user": user_out, "token": token, "csrf_token": csrf, "expires_at": expires}

    def login(self, email: str, password: str) -> Dict[str, Any]:
        if not validate_email(email):
            raise ValueError("E-mail ou senha inválidos")
        email_norm = normalize_email(email)
        user = self.users.get_user_by_email_norm(email_norm)
        if not user:
            raise ValueError("E-mail ou senha inválidos")
        if not self.hasher.verify_password(password, user.get("password_hash", ""), user.get("password_algo", "argon2id")):
            raise ValueError("E-mail ou senha inválidos")
        token, csrf, expires = self.sessions.create_session(user["id"])
        user_out = dict(user)
        user_out.pop("password_hash", None)
        user_out.pop("password_params", None)
        user_out.pop("avatar_blob", None)
        return {"user": user_out, "token": token, "csrf_token": csrf, "expires_at": expires}

    def get_current(self, token: str) -> Optional[Dict[str, Any]]:
        sess = self.sessions.validate_session(token)
        if not sess:
            return None
        user = self.users.get_user_by_id(sess["user_id"])
        if not user:
            return None
        user_out = dict(user)
        user_out.pop("password_hash", None)
        user_out.pop("password_params", None)
        user_out.pop("avatar_blob", None)
        return {"user": user_out, "session": sess}

    def logout(self, token: str) -> bool:
        return self.sessions.revoke_session(token)

    def update_profile(self, token: str, display_name: Optional[str] = None, age: Optional[int] = None,
                       avatar_blob: Optional[bytes] = None, avatar_mime: Optional[str] = None,
                       clear_avatar: bool = False) -> Optional[Dict[str, Any]]:
        sess = self.sessions.validate_session(token)
        if not sess:
            return None
        user_id = sess["user_id"]
        if age is not None and (int(age) < 0 or int(age) > 120):
            raise ValueError("Idade inválida")
        if avatar_blob is not None:
            if len(avatar_blob) > MAX_AVATAR_BYTES:
                raise ValueError("Imagem muito grande")
            if avatar_mime not in ALLOWED_IMAGE_MIMES:
                raise ValueError("Formato de imagem não suportado")
        user = self.users.update_profile(user_id, display_name=display_name, age=age,
                                         avatar_blob=avatar_blob, avatar_mime=avatar_mime,
                                         clear_avatar=clear_avatar)
        if not user:
            return None
        user_out = dict(user)
        user_out.pop("password_hash", None)
        user_out.pop("password_params", None)
        user_out.pop("avatar_blob", None)
        return user_out

    def change_password(self, token: str, current_password: str, new_password: str) -> bool:
        sess = self.sessions.validate_session(token)
        if not sess:
            return False
        user = self.users.get_user_by_id(sess["user_id"])
        if not user:
            return False
        if not self.hasher.verify_password(current_password, user.get("password_hash", ""), user.get("password_algo", "argon2id")):
            raise ValueError("Senha atual inválida")
        if not new_password or len(new_password) < 8 or len(new_password) > 256:
            raise ValueError("Nova senha inválida")
        pwd_hash, pwd_algo, pwd_params = self.hasher.hash_password(new_password)
        ok = self.users.update_password(user["id"], pwd_hash, pwd_algo, pwd_params)
        if ok:
            self.users.revoke_user_sessions(user["id"])
        return ok

    def get_avatar(self, user_id: str) -> Optional[tuple]:
        user = self.users.get_user_by_id(user_id)
        if not user:
            return None
        blob = user.get("avatar_blob")
        if not blob:
            return None
        mime = user.get("avatar_mime") or "image/jpeg"
        return (blob, mime)
