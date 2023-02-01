class NotToken(Exception):
    """Отсутствие токена"""

    def __str__(self):
        return f'{self.__class__.__name__}: проверьте наличие токинов'

class NotCorrectResponse(Exception):
    """Невалидный ответ API"""