from http import HTTPStatus


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


class NotOkResponseStatusExeption(Exception):
    """Получен ответ с кодом, отличным от 200"""

    excepted_status = HTTPStatus.OK
    
    def __init__(self, got_status):
        self.msg = (f'При отправке запроса к API '
                    f'ожидался статус {self.excepted_status}\n'
                    f'Получен статус {got_status}')

    def __str__(self):
        return self.msg


class RequestError(Exception):
    """Исключение при возникновении проблем отправкой запросов"""

    def __init__(self, error):
        self.msg = f'Во время отправления запроса возникла ошибка.\n{error}'

    def __str__(self):
        return self.msg
