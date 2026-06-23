import requests
import logging
from config import API_URL, BASE_URL, HEADERS, VINTED_SESSION_COOKIE, PRICE_MIN, PRICE_MAX

logger = logging.getLogger(__name__)


class _VintedClient:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._ready = False

    def _init(self):
        if self._ready:
            return
        try:
            self._session.get(BASE_URL, timeout=15)
        except Exception as e:
            logger.warning(f"Init session: {e}")

        try:
            resp = self._session.post(
                f"{BASE_URL}/oauth/token",
                data={"grant_type": "client_credentials", "client_id": "web", "scope": "public"},
                timeout=15,
            )
            if resp.ok:
                token = resp.json().get("access_token")
                if token:
                    self._session.headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            logger.warning(f"OAuth fallito: {e}")

        if VINTED_SESSION_COOKIE:
            for part in VINTED_SESSION_COOKIE.split(";"):
                part = part.strip()
                if "=" in part:
                    name, _, value = part.partition("=")
                    self._session.cookies.set(name.strip(), value.strip())

        self._ready = True

    def get(self, url: str, **kwargs) -> requests.Response:
        self._init()
        return self._session.get(url, **kwargs)


_client = _VintedClient()


def search_items_by_brand_name(brand_name: str) -> list[dict]:
    """Cerca articoli per nome brand usando ricerca testuale."""
    resp = _client.get(
        f"{API_URL}/catalog/items",
        params={
            "search_text": brand_name,
            "price_from": PRICE_MIN,
            "price_to": PRICE_MAX,
            "currency": "EUR",
            "order": "newest_first",
            "per_page": 48,
            "page": 1,
        },
        timeout=20,
    )
    if resp.status_code == 401:
        raise PermissionError("Autenticazione Vinted fallita.")
    resp.raise_for_status()
    return resp.json().get("items", [])


def search_items(brand_ids: list[int]) -> list[dict]:
    """Mantenu per compatibilità — non usata attivamente."""
    return []
