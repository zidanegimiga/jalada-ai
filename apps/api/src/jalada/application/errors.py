class ApplicationError(Exception):
    """Base class for errors a use case reports to its caller."""


class EmailAlreadyRegistered(ApplicationError):
    pass


class WeakPassword(ApplicationError):
    pass


class InvalidCredentials(ApplicationError):
    pass


class NotSignedIn(ApplicationError):
    pass


class GoogleSignInFailed(ApplicationError):
    pass


class UnsupportedFile(ApplicationError):
    pass


class FileTooLarge(ApplicationError):
    pass


class EmptyEvidence(ApplicationError):
    pass


class EvidenceNotFound(ApplicationError):
    pass
