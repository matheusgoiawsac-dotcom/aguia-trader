"""Auth API endpoints."""

from __future__ import annotations

import json
from http.cookies import SimpleCookie
from typing import Any, Dict

from aguia.auth.service import AuthService
from aguia.server.auth_handlers import _get_session_token, set_session_cookie, clear_session_cookie, COOKIE_NAME


auth_service = AuthService()


def _read_json(handler) -> Dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length") or "0")
    except Exception:
        length = 0
    if length > 1024 * 1024:
        raise ValueError("Corpo muito grande")
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        raise ValueError("JSON inválido")


def handle_auth_register(handler):
    try:
        data = _read_json(handler)
        display_name = data.get("nome") or data.get("display_name") or data.get("name") or ""
        email = data.get("email") or ""
        age = data.get("idade") or data.get("age")
        birth_date = data.get("data_nascimento") or data.get("birth_date") or data.get("nascimento")
        password = data.get("senha") or data.get("password") or ""
        password2 = data.get("senha2") or data.get("password2") or ""
        if password2 and password != password2:
            handler._send_json({"sucesso": False, "erro": "As senhas não coincidem"}, status_code=400)
            return
        avatar_blob = None
        avatar_mime = None
        # avatar might be base64 in data.avatar
        avatar_b64 = data.get("avatar") or data.get("foto") or data.get("avatar_base64")
        if avatar_b64 and isinstance(avatar_b64, str):
            try:
                import base64
                if avatar_b64.startswith("data:"):
                    # data:mime;base64,...
                    header, b64data = avatar_b64.split(",", 1)
                    # extract mime
                    try:
                        mime_part = header.split(";")[0].replace("data:", "")
                        avatar_mime = mime_part or "image/jpeg"
                    except Exception:
                        avatar_mime = "image/jpeg"
                else:
                    b64data = avatar_b64
                    avatar_mime = data.get("avatar_mime") or "image/jpeg"
                avatar_blob = base64.b64decode(b64data)
            except Exception as e:
                handler._send_json({"sucesso": False, "erro": "Imagem inválida"}, status_code=400)
                return
        res = auth_service.register(display_name, email, age, password, avatar_blob=avatar_blob, avatar_mime=avatar_mime, birth_date=birth_date)
        # set cookie
        token = res.get("token")
        if token:
            handler.send_response(200)
            handler.send_header("Content-Type", "application/json; charset=utf-8")
            parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax"]
            handler.send_header("Set-Cookie", "; ".join(parts))
            handler.send_header("X-Content-Type-Options", "nosniff")
            handler.end_headers()
            body = json.dumps({"sucesso": True, "dados": {"user": res["user"], "expires_at": res.get("expires_at")}}, ensure_ascii=False).encode("utf-8")
            handler.wfile.write(body)
            return
        handler._send_json({"sucesso": True, "dados": {"user": res["user"]}})
    except ValueError as ve:
        handler._send_json({"sucesso": False, "erro": str(ve)}, status_code=400)
    except Exception as e:
        handler._send_json({"sucesso": False, "erro": "Erro ao cadastrar"}, status_code=500)


def handle_auth_login(handler):
    try:
        data = _read_json(handler)
        email = data.get("email") or ""
        password = data.get("senha") or data.get("password") or ""
        res = auth_service.login(email, password)
        token = res.get("token")
        if token:
            handler.send_response(200)
            handler.send_header("Content-Type", "application/json; charset=utf-8")
            parts = [f"{COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax"]
            handler.send_header("Set-Cookie", "; ".join(parts))
            handler.send_header("X-Content-Type-Options", "nosniff")
            handler.end_headers()
            body = json.dumps({"sucesso": True, "dados": {"user": res["user"], "expires_at": res.get("expires_at")}}, ensure_ascii=False).encode("utf-8")
            handler.wfile.write(body)
            return
        handler._send_json({"sucesso": True, "dados": {"user": res["user"]}})
    except ValueError as ve:
        handler._send_json({"sucesso": False, "erro": str(ve)}, status_code=401)
    except Exception as e:
        handler._send_json({"sucesso": False, "erro": "Erro ao entrar"}, status_code=500)


def handle_auth_me(handler):
    try:
        token = _get_session_token(handler)
        res = auth_service.get_current(token)
        if not res:
            handler._send_json({"sucesso": True, "dados": {"autenticado": False, "user": None}})
            return
        handler._send_json({"sucesso": True, "dados": {"autenticado": True, "user": res["user"]}})
    except Exception as e:
        handler._send_json({"sucesso": True, "dados": {"autenticado": False, "user": None}})


def handle_auth_logout(handler):
    try:
        token = _get_session_token(handler)
        if token:
            auth_service.logout(token)
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        parts = [f"{COOKIE_NAME}=", "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0"]
        handler.send_header("Set-Cookie", "; ".join(parts))
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.end_headers()
        body = json.dumps({"sucesso": True}, ensure_ascii=False).encode("utf-8")
        handler.wfile.write(body)
    except Exception as e:
        handler._send_json({"sucesso": True})


def handle_auth_update_profile(handler):
    try:
        token = _get_session_token(handler)
        data = _read_json(handler)
        display_name = data.get("nome") or data.get("display_name") or data.get("name")
        age = data.get("idade") or data.get("age")
        clear_avatar = bool(data.get("remover_foto") or data.get("clear_avatar"))
        avatar_blob = None
        avatar_mime = None
        avatar_b64 = data.get("avatar") or data.get("foto") or data.get("avatar_base64")
        if avatar_b64 and isinstance(avatar_b64, str) and not clear_avatar:
            try:
                import base64
                if avatar_b64.startswith("data:"):
                    header, b64data = avatar_b64.split(",", 1)
                    try:
                        mime_part = header.split(";")[0].replace("data:", "")
                        avatar_mime = mime_part or "image/jpeg"
                    except Exception:
                        avatar_mime = "image/jpeg"
                else:
                    b64data = avatar_b64
                    avatar_mime = data.get("avatar_mime") or "image/jpeg"
                avatar_blob = base64.b64decode(b64data)
            except Exception:
                handler._send_json({"sucesso": False, "erro": "Imagem inválida"}, status_code=400)
                return
        user = auth_service.update_profile(token, display_name=display_name, age=age,
                                           avatar_blob=avatar_blob, avatar_mime=avatar_mime,
                                           clear_avatar=clear_avatar)
        if user is None:
            handler._send_json({"sucesso": False, "erro": "Não autorizado"}, status_code=401)
            return
        handler._send_json({"sucesso": True, "dados": {"user": user}})
    except ValueError as ve:
        handler._send_json({"sucesso": False, "erro": str(ve)}, status_code=400)
    except Exception as e:
        handler._send_json({"sucesso": False, "erro": "Erro ao atualizar"}, status_code=500)


def handle_auth_change_password(handler):
    try:
        token = _get_session_token(handler)
        data = _read_json(handler)
        current = data.get("senha_atual") or data.get("current_password") or ""
        newp = data.get("nova_senha") or data.get("new_password") or ""
        newp2 = data.get("nova_senha2") or data.get("new_password2") or ""
        if newp2 and newp != newp2:
            handler._send_json({"sucesso": False, "erro": "As senhas não coincidem"}, status_code=400)
            return
        ok = auth_service.change_password(token, current, newp)
        if not ok:
            handler._send_json({"sucesso": False, "erro": "Não foi possível alterar a senha"}, status_code=400)
            return
        # revoke all sessions on password change -> clear cookie
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        parts = [f"{COOKIE_NAME}=", "Path=/", "HttpOnly", "SameSite=Lax", "Max-Age=0"]
        handler.send_header("Set-Cookie", "; ".join(parts))
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.end_headers()
        body = json.dumps({"sucesso": True}, ensure_ascii=False).encode("utf-8")
        handler.wfile.write(body)
    except ValueError as ve:
        handler._send_json({"sucesso": False, "erro": str(ve)}, status_code=400)
    except Exception as e:
        handler._send_json({"sucesso": False, "erro": "Erro ao alterar senha"}, status_code=500)


def handle_auth_avatar(handler, user_id: str):
    try:
        res = auth_service.get_avatar(user_id)
        if not res:
            handler.send_error(404)
            return
        blob, mime = res
        handler.send_response(200)
        handler.send_header("Content-Type", mime)
        handler.send_header("Content-Length", str(len(blob)))
        handler.send_header("Cache-Control", "private, max-age=300")
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(blob)
    except Exception:
        handler.send_error(404)
