class CheckOutProjectExceptionError(Exception):
    """Базовое исключение для проекта."""


class InvalidHomeworkKeyError(CheckOutProjectExceptionError):
    """Исключение при проверки статуса ответа."""


class PracticumAPIRequestError(CheckOutProjectExceptionError):
    """Неоднозначное исключение при обработке запроса API Практикум.Домашка."""


class HTTPExceptionError(CheckOutProjectExceptionError):
    """Исключение при получении ответа HTTP."""
