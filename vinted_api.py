import requests
import logging
from config import API_URL, BASE_URL, HEADERS, VINTED_SESSION_COOKIE, VINTED_EMAIL, VINTED_PASSWORD, PRICE_MIN, PRICE_MAX

logger = logging.getLogger(__name__)


class _VintedClient:
    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._ready = False

    def _login(self) -> bool:
        """Tenta il login con email e password per ottenere un token."""
        if not VINTED_EMAIL or not VINTED_PASSWORD:
            return False
        try:
            # Prima visita la homepage per ottenere i cookie iniziali
            self._session.get(BASE_URL, timeout=15)

            resp = self._session.post(
                f"{BASE_URL}/oauth/token",
                data={
                    "grant_type": "password",
                    "username": VINTED_EMAIL,
                    "password": VINTED_PASSWORD,
                    "client_id": "web",
                    "scope": "user:*",
                },
                timeout=15,
            )
            if resp.ok:
                token = resp.json().get("access_token")
                if token:
                    self._session.headers["Authorization"] = f"Bearer {token}"
                    logger.info("Login Vinted riuscito con email/password")
                    return True
        except Exception as e:
            logger.warning(f"Login fallito: {e}")
        return False

    def _init(self):
        if self._ready:
            return

        # Prima prova il login con credenziali
        logged_in = self._login()

        if not logged_in:
            # Fallback: sessione anonima + cookie manuale
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
                logger.warning(f"OAuth anonimo fallito: {e}")

            if VINTED_SESSION_COOKIE:
                for part in VINTED_SESSION_COOKIE.split(";"):
                    part = part.strip()
                    if "=" in part:
                        name, _, value = part.partition("=")
                        self._session.cookies.set(name.strip(), value.strip())

        self._ready = True

    def _reset(self):
        """Resetta la sessione e riprova il login."""
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._ready = False

    def get(self, url: str, **kwargs) -> requests.Response:
        self._init()
        resp = self._session.get(url, **kwargs)

        # Se scade la sessione, ri-autentica automaticamente e riprova
        if resp.status_code == 401:
            logger.info("Sessione scaduta — ri-autenticazione in corso...")
            self._reset()
            self._init()
            resp = self._session.get(url, **kwargs)

        return resp


_client = _VintedClient()


def search_items_by_brand_name(brand_name: str) -> list[dict]:
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
    return []
