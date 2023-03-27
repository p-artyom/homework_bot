class CheckOutProjectException(Exception):
    """Базовое исключение для проекта."""


class InvalidResponseKey(CheckOutProjectException):
    """Исключение при проверки ответа на соответствие документации."""


class InvalidHomeworkKey(CheckOutProjectException):
    """Исключение при проверки статуса ответа."""


class PracticumAPIRequestError(CheckOutProjectException):
    """Неоднозначное исключение при обработке запроса API Практикум.Домашка."""


class HTTPException(CheckOutProjectException):
    """Исключение при получении ответа HTTP."""


class InvalidInputDataError(CheckOutProjectException):
    """Исключение при получении ответа HTTP."""
