from urllib.parse import quote_plus

def _norm(s: str) -> str:
    return " ".join((s or "").split()).strip()

def build_queries(item: dict) -> tuple[str, str]:
    """Return (shopee_query, google_query) in English.
    Shopee query: short. Google query: richer.
    """
    name = _norm(item.get("productDisplayName") or item.get("name") or "")
    gender = _norm(item.get("gender") or "")
    article = _norm(item.get("articleType") or item.get("type") or "")
    color = _norm(item.get("baseColour") or "")
    usage = _norm(item.get("usage") or "")

    shopee_parts = [article, gender, color]
    shopee_q = _norm(" ".join([p for p in shopee_parts if p]))

    google_parts = ["buy", article, gender, color, usage, name]
    google_q = _norm(" ".join([p for p in google_parts if p]))

    if not shopee_q:
        shopee_q = name or article or "fashion"
    if not google_q:
        google_q = shopee_q

    return shopee_q, google_q

def build_buy_links(item: dict) -> dict:
    shopee_q, google_q = build_queries(item)
    return {
        "shopee": f"https://shopee.vn/search?keyword={quote_plus(shopee_q)}",
        "google": f"https://www.google.com/search?q={quote_plus(google_q)}",
        "google_shopping": f"https://www.google.com/search?tbm=shop&q={quote_plus(google_q)}",
        "google_images": f"https://www.google.com/search?tbm=isch&q={quote_plus(google_q)}",
    }