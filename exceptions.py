class EmptyResponseAPI(Exception):
    """Исключение при возникновении проблем с получением ответа."""

    def __init__(self, response):
        self.msg = f'Неверный формат ответа API.\n{response}'

    def __str__(self):
        return self.msg


class EnvironmentVariableMissing(Exception):
    """Исключение в случае отсустсвия обязательной переменная окружения."""

    def __init__(self, token):
        self.msg = f'Отсустсвует обязательной переменная окружения {token}'

    def __str__(self):
        return self.msg


class BadRequestExeption(Exception):
    """Получен ответ с кодом 400."""


class UnauthorizedExeption(Exception):
    """Получен ответ с кодом 401."""


class NotFoundExeption(Exception):
    """Получен ответ с кодом 404."""


class RequestError(Exception):
    """Исключение при возникновении проблем отправкой запросов"""

    def __init__(self, error):
        self.msg = f'Во время отправления запроса возникла ошибка.\n{error}'

    def __str__(self):
        return self.msg
