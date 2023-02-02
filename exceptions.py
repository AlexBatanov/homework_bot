class NotToken(Exception):
    """Отсутствие токена."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f'{self.__class__.__name__}: нет токина {self.message}'


class UnknownStatusHomework(Exception):
    """Нет нужного статуса работы."""
    def __str__(self):
        return (f'{self.__class__.__name__}: '
                'такого статуса не существет в HOMEWORK_VERDICTS')


class ResponseStatusInvalid(Exception):
    """API status code != 200."""
    def __str__(self):
        return (f'{self.__class__.__name__}: API status code != 200')


class NoStatusHomework(Exception):
    """Нет статуса домашней работы."""
    def __str__(self):
        return (f'{self.__class__.__name__}: '
                'Отсутсвует статус домашней работы')


class NoHomework(Exception):
    """Нет домашних работ."""
    def __str__(self):
        return (f'{self.__class__.__name__}: Нет домашних работ')
