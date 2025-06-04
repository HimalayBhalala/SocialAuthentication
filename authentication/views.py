from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext
from .models import User, Token
from .serializers import TokenSerializer, UserSerializer
from .utils import get_token_for_user, handle_exceptions
from .exceptions import UserDeactivatedException
import requests
import jwt
from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.permissions import AllowAny
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken



APPLE_PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"

# Create your views here.


def get_token_for_user(user):

    token = RefreshToken.for_user(user)

    return {
        "access" : str(token.access_token),
        "refresh" : str(token)
    }


class GoogleLoginView(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
       
        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Google
        google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(google_userinfo_url, headers={"Authorization": f"Bearer {str(access_token)}"})

        if response.status_code != 200:
            return Response({'error': gettext('Invalid Google access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')

        first_name = email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(email=email, defaults={"first_name" : first_name, "username": email, "provider": "google"})
        
        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            defaults={
                "access_token": refresh.get("access"),
                "refresh_token": refresh.get("refresh")
            }
        )

        return Response({
            "message": gettext("Google authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token':TokenSerializer(token).data,
	    'redirect_url':'http://localhost:8000/'
        })
     

class GitHubLoginView(APIView):
    @handle_exceptions()
    def post(self, request, *args, **kwargs):

        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        github_userinfo_url = "https://api.github.com/user"
        github_email_url = "https://api.github.com/user/emails"

        headers = {"Authorization": f"Bearer {access_token}"}

        # Get basic user info
        user_response = requests.get(github_userinfo_url, headers=headers)
        if user_response.status_code != 200:
            return Response({'error': gettext('Invalid GitHub access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = user_response.json()

        # Get user email info
        email_response = requests.get(github_email_url, headers=headers)
        if email_response.status_code != 200:
            return Response({'error': gettext('Unable to fetch GitHub email')}, status=status.HTTP_400_BAD_REQUEST)

        emails = email_response.json()
        primary_email = next((item['email'] for item in emails if item.get('primary') and item.get('verified')), None)

        if not primary_email:
            return Response({'error': gettext('Primary verified email not found')}, status=status.HTTP_400_BAD_REQUEST)

        first_name = user_info.get("login") if user_info.get("login") else primary_email.split('@')[0]

        user, created = User.all_objects.get_or_create(
            email=primary_email, 
            defaults={"first_name": first_name, "username": primary_email, "provider": "github"}
        )

        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("GitHub authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token': TokenSerializer(token).data,
            'redirect_url': 'http://localhost:8000/'
        })


class AppleLoginView(APIView):
    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        identity_token = request.data.get('token')
        if not identity_token:
            return Response({'error': gettext('Identity token is required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get Apple public keys
            apple_keys_response = requests.get(APPLE_PUBLIC_KEYS_URL)
            apple_keys = apple_keys_response.json().get('keys')

            # Decode token headers to match the correct public key
            headers = jwt.get_unverified_header(identity_token)
            key = next((k for k in apple_keys if k['kid'] == headers['kid']), None)
            if not key:
                return Response({'error': gettext('Invalid identity token key')}, status=status.HTTP_400_BAD_REQUEST)

            # Construct public key and decode the token
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
            decoded_token = jwt.decode(identity_token, public_key, algorithms=["RS256"], audience=settings.APPLE_CLIENT_ID)

            email = decoded_token.get('email') or request.data.get("email")
            if not email:
                return Response({'error': gettext('Email not provided in Apple token')}, status=status.HTTP_400_BAD_REQUEST)

        except jwt.ExpiredSignatureError:
            return Response({'error': gettext('Token has expired')}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': gettext('Invalid token')}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get("name", "")
        first_name = name.split()[0] if name else email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "username": email, "provider": "apple"}
        )

        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"),
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Apple authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token': TokenSerializer(token).data,
            'redirect_url': 'http://localhost:8000/'
        })

    
class LinkedInLoginView(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):

        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 1: Get user profile (first name, last name, id)
        profile_url = "https://api.linkedin.com/v2/me"
        profile_response = requests.get(profile_url, headers=headers)

        if profile_response.status_code != 200:
            return Response({'error': gettext('Invalid LinkedIn access token')}, status=status.HTTP_400_BAD_REQUEST)

        profile_data = profile_response.json()

        # Step 2: Get user email
        email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
        email_response = requests.get(email_url, headers=headers)

        if email_response.status_code != 200:
            return Response({'error': gettext('Unable to fetch LinkedIn email')}, status=status.HTTP_400_BAD_REQUEST)

        email_data = email_response.json()
        elements = email_data.get("elements", [])
        email = elements[0].get("handle~", {}).get("emailAddress") if elements else None

        if not email:
            return Response({'error': gettext('LinkedIn email not found')}, status=status.HTTP_400_BAD_REQUEST)

        first_name = profile_data.get("firstName") if profile_data.get("firstName") else email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(
            email=email,
            defaults={"first_name": first_name, "username": email, "provider": "linkedin"}
        )

        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("LinkedIn authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token': TokenSerializer(token).data,
            'redirect_url': 'http://localhost:8000/'
        })

     
class MicrosoftLoginView(APIView):

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
       
        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Google
        google_userinfo_url = "https://graph.microsoft.com/v1.0/me"
        response = requests.get(google_userinfo_url, headers={"Authorization": f"Bearer {str(access_token)}"})

        if response.status_code != 200:
            return Response({'error': gettext('Invalid Google access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')

        first_name = email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(email=email, defaults={"first_name" : first_name, "username": email, "provider": "microsoft"})
        
        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Microsoft authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token':TokenSerializer(token).data,
	    'redirect_url':'http://localhost:8000/'
        })


class TwitterLoginView(APIView):
    @handle_exceptions()
    def post(self, request, *args, **kwargs):
       
        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Google
        google_userinfo_url = "https://api.twitter.com/2/users/me"
        response = requests.get(google_userinfo_url, headers={"Authorization": f"Bearer {str(access_token)}"})

        if response.status_code != 200:
            return Response({'error': gettext('Invalid Google access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')

        first_name = email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(email=email, defaults={"first_name" : first_name, "username": email, "provider": "twitter"})
        
        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Twitter authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token':TokenSerializer(token).data,
	    'redirect_url':'http://localhost:8000/'
        })


class FacebookLoginView(APIView):
    
    @handle_exceptions()
    def post(self, request, *args, **kwargs):
       
        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Google
        google_userinfo_url = "https://graph.facebook.com/me"
        response = requests.get(google_userinfo_url, headers={"Authorization": f"Bearer {str(access_token)}"})

        if response.status_code != 200:
            return Response({'error': gettext('Invalid Google access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')

        first_name = email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(email=email, defaults={"first_name" : first_name, "username": email, "provider": "microsoft"})
        
        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Microsoft authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },
            'token':TokenSerializer(token).data,
	    'redirect_url':'http://localhost:8000/'
        })


class InstagramLoginView(APIView):
    @handle_exceptions()
    def post(self, request, *args, **kwargs):

        access_token = request.data.get('token')
        if not access_token:
            return Response({'error': gettext('Access token is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user info from Instagram
        instagram_userinfo_url = "https://graph.instagram.com/me"

        response = requests.get(instagram_userinfo_url, headers={"Authorization": f"Bearer {str(access_token)}"})

        if response.status_code != 200:
            return Response({'error': gettext('Invalid Instagram access token')}, status=status.HTTP_400_BAD_REQUEST)

        user_info = response.json()
        email = user_info.get('email')

        first_name = email.split('@')[0]

        # Create or authenticate user
        user, created = User.all_objects.get_or_create(email=email, defaults={"first_name" : first_name, "username": email, "provider": "instagram"})

        if not user.account_activate:
            raise UserDeactivatedException()

        if not user.is_terms_accepted:
            user.is_terms_accepted = True
            user.save(update_fields=["is_terms_accepted"])  

        # Generate JWT token (assuming you have a token generation function)
        refresh = get_token_for_user(user)

        token, is_created = Token.objects.update_or_create(
            user=user,
            access_token=refresh.get("access"), 
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Instagram authentication successful"),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "username": user.email,
            },  
            'token': TokenSerializer(token).data,
            'redirect_url': 'http://localhost:8000/'
        })


# Template Views
class LoginTemplateView(TemplateView):
    template_name = 'account/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('authentication:dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'GOOGLE_CLIENT_ID': settings.GOOGLE_OAUTH_CLIENT_ID,
            'GITHUB_CLIENT_ID': settings.GITHUB_OAUTH_CLIENT_ID,
            'FACEBOOK_CLIENT_ID': settings.FACEBOOK_OAUTH_CLIENT_ID,
            'TWITTER_CLIENT_ID': settings.TWITTER_OAUTH_CLIENT_ID,
            'MICROSOFT_CLIENT_ID': settings.MICROSOFT_OAUTH_CLIENT_ID,
            'APPLE_CLIENT_ID': settings.APPLE_CLIENT_ID,
        })
        return context

class DashboardTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'account/dashboard.html'
    login_url = 'authentication:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    
class SignupTemplateView(TemplateView):
    template_name = 'account/signup.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('authentication:dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'GOOGLE_CLIENT_ID': settings.GOOGLE_OAUTH_CLIENT_ID,
            'GITHUB_CLIENT_ID': settings.GITHUB_OAUTH_CLIENT_ID,
            'FACEBOOK_CLIENT_ID': settings.FACEBOOK_OAUTH_CLIENT_ID,
            'TWITTER_CLIENT_ID': settings.TWITTER_OAUTH_CLIENT_ID,
            'MICROSOFT_CLIENT_ID': settings.MICROSOFT_OAUTH_CLIENT_ID,
            'APPLE_CLIENT_ID': settings.APPLE_CLIENT_ID,
        })
        return context

class LogoutView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, *args, **kwargs):
        # Handle direct browser navigation/logout
        logout(request)
        if request.user.is_authenticated:
            Token.objects.filter(user=request.user).delete()
        messages.success(request, gettext('You have been successfully logged out.'))
        return redirect('authentication:login')
    
    def post(self, request, *args, **kwargs):
        # Handle AJAX logout
        try:
            logout(request)
            if request.user.is_authenticated:
                Token.objects.filter(user=request.user).delete()
            
            return Response({
                'message': gettext('You have been successfully logged out.'),
                'redirect_url': reverse('authentication:login')
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    permission_classes = [AllowAny]

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        remember = request.data.get('remember', False)

        if not email or not password:
            return Response(
                {'error': gettext('Email and password are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response(
                {'error': gettext('Invalid email or password')},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.account_activate:
            raise UserDeactivatedException()

        # Login the user in the session
        login(request, user)

        # Generate tokens
        refresh = get_token_for_user(user)
        
        token, is_created = Token.objects.update_or_create(
            user=user,
            defaults={
                'access_token': refresh.get("access"),
                'refresh_token': refresh.get("refresh")
            }
        )

        response = Response({
            "message": gettext("Login successful"),
            "user": UserSerializer(user).data,
            'token': TokenSerializer(token).data,
            'redirect_url': reverse('authentication:dashboard')
        })

        if remember:
            # Set longer expiry for remember me
            response.set_cookie(
                'refresh_token',
                refresh.get("refresh"),
                httponly=True,
                secure=True,
                samesite='Lax',
                max_age=30 * 24 * 60 * 60  # 30 days
            )

        return response

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @handle_exceptions()
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        username = request.data.get('username')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        is_terms_accepted = request.data.get('is_terms_accepted')

        if not all([email, password, username, first_name, last_name]):
            return Response(
                {'error': gettext('All fields are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not is_terms_accepted:
            return Response(
                {'error': gettext('You must accept the terms and conditions')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {'error': e.messages},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': gettext('User with this email already exists')},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': gettext('Username is already taken')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_terms_accepted=is_terms_accepted
        )

        # Login the user
        login(request, user)

        # Generate tokens
        refresh = get_token_for_user(user)
        
        token = Token.objects.create(
            user=user,
            access_token=refresh.get("access"),
            refresh_token=refresh.get("refresh")
        )

        return Response({
            "message": gettext("Registration successful"),
            "user": UserSerializer(user).data,
            'token': TokenSerializer(token).data,
            'redirect_url': reverse('authentication:dashboard')
        }, status=status.HTTP_201_CREATED)