import sys
import time
import os

from dotenv import load_dotenv
from telegram import Bot
import requests

from app_logger import get_logger
from exceptions import NotToken, NotCorrectResponse


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = ...
TELEGRAM_CHAT_ID = ...

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

load_dotenv()
logger = get_logger(__name__)
cache_verdict = dict()

def check_tokens() -> None:
    """Проверка наличия токенов, возбуждает исключение"""

    if None in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        logger.critical('Отсутствует обязательная переменная окружения')
        raise NotToken


def send_message(bot: Bot, message: str) -> None:
    """Отправка сообщений в Telegram"""

    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('удачная отправка сообщения в Telegram')
    except Exception as error:
        logger.error(f'{error}: сбой при отправке сообщения в Telegram')

def get_api_answer(timestamp: int) -> dict | None:
    """Подключение к API"""

    payload = {'from_date': timestamp}

    try:
        request = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        response = request.json()
    except Exception:
        logger.error(
            f'Сбой в работе программы: Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {request.status_code}'
        )
    else:
        return response

def check_response(response: dict) -> None:
    """Проверка валидности данных"""

    if not response.get('homeworks'):
        logger.error('отсутствие ожидаемых ключей в ответе API')
        raise TypeError


def parse_status(homework: dict) -> str | None:
    """Извлекает статус работы, при изменении статуса возвращает строку"""

    #homework_name = homework.get('homework_name')
    verdict = homework.get('status')
    id = homework.get('id')

    if not HOMEWORK_VERDICTS.get(verdict):
        logger.error('неожиданный статус  домашней работы, обнаруженный в ответе API ')

    if cache_verdict.get(id) != verdict:
        cache_verdict[id] = verdict

        return HOMEWORK_VERDICTS.get(verdict)
    else:
        logger.debug('отсутствие в ответе новых статусов')
        cache_verdict[id] = verdict


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except Exception as error:
        sys.exit(error)

    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        else:
            send_message(bot, message)

        time.sleep(600)

if __name__ == '__main__':
    main()
