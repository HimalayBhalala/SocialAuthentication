from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class UserDeactivatedException(Exception):
    """Raised when a user account is deactivated"""
    pass

class SocialAuthException(Exception):
    """Raised when social authentication fails"""
    pass

def custom_exception_handler(exc, context):
    """Custom exception handler for authentication-related exceptions"""
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, UserDeactivatedException):
            return Response(
                {'error': _('Your account has been deactivated. Please contact support.')},
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, SocialAuthException):
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, ValidationError):
            return Response(
                {'error': exc.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, (InvalidToken, TokenError)):
            return Response(
                {'error': _('Invalid or expired token.')},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return None

    # Handle specific error cases
    if isinstance(exc, ValidationError):
        response.data = {'error': exc.messages}
    elif isinstance(exc, (InvalidToken, TokenError)):
        response.data = {'error': _('Invalid or expired token.')}
    elif response.status_code == 401:
        response.data = {'error': _('Authentication credentials were not provided.')}
    elif response.status_code == 403:
        response.data = {'error': _('You do not have permission to perform this action.')}
    elif response.status_code == 404:
        response.data = {'error': _('The requested resource was not found.')}
    elif response.status_code == 500:
        response.data = {'error': _('An unexpected error occurred. Please try again later.')}

    return response 