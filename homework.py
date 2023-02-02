from http import HTTPStatus
import sys
import time
import logging

import requests
import telegram

from exceptions import (NoHomework, NoStatusHomework, NotToken,
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

cache_verdict = dict()


def check_tokens() -> None:
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
            raise NotToken(value)


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщений в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('удачная отправка сообщения в Telegram')
    except Exception as error:
        logger.error(f'{error}: сбой при отправке сообщения в Telegram')


def get_api_answer(timestamp: int) -> dict:
    """
    Подключение к API.
    возбуждает исключение если статус ответа != 200
    """
    payload = {'from_date': timestamp}

    try:
        request = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as err:
        logger.error(f'{err}: Сбой в работе программы: '
                     f'Эндпоинт {ENDPOINT} недоступен. ')

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
    вызывает исключение ели данные не валидны
    """
    if not type(response) is dict:
        logger.error('Данные не верного типа')
        raise TypeError

    if not type(response.get('homeworks')) is list:
        logger.error('Данные не верного типа')
        raise TypeError

    if not response.get('homeworks'):
        logger.error('Домашние работы отсутсвуют')
        raise NoHomework


def parse_status(homework: dict) -> str:
    """
    Извлекает статус работы.
    вызывает исключение если данные не валидны
    """
    verdict = homework.get('status')
    homework_name = homework.get('homework_name')

    if not homework_name:
        logger.error('Отсутсвет статус домашней работы')
        raise NoStatusHomework

    if verdict not in HOMEWORK_VERDICTS:
        logger.error('Неожиданный статус  домашней работы, '
                     'обнаруженный в ответе API ')
        raise UnknownStatusHomework

    if cache_verdict.get(homework_name) == verdict:
        logger.debug('отсутствие в ответе новых статусов')
    else:
        cache_verdict[homework_name] = verdict
        logger.debug(f'Изменился статус проверки работы "{homework_name}"')

        return (f'Изменился статус проверки работы "{homework_name}" '
                f'{HOMEWORK_VERDICTS.get(verdict)}')


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except Exception as err:
        sys.exit(err)

    logger.debug('Запуск бота')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response.get('homeworks')[0]
            message = parse_status(homework)
        except Exception as error:
            logger.debug(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'

        if message:
            send_message(bot, message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
