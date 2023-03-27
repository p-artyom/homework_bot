import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from requests.exceptions import RequestException

import exceptions

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
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

ENV_VARIABLES = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

HOMEWORK_KEYS = [
    'homeworks',
    'current_date',
]

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s',
)


def check_tokens() -> None:
    """Проверяет доступность переменных."""
    for variable in ENV_VARIABLES:
        if os.getenv(variable) is None:
            logging.critical('Отсутствуют обязательные переменные окружения.')
            sys.exit()
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствуют обязательные переменные окружения.')
        sys.exit()


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.

    Args:
        bot (telegram.Bot): Экземпляр класса Bot.
        message (str): Cтрока с текстом сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Удачная отправка сообщения "{message}" в Telegram.')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}.')


def get_api_answer(timestamp: int) -> dict:
    """Выполняет запрос к API сервиса Практикум.Домашка.

    Args:
        timestamp (int): Временная метка в формате Unix time.

    Returns:
        Ответ API, приведенный к типам данных Python.
    """
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={
                'from_date': timestamp,
            },
        )
        if response.status_code != HTTPStatus.OK:
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                raise exceptions.HTTPException('Ошибка авторизации.')
            if response.status_code == HTTPStatus.BAD_REQUEST:
                raise exceptions.HTTPException(
                    'Ошибка запроса к API сервиса Практикум.Домашка.',
                )
            raise exceptions.HTTPException(
                'Некорректный ответ от API сервиса Практикум.Домашка.',
            )
        if (
            'code' in response.json().keys()
            and response['code'].json() == 'UnknownError'
        ):
            logging.error(
                f'В качестве параметра `from_date` передано `{timestamp}`. '
                'API такого не ожидает!',
            )
        elif (
            'code' in response.json().keys()
            and response['code'].json() == 'not_authenticated'
        ):
            logging.error(
                'Запрос выполнен с недействительным или некорректным токеном.',
            )
        return response.json()
    except RequestException as error:
        logging.error(
            'Сбой при отправке запроса к API сервиса Практикум.Домашка.',
        )
        raise exceptions.PracticumAPIRequestError(
            'Неоднозначное исключение во время обработки запроса.',
        ) from error


def check_response(response: dict) -> dict:
    """Проверяет ответ API на соответствие документации.

    Args:
        response (dict): Ответ API, приведенный к типам данных Python.

    Returns:
        Ответ API, который соответствует документации.
    """
    if not isinstance(response, dict):
        raise TypeError(
            'Невалидный тип ответа от API сервиса Практикум.Домашка.',
        )
    if 'homeworks' not in response:
        raise KeyError(
            'Невалидный формат ответа от сервиса Практикум.Домашка, '
            'отсутствует необходимый ключ `homeworks`',
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Невалидный тип ответа от API сервиса Практикум.Домашка, '
            'ключ `homeworks` должен быть списком.',
        )
    if set(response.keys()) != set(HOMEWORK_KEYS):
        logging.error('Отсутствуют ожидаемые ключи в ответе API.')
        raise exceptions.InvalidResponseKey(
            'Ответ не соответствует документации.',
        )
    return response['homeworks'][0]


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    Args:
        homework (dict): Последний элемент из списка домашних работ.

    Returns:
        Сообщение, которое содержит информацию работы и её статус.
    """
    try:
        if homework['status'] not in HOMEWORK_VERDICTS.keys():
            logging.error(
                'Неожиданный статус домашней работы, обнаруженный '
                'в ответе API.',
            )
            raise exceptions.InvalidHomeworkKey(
                'Статус не соответствует ожидаемым.',
            )
        return (
            'Изменился статус проверки работы "'
            + homework['homework_name']
            + '". '
            + HOMEWORK_VERDICTS[homework['status']]
        )
    except (KeyError, TypeError) as error:
        raise exceptions.InvalidInputDataError(
            'Ключ или тип данных не соответствует ожидаемым.',
        ) from error


def main() -> None:
    """Основная логика работы бота-ассистента."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            if response:
                send_message(bot, parse_status(check_response(response)))
            else:
                logging.debug('Новых статусов нет.')
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = int(time.time())


if __name__ == '__main__':
    main()
