import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl, unquote
from typing import Tuple, Dict


# Telegram bot token (обязательно токен именно того бота, который открыл Mini App)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# Исключения
class TMAValidationError(Exception):
    pass


class TMATokenExpired(Exception):
    pass


def _pick_validation_payload(raw: str) -> str:
    """
    Выбирает корректную строку для проверки подписи.

    Варианты входа:
    1) "Чистый" initData (например, то, что приходит из JS: window.Telegram.WebApp.initData),
       содержит пары вида user=...&auth_date=...&hash=...
    2) Полная query-строка открытия Mini App с параметром tgWebAppData=..., где внутри лежит (1).

    Возвращает строку формата (1), по которой и нужно считать hash.
    """
    # Быстрая эвристика: если строка уже содержит &hash= на верхнем уровне — это initData.
    if "hash=" in raw and "tgWebAppData=" not in raw:
        return raw

    # Иначе попробуем распарсить верхний уровень и достать tgWebAppData.
    outer = dict(parse_qsl(raw, keep_blank_values=True))
    if "hash" in outer:
        # На случай, если initData перемешан с другими tgWebApp* полями
        # (редко, но встречается): валидация должна идти по тем ключам, где есть hash.
        return raw

    tgwad = outer.get("tgWebAppData")
    if tgwad:
        # Внутри один раз декодируем и используем это как initData
        return unquote(tgwad)

    # Попытка: возможно, нам сразу прислали initData, но вперемешку с другими полями без tgWebAppData.
    # Если внутри все-таки есть hash (как подстрока), вернем как есть.
    # Иначе считаем, что данных недостаточно.
    if "hash=" in raw:
        return raw

    raise TMAValidationError("Cannot find initData or tgWebAppData with hash")


def _build_data_check_string(params: Dict[str, str]) -> str:
    """
    Собирает data_check_string: пары key=value, отсортированные по ключу и
    соединённые символом перевода строки.
    """
    return "\n".join(f"{k}={v}" for k, v in sorted(params.items()))


def _calc_hash(data_check_string: str, bot_token: str) -> str:
    """
    Вычисляет контрольный хэш по правилам Telegram:
      secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
      hash = HMAC_SHA256(key=secret_key, msg=data_check_string).hexdigest()
    """
    if not bot_token:
        raise TMAValidationError("TELEGRAM_TOKEN is not set")

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def check_validate_init_data(raw: str, bot_token: str) -> bool:
    """
    Проверяет подпись initData.
    Поддерживает как «чистый» initData, так и обёртку с tgWebAppData=...
    """
    payload = _pick_validation_payload(raw)
    params = dict(parse_qsl(payload, keep_blank_values=True))

    received_hash = params.pop("hash", None)
    if not received_hash:
        return False

    data_check_string = _build_data_check_string(params)
    calculated_hash = _calc_hash(data_check_string, bot_token)

    # Используем сравнение с защитой от таймингов
    return hmac.compare_digest(calculated_hash, received_hash)


def parse_init_data(raw: str) -> Dict:
    """
    Универсальный парсер initData (и/или полной query-строки с tgWebAppData).
    На выходе словарь со всеми полями, где user — dict (если парсится).
    """
    result = {}

    # Разберём верхний уровень (на случай, если пригодится tgWebApp* и пр.)
    outer = dict(parse_qsl(raw, keep_blank_values=True))
    result.update(outer)

    # Если есть tgWebAppData — раскроем его внутрь
    if "tgWebAppData" in outer:
        inner = unquote(outer["tgWebAppData"])
        inner_params = dict(parse_qsl(inner, keep_blank_values=True))
        result.update(inner_params)
        result.pop("tgWebAppData", None)

    # Если user есть и он строка JSON — распарсим
    if "user" in result and isinstance(result["user"], str):
        try:
            result["user"] = json.loads(result["user"])
        except json.JSONDecodeError:
            pass

    return result


def extract_user_from_init_data(init_data_raw: str) -> Dict:
    """
    Полный цикл:
      1) Проверка подписи.
      2) Парсинг данных (user -> dict).
      3) Проверка истечения срока (24 часа).
      4) Возврат user.
    """
    if not check_validate_init_data(init_data_raw, TELEGRAM_TOKEN):
        raise TMAValidationError("Invalid hash")

    data = parse_init_data(init_data_raw)

    # auth_date может лежать как во "внутренней", так и во "внешней" части.
    auth_date_str = str(data.get("auth_date", "0"))
    try:
        auth_date = int(auth_date_str)
    except ValueError:
        auth_date = 0

    # 24 часа = 86400 секунд
    if int(time.time()) - auth_date > 86400:
        raise TMATokenExpired("Token expired")

    user = data.get("user")
    if user is None:
        raise TMAValidationError("Missing user data")

    # На всякий случай, если не распарсился
    if isinstance(user, str):
        user = json.loads(user)

    if not isinstance(user, dict):
        raise TMAValidationError("User data is malformed")

    return user
