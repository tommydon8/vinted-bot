import requests
from config import API_URL, BASE_URL, HEADERS, VINTED_SESSION_COOKIE, PRICE_MIN, PRICE_MAX


def _get_headers() -> dict:
    h = dict(HEADERS)
    if VINTED_SESSION_COOKIE:
        h["Cookie"] = VINTED_SESSION_COOKIE
    return h


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

    resp = requests.get(
        f"{API_URL}/catalog/items",
        params=params,
        headers=_get_headers(),
        timeout=20,
    )
    if resp.status_code == 401:
        raise PermissionError("Cookie Vinted scaduto o mancante.")
    resp.raise_for_status()
    return resp.json().get("items", [])


def search_brands(query: str) -> list[dict]:
    resp = requests.get(
        f"{API_URL}/brands",
        params={"q": query, "limit": 10},
        headers=_get_headers(),
        timeout=15,
    )
    if resp.status_code == 401:
        raise PermissionError("Cookie Vinted scaduto o mancante.")
    resp.raise_for_status()
    return resp.json().get("brands", [])
