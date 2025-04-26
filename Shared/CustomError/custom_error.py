class CustomException(Exception):
    """
    Базовый класс для всех пользовательских исключений в нашем приложении.
    """

    def __init__(self, message="Произошла ошибка"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"CustomException: {self.message}"


class OverlappingReservationError(CustomException):
    """
    Исключение, возникающее при пересечении по времени между бронями
    """

    def __init__(self, message="Время для записи занято"):
        super().__init__(message)


class NotFoundInDBError(CustomException):
    """
    Исключение, возникающее когда запись была не найдена
    """

    def __init__(self, message="Запись не найдена"):
        super().__init__(message)


class NotValidPassword(CustomException):
    """
    Исключение, возникающее когда ввели неверный пароль
    """

    def __init__(self, message="Неверный пароль"):
        super().__init__(message)