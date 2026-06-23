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
        # Visita la homepage per ottenere cookie anonimi (anon_id, CSRF, ecc.)
        try:
            self._session.get(BASE_URL, timeout=15)
        except Exception as e:
            logger.warning(f"Init session: {e}")

        # Prova a ottenere un token OAuth anonimo
        try:
            resp = self._session.post(
                f"{BASE_URL}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "web",
                    "scope": "public",
                },
                timeout=15,
            )
            if resp.ok:
                token = resp.json().get("access_token")
                if token:
                    self._session.headers["Authorization"] = f"Bearer {token}"
                    logger.info("Token OAuth anonimo ottenuto")
        except Exception as e:
            logger.warning(f"OAuth fallito: {e}")

        # Aggiungi i cookie dell'utente se presenti (hanno priorità)
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


def search_items(brand_ids: list[int]) -> list[dict]:
    params: dict = {
        "price_from": PRICE_MIN,
        "price_to": PRICE_MAX,
        "currency": "EUR",
        "order": "newest_first",
        "per_page": 96,
        "page": 1,
    }
    for bid in brand_ids:
        params.setdefault("brand_ids[]", [])
        if isinstance(params["brand_ids[]"], list):
            params["brand_ids[]"].append(bid)

    resp = _client.get(f"{API_URL}/catalog/items", params=params, timeout=20)
    if resp.status_code == 401:
        raise PermissionError("Autenticazione Vinted fallita.")
    resp.raise_for_status()
    return resp.json().get("items", [])


def search_brands(query: str) -> list[dict]:
    resp = _client.get(
        f"{API_URL}/brands",
        params={"q": query, "limit": 10},
        timeout=15,
    )
    if resp.status_code == 401:
        raise PermissionError("Autenticazione Vinted fallita.")
    resp.raise_for_status()
    return resp.json().get("brands", [])
