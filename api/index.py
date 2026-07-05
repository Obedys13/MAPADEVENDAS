import sys
import os

# Torna o diretório backend/ importável como pacote "app.*"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app as _fastapi_app  # noqa: E402


class _StripApiPrefix:
    """Remove /api do path antes de passar ao FastAPI.

    Vercel roteia /api/* para esta função, mas o FastAPI registra
    as rotas sem esse prefixo (/auth/login, /uploads/..., etc.).
    """

    def __init__(self, asgi_app, prefix: str = "/api"):
        self._app = asgi_app
        self._prefix = prefix

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path: str = scope.get("path", "/")
            if path.startswith(self._prefix):
                stripped = path[len(self._prefix):] or "/"
                scope = {**scope, "path": stripped, "raw_path": stripped.encode()}
        await self._app(scope, receive, send)


# Vercel chama o objeto chamado "app" neste arquivo
app = _StripApiPrefix(_fastapi_app)
