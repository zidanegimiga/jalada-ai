from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from jalada.shared.errors import (
    ActionClosed,
    ActionNotFound,
    ApplicationError,
    AssistantOff,
    ConfirmationMismatch,
    ConsentNeeded,
    EmailAlreadyRegistered,
    EmptyEvidence,
    EmptyQuestion,
    EntryNotFound,
    EvidenceNotFound,
    FileTooLarge,
    GoogleSignInFailed,
    InvalidCredentials,
    InvalidEntry,
    NotSignedIn,
    SuggestionNotFound,
    ThreadNotFound,
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
    EntryNotFound: (404, "not_found", "That entry does not exist."),
    SuggestionNotFound: (404, "not_found", "That question has no answer to give any more."),
    ConfirmationMismatch: (
        422,
        "confirmation_mismatch",
        "Type your email exactly as it is on your account.",
    ),
    TooManyAttempts: (429, "too_many_attempts", "Too many attempts. Wait a minute and try again."),
    AssistantOff: (404, "assistant_off", "The assistant is not available."),
    ThreadNotFound: (404, "not_found", "That conversation does not exist."),
    EmptyQuestion: (422, "empty", "Type a question first."),
    ActionNotFound: (404, "not_found", "That suggested change does not exist."),
    ConsentNeeded: (
        403,
        "consent_needed",
        "Allow reading with AI on your Account page to ask about your records.",
    ),
    ActionClosed: (
        409,
        "already_decided",
        "That change was already confirmed or declined, or it has expired. Ask again.",
    ),
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def add_error_handlers(app: FastAPI) -> None:
    async def known_error(request: Request, error: Exception) -> JSONResponse:
        return error_response(*ERRORS[type(error)])

    async def invalid_entry(request: Request, error: Exception) -> JSONResponse:
        reason = error.reason if isinstance(error, InvalidEntry) else "That entry is not valid."
        return error_response(422, "invalid_entry", reason)

    async def invalid_request(request: Request, error: Exception) -> JSONResponse:
        return error_response(422, "invalid_request", "Some fields are missing or invalid.")

    for error_type in ERRORS:
        app.add_exception_handler(error_type, known_error)
    app.add_exception_handler(InvalidEntry, invalid_entry)
    app.add_exception_handler(RequestValidationError, invalid_request)
    app.add_exception_handler(ApplicationError, known_error)
