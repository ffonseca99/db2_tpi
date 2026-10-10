"""Excepciones de negocio. main.py las convierte en respuestas HTTP con {"detail": "..."}."""


class AppError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    """Pedido mal formado (id inválido, nada para actualizar)."""
    status_code = 400


class NotFoundError(AppError):
    """El recurso no existe o está dado de baja."""
    status_code = 404


class ConflictError(AppError):
    """Choca con el estado actual (DNI repetido, sin cupo, reserva duplicada)."""
    status_code = 409


class BusinessRuleError(AppError):
    """Regla de negocio incumplida (ej. reservar con un socio dado de baja)."""
    status_code = 422
