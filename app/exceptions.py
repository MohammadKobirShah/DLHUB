"""
DLHUB - Custom Exception Classes
================================
Application-specific exceptions for error handling.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from fastapi import HTTPException, status


class DLHUBException(Exception):
    """Base exception for DLHUB."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DownloadException(DLHUBException):
    """Base exception for download-related errors."""
    pass


class InvalidURLException(DownloadException):
    """Invalid or unsupported URL."""
    pass


class URLBlockedException(DownloadException):
    """URL blocked by SSRF protection."""
    pass


class UnsupportedExtractorException(DownloadException):
    """Extractor not supported."""
    pass


class DownloadTimeoutException(DownloadException):
    """Download operation timed out."""
    pass


class FileTooLargeException(DownloadException):
    """File exceeds maximum size limit."""
    pass


class DurationTooLongException(DownloadException):
    """Video duration exceeds maximum limit."""
    pass


class DownloadFailedException(DownloadException):
    """Download operation failed."""
    pass


class JobNotFoundException(DLHUBException):
    """Job not found in database."""
    pass


class JobCancelledException(DLHUBException):
    """Job was cancelled."""
    pass


class InvalidFormatException(DLHUBException):
    """Invalid output format specified."""
    pass


class FileNotFoundException(DLHUBException):
    """File not found."""
    pass


class StorageException(DLHUBException):
    """Storage operation failed."""
    pass


class QueueException(DLHUBException):
    """Queue operation failed."""
    pass


class WorkerException(DLHUBException):
    """Worker process failed."""
    pass


class MediaProcessingException(DLHUBException):
    """Media processing operation failed."""
    pass


def http_exception(status_code: int, message: str, details: dict = None):
    """Create HTTP exception with custom message."""
    return HTTPException(
        status_code=status_code,
        detail={"message": message, "details": details or {}}
    )


def not_found(resource: str, identifier: str = None):
    """Create 404 not found exception."""
    msg = f"{resource} not found"
    if identifier:
        msg += f": {identifier}"
    return http_exception(status.HTTP_404_NOT_FOUND, msg)


def bad_request(message: str, details: dict = None):
    """Create 400 bad request exception."""
    return http_exception(status.HTTP_400_BAD_REQUEST, message, details)


def internal_error(message: str, details: dict = None):
    """Create 500 internal error exception."""
    return http_exception(status.HTTP_500_INTERNAL_SERVER_ERROR, message, details)


def service_unavailable(message: str):
    """Create 503 service unavailable exception."""
    return http_exception(status.HTTP_503_SERVICE_UNAVAILABLE, message)