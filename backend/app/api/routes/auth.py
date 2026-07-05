from fastapi import APIRouter, HTTPException, status
from ...core.auth import create_access_token, hash_password, verify_password
from ...core.config import settings
from ...schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Hash da senha padrão gerado em runtime na primeira chamada
_admin_hash: str | None = None


def _get_admin_hash() -> str:
    global _admin_hash
    if _admin_hash is None:
        _admin_hash = hash_password(settings.ADMIN_PASSWORD)
    return _admin_hash


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not verify_password(body.password, _get_admin_hash()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )
    token = create_access_token({"sub": "admin", "perfil": "admin"})
    return TokenResponse(access_token=token)


@router.get("/me")
def me(user: dict = None):
    from ...core.auth import get_current_user
    from fastapi import Depends
    return {"usuario": user.get("sub"), "perfil": user.get("perfil")}
