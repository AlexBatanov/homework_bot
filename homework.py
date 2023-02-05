from http import HTTPStatus
import sys
import time
import logging

import requests
import telegram

from exceptions import (NoStatusHomework, RequestConnectException,
                        ResponseStatusInvalid, UnknownStatusHomework)
from consts import (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                    RETRY_PERIOD, ENDPOINT, HEADERS, HOMEWORK_VERDICTS)


def get_logger(name: str) -> object:
    """Настройка логера."""
    format = ('%(asctime)s %(levelname)s - '
              '%(funcName)s(%(lineno)d) - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(format))
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    return logger


logger = get_logger(__name__)


def check_tokens() -> bool:
    """Проверка наличия токенов, возбуждает исключение."""
    tokens = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID'
    }

    for key, value in tokens.items():
        if not key:
            logger.critical('Отсутствует обязательная '
                            f'переменная окружения: {value}')
            return False

    return True


def send_message(bot: telegram.Bot, message: str) -> bool:
    """Отправка сообщений в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('удачная отправка сообщения в Telegram')
    except telegram.error.TelegramError as error:
        logger.error(f'{error}: сбой при отправке сообщения в Telegram')

        return False
    return True


def get_api_answer(timestamp: int) -> dict:
    """
    Подключение к API.
    возбуждает исключение если статус ответа != 200
    """
    payload = {'from_date': timestamp}

    try:
        request = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as err:
        logger.error(f'{err}: Сбой в работе программы: '
                     f'Эндпоинт {ENDPOINT} недоступен. ')
        raise RequestConnectException(err)

    if request.status_code != HTTPStatus.OK:
        logger.error(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {request.status_code}'
        )
        raise ResponseStatusInvalid

    return request.json()


def check_response(response: dict) -> None:
    """
    Проверка данных.
    вызывает исключение если данные не валидны
    """
    data = {'homeworks': list, 'current_date': int}

    if not isinstance(response, dict):
        logger.error('Данные не верного типа')
        raise TypeError

    for k, v in data.items():
        if k not in response:
            logger.error(f'Данные не валидны, отсутсвует ключ "{k}"')
            raise KeyError

        if not isinstance(response.get(k), v):
            logger.error('Данные не верного типа')
            raise TypeError


def parse_status(homework: dict) -> str:
    """
    Извлекает статус и название работы.
    вызывает исключение если данные не валидны
    """
    verdict = homework.get('status')
    homework_name = homework.get('homework_name')

    for key in ('status', 'homework_name'):
        if key not in homework:
            logger.error(f'Данные не валидны, отсутсвует ключ "{key}"')
            raise KeyError

    if not homework_name:
        logger.error('Отсутсвет статус домашней работы')
        raise NoStatusHomework

    if verdict not in HOMEWORK_VERDICTS:
        logger.error('Неожиданный статус  домашней работы, '
                     'обнаруженный в ответе API ')
        raise UnknownStatusHomework

    return (f'Изменился статус проверки работы "{homework_name}" '
            f'{HOMEWORK_VERDICTS.get(verdict)}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Проблема с токенами')

    logger.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    message_no_hw = 'Домашних работ нет, ждем...'
    message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response.get('homeworks')

            if not homework and message != message_no_hw:
                message = message_no_hw
                send_message(bot, message)
            else:
                message_new = parse_status(homework[0])

            if message != message_new:
                if send_message(bot, message_new):
                    message = message_new
                    timestamp = response.get('current_date')

        except Exception as error:
            logger.debug(f'Сбой в работе программы: {error}')
            message_err = f'Сбой в работе программы: {error}'

            if message != message_err:
                if send_message(bot, message_err):
                    message = message_err
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
