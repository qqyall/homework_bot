import logging
import os
import time
from http import HTTPStatus
from sys import stdout

import requests
import telegram
from dotenv import load_dotenv

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
    for token, token_val in must_have_tokens.items():
        if not token_val:
            message = f'Отсустсвует обязательная переменная окружения {token}'
            logging.critical(message)
            raise Exception(message)


def send_message(bot, message):
    """Отправка сообщения в телеграм-чат бота и пользователя."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение в телеграм-чат отправлено')

    except Exception as error:
        message = f'Сбой в отправке сообщения ботом: {error}'
        logging.error(message)


def get_api_answer(timestamp):
    """Отправка get запроса API, обработка полученного ответа."""
    payload = {'from_date': timestamp}

    try:
        homework = requests.get(ENDPOINT, headers=HEADERS, params=payload)

        if homework.status_code == HTTPStatus.OK:
            return homework.json()

        elif homework.status_code == HTTPStatus.BAD_REQUEST:
            message = homework.error
            logging.error(message)
            raise Exception(message)

        elif homework.status_code == HTTPStatus.UNAUTHORIZED:
            message = f'{homework.code} {homework.message}'
            logging.error(message)
            raise Exception(message)

        elif homework.status_code == HTTPStatus.NOT_FOUND:
            message = f'Недоступность эндпоинта: {ENDPOINT}'
            logging.error(message)
            raise Exception(message)

        else:
            message = homework
            logging.error(message)
            raise Exception(message)

    except requests.RequestException as e:
        logging.error(e)


def check_response(response):
    """Проверка полученного ответа на соответствие типам."""
    must_have_keys = ('homeworks', 'current_date')

    if not isinstance(response, dict):
        message = ('В ответе API структура данных не соответствует ожиданиям,'
                   'ожидался тип данных dict')
        logging.error(message)
        raise TypeError(message)

    for key in must_have_keys:
        if key not in response:
            message = f'Нет ключа {key} в ответе API'
            logging.error('Нет обязательных ключей в ответе API. {message}')
            raise Exception(message)

    if not isinstance(response['homeworks'], list):
        message = ('В ответе API под ключом "homeworks"'
                   ' данные приходят не в виде списка')
        logging.error(message)
        raise TypeError(message)

    return True


def parse_status(homework):
    """Обработка статуса полученной домашки.
    Cоздание сообщения для отправки в телеграм-бота
    в соответствии с полученным статусом.
    """
    status = homework.get('status')
    if not status:
        message = 'Отсутствует "status" ключ в домашке'
        logging.error(message)
        raise Exception(message)

    verdict = HOMEWORK_VERDICTS.get(status)
    if verdict:
        homework_name = homework.get('homework_name')
        if not homework_name:
            message = 'No "homework_name" key in homework'
            logging.error(message)
            raise Exception(message)
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

    else:
        message = f'Неизвестный HOMEWORK_VERDICTS ключ – {verdict}'
        logging.error('Неизвестный статус проверки домашней работы. {message}')
        raise Exception(message)


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s',
        stream=stdout
    )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    check_tokens()

    while True:
        try:
            response = get_api_answer(timestamp)
            if check_response(response):
                for homework in response['homeworks']:
                    message = parse_status(homework)
                    send_message(bot, message)
            timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
