import hashlib
import hmac
import os
import time
import urllib.parse

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TTL = int(os.getenv("INIT_DATA_TTL_SECONDS", "86400"))


class TMAValidationError(Exception): ...


class TMATokenExpired(TMAValidationError): ...


def parse_init_data(init_data_raw: str) -> dict:
    return dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))


def build_data_check_string(pairs: dict) -> str:
    items = []
    for k, v in pairs.items():
        if k in ("hash", "signature"):
            continue
        items.append(f"{k}={v}")
    items.sort()
    return "\n".join(items)


def compute_secret_key(bot_token: str) -> bytes:
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def compute_hash(dcs: str, secret_key: bytes) -> str:
    return hmac.new(secret_key, dcs.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_init_data(init_data_raw: str, max_age_seconds: int = TTL) -> dict:
    if not BOT_TOKEN:
        raise TMAValidationError("BOT_TOKEN not configured")
    pairs = parse_init_data(init_data_raw)
    received_hash = pairs.get("hash")
    if not received_hash:
        raise TMAValidationError("Missing hash")
    dcs = build_data_check_string(pairs)
    secret_key = compute_secret_key(BOT_TOKEN)
    expected_hash = compute_hash(dcs, secret_key)
    if not hmac.compare_digest(received_hash, expected_hash):
        raise TMAValidationError("Invalid hash")
    auth_date = int(pairs.get("auth_date", "0"))
    if auth_date and max_age_seconds > 0 and int(time.time()) - auth_date > max_age_seconds:
        raise TMATokenExpired("InitData expired")
    return pairs


def check_telegram_auth(init_data: str) -> bool:
    """
    Проверяет корректность init_data из Telegram Mini App.
    """
    parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

    received_hash = parsed_data.pop('hash', None)
    if not received_hash:
        return False

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(received_hash, computed_hash)
