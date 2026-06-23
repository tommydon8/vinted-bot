import requests
from config import API_URL, BASE_URL, HEADERS, VINTED_SESSION_COOKIE, PRICE_MIN, PRICE_MAX

_session = requests.Session()
_session.headers.update(HEADERS)
if VINTED_SESSION_COOKIE:
    _session.cookies.set("_vinted_fr_session", VINTED_SESSION_COOKIE)


def _refresh_csrf() -> None:
    try:
        _session.get(BASE_URL, timeout=15)
    except Exception:
        pass


def search_items(brand_ids: list[int]) -> list[dict]:
    _refresh_csrf()
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

    resp = _session.get(f"{API_URL}/catalog/items", params=params, timeout=20)
    if resp.status_code == 401:
        raise PermissionError("Cookie Vinted scaduto o mancante.")
    resp.raise_for_status()
    return resp.json().get("items", [])


def search_brands(query: str) -> list[dict]:
    resp = _session.get(
        f"{API_URL}/brands",
        params={"q": query, "limit": 10},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("brands", [])
