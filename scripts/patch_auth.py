from pathlib import Path

path = Path("aguia/server/handler.py")
content = path.read_text(encoding="utf-8")

# Add imports
imp = """from aguia.server.auth_api import (
    handle_auth_register,
    handle_auth_login,
    handle_auth_me,
    handle_auth_logout,
    handle_auth_update_profile,
    handle_auth_change_password,
    handle_auth_avatar,
)
"""

if "handle_auth_register" not in content:
    marker = "from aguia.server.routes import (\n    handle_api_status,\n    handle_api_status_ollama,\n    handle_api_acoes,\n    handle_api_analise,\n    handle_api_dados,\n    handle_api_modos,\n    handle_api_estrategia_macro_jr,\n)\n"
    if marker in content:
        content = content.replace(marker, marker + imp)

# Add routes in _route
old_route = """    def _route(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            try:
                if path == "/api/status":"""
new_route = """    def _route(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # Auth routes
        if path == "/api/auth/me":
            return handle_auth_me(self)
        if path.startswith("/api/auth/avatar/"):
            # /api/auth/avatar/<user_id>
            try:
                uid = path.split("/api/auth/avatar/")[-1].strip("/")
                return handle_auth_avatar(self, uid)
            except Exception:
                pass
        if path.startswith("/api/"):
            try:
                if path == "/api/status":"""

if '"/api/auth/me"' not in content:
    content = content.replace(old_route, new_route)

# Add POST routes
old_post_route = """    def _route_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            try:
                if path == "/api/update-strategy":"""
new_post_route = """    def _route_post(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # Auth POST routes
        if path == "/api/auth/register":
            return handle_auth_register(self)
        if path == "/api/auth/login":
            return handle_auth_login(self)
        if path == "/api/auth/logout":
            return handle_auth_logout(self)
        if path == "/api/auth/update":
            return handle_auth_update_profile(self)
        if path == "/api/auth/change-password":
            return handle_auth_change_password(self)

        if path.startswith("/api/"):
            try:
                if path == "/api/update-strategy":"""

if '"/api/auth/register"' not in content:
    content = content.replace(old_post_route, new_post_route)

path.write_text(content, encoding="utf-8")
print("done")
