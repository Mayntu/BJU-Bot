from urllib.parse import parse_qs

def parse_utm_source(start_param: str) -> str:
    """
    Получает только utm_source из строки после /start
    Пример: /start utm_source=telegram&utm_campaign=123

    :return: Строка utm_source
    """

    try:
        parsed : dict = parse_qs(start_param)
        return parsed.get("utm_source", [""])[0]
    except Exception:
        return ""