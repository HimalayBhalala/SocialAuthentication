from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils.translation import gettext as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .exceptions import UserDeactivatedException

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip authentication for login and public endpoints
        if request.path.startswith('/auth/login/') or request.path.startswith('/auth/api/auth/'):
            return None

        # Skip authentication for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None

        try:
            jwt_auth = JWTAuthentication()
            auth_tuple = jwt_auth.authenticate(request)
            if auth_tuple is not None:
                user, token = auth_tuple
                request.user = user
                request.auth = token

                # Check if user account is activated
                if not user.account_activate:
                    raise UserDeactivatedException()

        except (InvalidToken, TokenError) as e:
            return JsonResponse(
                {'error': _('Invalid or expired token')},
                status=401
            )
        except UserDeactivatedException:
            return JsonResponse(
                {'error': _('Account is deactivated')},
                status=403
            )
        except Exception as e:
            return JsonResponse(
                {'error': str(e)},
                status=401
            )

        return None 