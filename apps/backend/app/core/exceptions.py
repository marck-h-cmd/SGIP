from fastapi import HTTPException, status
from typing import Optional, Any


class SGIPCAPException(HTTPException):
    """Base exception for SGIP-CAP"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        data: Optional[Any] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.data = data


class NotFoundException(SGIPCAPException):
    """Resource not found exception"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found",
            error_code="RESOURCE_NOT_FOUND"
        )


class ValidationException(SGIPCAPException):
    """Validation error exception"""
    def __init__(self, detail: str, data: Optional[Any] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            data=data
        )


class ProviderException(SGIPCAPException):
    """Data provider exception"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data provider error: {detail}",
            error_code="PROVIDER_ERROR"
        )


class MLException(SGIPCAPException):
    """ML model exception"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML model error: {detail}",
            error_code="ML_ERROR"
        )


class SecurityException(SGIPCAPException):
    """Security related exception"""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR"
        )