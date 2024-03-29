import logging
import os
import time
from http import HTTPStatus
from sys import stdout

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (EmptyResponseAPI, EnvironmentVariableMissing,
                        NotOkResponseStatusExeption, RequestError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка на присутствие обязательных переменных окружения."""
    must_have_tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missed_tokens = []
    for token, token_val in must_have_tokens.items():
        if not token_val:
            missed_tokens.append(token)

    if token in missed_tokens:
        tokens = ' '.join(missed_tokens)
        message = ('Отсустсвует обязательные '
                   f'переменные окружения {tokens}')
        logging.critical(message)
        raise EnvironmentVariableMissing(tokens)


def send_message(bot, message):
    """Отправка сообщения в телеграм-чат бота и пользователя."""
    logging.debug('Готовимся отправить сообщение в телеграм-чат')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение в телеграм-чат отправлено')

    except telegram.error.TelegramError as error:
        message = f'Сбой в отправке сообщения ботом: {error}'
        logging.error(message)


def get_api_answer(timestamp):
    """Отправка get запроса API, обработка полученного ответа."""
    payload = {'from_date': timestamp}

    request_kwargs = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': payload
    }

    message = 'Направляем запрос на {}, данные заголовка: {}, параметры: {}'
    logging.debug(message.format(*request_kwargs.values()))
    try:
        homework = requests.get(**request_kwargs)

        if homework.status_code != HTTPStatus.OK:
            raise NotOkResponseStatusExeption(homework.status_code)

        return homework.json()

    except requests.RequestException as error:
        raise RequestError(error)


def check_response(response):
    """Проверка полученного ответа на соответствие типам."""
    must_have_keys = ('homeworks', 'current_date')

    if not isinstance(response, dict):
        message = ('В ответе API структура данных не соответствует ожиданиям,'
                   'ожидался тип данных dict')
        raise TypeError(message)

    for key in must_have_keys:
        if key not in response:
            message = (f'Нет обязательных ключей в ответе API. {message}')
            raise EmptyResponseAPI(message)

    response_homeworks = response.get('homeworks')
    if not isinstance(response_homeworks, list):
        message = ('В ответе API под ключом "homeworks"'
                   ' данные приходят не в виде списка')
        raise TypeError(message)

    return response_homeworks


def parse_status(homework):
    """Обработка статуса полученной домашки."""
    status = homework.get('status')
    if not status:
        message = 'Отсутствует "status" ключ в домашке'
        raise KeyError(message)

    homework_name = homework.get('homework_name')
    if not homework_name:
        message = 'No "homework_name" key in homework'
        raise KeyError(message)

    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        message = f'Неизвестный HOMEWORK_VERDICTS ключ – {verdict}'
        raise KeyError(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    old_status = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
            else:
                message = 'Нет новых статусов'
            if message != old_status:
                old_status = message
                send_message(bot, message)
            timestamp = response.get('current_date', timestamp)
        except EmptyResponseAPI as error:
            logging.error(error)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error)
            if message != old_status:
                old_status = message
                send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s',
        stream=stdout
    )

    main()
