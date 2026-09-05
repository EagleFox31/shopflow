class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class ForbiddenError(DomainError):
    status_code = 403


class UnauthorizedError(DomainError):
    status_code = 401


class InvalidStateError(DomainError):
    status_code = 422
