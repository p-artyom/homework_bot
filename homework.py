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
RETRY_PERIOD = 6
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s',
)


def check_tokens() -> bool:
    """Проверяет доступность переменных.

    Returns:
        Значение True, если все необходимые переменные окружения доступны,
        в противном случае False.
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.

    Args:
        bot (telegram.Bot): Экземпляр класса Bot.
        message (str): Cтрока с текстом сообщения.
    """
    try:
        logging.debug(
            f'Запущен процесс отправки сообщения "{message}" в Telegram.',
        )
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
        logging.debug('Запущен процесс отправки запроса к API.')
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={
                'from_date': timestamp,
            },
        )
        if response.status_code != HTTPStatus.OK:
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                raise exceptions.HTTPExceptionError(
                    'Ошибка авторизации к API сервиса Практикум.Домашка.',
                )
            if response.status_code == HTTPStatus.BAD_REQUEST:
                raise exceptions.HTTPExceptionError(
                    'Ошибка запроса к API сервиса Практикум.Домашка.',
                )
            raise exceptions.HTTPExceptionError(
                'Некорректный ответ от API сервиса Практикум.Домашка.',
            )
        logging.debug('Удачная отправка запроса к API.')
        return response.json()
    except RequestException as error:
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
            'Невалидный тип ответа от API сервиса Практикум.Домашка, '
            'response должен быть словарем.',
        )
    if 'homeworks' not in response:
        raise KeyError(
            'Невалидный формат ответа от сервиса Практикум.Домашка, '
            'отсутствует необходимый ключ `homeworks`',
        )
    if 'current_date' not in response:
        raise KeyError(
            'Невалидный формат ответа от сервиса Практикум.Домашка, '
            'отсутствует необходимый ключ `current_date`',
        )
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(
            'Невалидный тип ответа от API сервиса Практикум.Домашка, '
            'ключ `homeworks` должен быть списком.',
        )
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    Args:
        homework (dict): Последний элемент из списка домашних работ.

    Returns:
        Сообщение, которое содержит информацию работы и её статус.
    """
    if 'homework_name' not in homework:
        raise exceptions.InvalidHomeworkKeyError(
            'Отсутствует необходимый ключ `homework_name` '
            'в списке домашних работ.',
        )
    if 'status' not in homework:
        raise exceptions.InvalidHomeworkKeyError(
            'Отсутствует необходимый ключ `homework_status` '
            'в списке домашних работ.',
        )
    homework_name, homework_status = homework.get(
        'homework_name',
    ), homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS.keys():
        raise exceptions.InvalidHomeworkKeyError(
            'Статус не соответствует ожидаемым.',
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота-ассистента."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения.')
        sys.exit()
    logging.debug('Все обязательные переменные окружения присутствуют.')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                time_now = time.strftime(
                    '%d.%m.%Y г. %H:%M:%S',
                    time.localtime(timestamp),
                )
                if message + f' Дата и время: {time_now}' != last_message:
                    send_message(bot, message)
                    last_message = message + f' Дата и время: {time_now}'
            else:
                logging.debug('Новых статусов нет.')
        except Exception as error:
            if str(error) != last_message:
                send_message(bot, str(error))
            last_message = str(error)
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)
            timestamp = int(time.time())


if __name__ == '__main__':
    main()
