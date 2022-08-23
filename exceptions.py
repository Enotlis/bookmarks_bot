"""Кастомные исключения, генерируемые приложением"""

class TechnicalWorks(Exception):
    """Технические работы на сайте"""
    pass

class NotCorrectMessage(Exception):
    """Некорректное сообщение в бот"""
    pass

class NotCorrectUrl(Exception):
    """Некорректная ссылка в сообщение"""
    pass


class MangaStoppedReleased(Exception):
    """Мангу перестали выпускать"""
    pass

class MangaComplete(Exception):
    """Манга завершена"""
    pass