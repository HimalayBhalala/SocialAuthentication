from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import UserDeactivatedException

# Generate JWT tokens for a user
def get_token_for_user(user):
    """Generate JWT tokens for a user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def handle_exceptions():
    """Decorator to handle common exceptions in views"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(view_instance, request, *args, **kwargs):
            try:
                return view_func(view_instance, request, *args, **kwargs)
            except UserDeactivatedException:
                return Response(
                    {'error': gettext('Account is deactivated')},
                    status=status.HTTP_403_FORBIDDEN
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return wrapper
    return decorator 