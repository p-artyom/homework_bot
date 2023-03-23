import logging
import os
import sys
import time
from pprint import pprint

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s',
)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENV_VARS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens() -> None:
    """Проверяет доступность переменных."""
    for var in ENV_VARS:
        if os.getenv(var) is None:
            logging.critical('Отсутствуют обязательные переменные окружения')
            sys.exit()


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.

    Args:
        bot (): .
        message (): .
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Удачная отправка сообщения "{message}" в Telegram')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Выполняет запрос к API сервиса Практикум.Домашка.

    Args:
        timestamp (int): Временная метка в формате Unix time.

    Returns:
        Ответ API, приведенный к типам данных Python.
    """
    try:
        homeworks = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={
                'from_date': timestamp,
            },
        ).json()
        if 'code' in homeworks.keys() and homeworks['code'] == 'UnknownError':
            logging.error(
                f'В качестве параметра `from_date` передано `{timestamp}`. '
                'API такого не ожидает!',
            )
        elif (
            'code' in homeworks.keys()
            and homeworks['code'] == 'not_authenticated'
        ):
            logging.error(
                'Запрос выполнен с недействительным или некорректным токеном.',
            )
        return homeworks
    except Exception as error:
        logging.error(
            'Сбой при отправке запроса к API сервиса Практикум.Домашка: '
            f'{error}',
        )


def check_response(response: dict) -> None:
    """Проверяет ответ API на соответствие документации.

    Args:
        response (dict): .

    Returns:
        .
    """
    ...
    # отсутствие ожидаемых ключей в ответе API (уровень ERROR);


def parse_status(homework) -> None:
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    Args:
        homework (): .

    Returns:
        .
    """
    ...
    # неожиданный статус домашней работы, обнаруженный в ответе API (уровень ERROR);
    # отсутствие в ответе новых статусов (уровень DEBUG).

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота-ассистента."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    timestamp = 0
    # while True:
    #     try:
    response = get_api_answer(timestamp)
    pprint(response)
    homework = check_response(response)
    #         parse_status(homework)
    #         send_message(bot, message)
    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'
    #         ...
    #     ...


if __name__ == '__main__':
    main()
