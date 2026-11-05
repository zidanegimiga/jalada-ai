from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from jalada.application.errors import (
    ApplicationError,
    EmailAlreadyRegistered,
    EmptyEvidence,
    EvidenceNotFound,
    FileTooLarge,
    GoogleSignInFailed,
    InvalidCredentials,
    NotSignedIn,
    UnsupportedFile,
    WeakPassword,
)


class TooManyAttempts(Exception):
    pass


ERRORS: dict[type[Exception], tuple[int, str, str]] = {
    EmailAlreadyRegistered: (409, "email_taken", "An account with this email already exists."),
    WeakPassword: (422, "weak_password", "Use a password of at least 10 characters."),
    InvalidCredentials: (401, "invalid_credentials", "The email or password is wrong."),
    NotSignedIn: (401, "not_signed_in", "Sign in to continue."),
    GoogleSignInFailed: (401, "google_failed", "Google sign-in did not work. Try again."),
    UnsupportedFile: (415, "unsupported_file", "Send a photo (JPEG, PNG or WebP) or a PDF."),
    FileTooLarge: (413, "too_large", "That is too big. Files can be up to 10 MB."),
    EmptyEvidence: (422, "empty", "There is nothing to save."),
    EvidenceNotFound: (404, "not_found", "That evidence does not exist."),
    TooManyAttempts: (429, "too_many_attempts", "Too many attempts. Wait a minute and try again."),
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def add_error_handlers(app: FastAPI) -> None:
    async def known_error(request: Request, error: Exception) -> JSONResponse:
        return error_response(*ERRORS[type(error)])

    async def invalid_request(request: Request, error: Exception) -> JSONResponse:
        return error_response(422, "invalid_request", "Some fields are missing or invalid.")

    for error_type in ERRORS:
        app.add_exception_handler(error_type, known_error)
    app.add_exception_handler(RequestValidationError, invalid_request)
    app.add_exception_handler(ApplicationError, known_error)
