import os
import time
import requests
from dotenv import load_dotenv
import telegram
import logging


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    ...


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)
    


def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    
    # may be here check for response.status_code 200 400 401

    return homework_statuses.json()

def check_response(response):
    must_have_keys = ('homeworks', 'current_date')
    for key in must_have_keys:
        if key not in response:
            raise Exception(f'No key {key} in response')
    return True


def parse_status(homework):
    verdict = HOMEWORK_VERDICTS.get(homework.get('status'))
    if verdict:
        homework_name = homework.get('homework_name')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return None

def main():
    """Основная логика работы бота."""

    # logging

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    
    check_tokens()

    while True:
        try:
            response = get_api_answer(timestamp)
            if check_response(response):
                for homework in response['homeworks']:
                    message = parse_status(homework)
                    if message:
                        send_message(bot, message)
            timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
