from supabase import create_client, Client
from .config import settings

_client: Client | None = None
_service_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def get_service_client() -> Client:
    """Service role client — usado no backend para escrita sem RLS."""
    global _service_client
    if _service_client is None:
        _service_client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
        )
    return _service_client
