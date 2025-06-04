from django.urls import path
from .views import *

app_name = 'authentication'

urlpatterns = [
    # Template
    path('login', LoginTemplateView.as_view(), name='login'),
    path('signup', SignupTemplateView.as_view(), name='signup'),
    path('logout', LogoutView.as_view(), name='logout'),

    # API Endpoints - Social Authentication
    path('google', GoogleLoginView.as_view(), name='google_login'),
    path('github', GitHubLoginView.as_view(), name='github_login'),
    path('apple', AppleLoginView.as_view(), name='apple_login'),
    path('linkedin', LinkedInLoginView.as_view(), name='linkedin_login'),
    path('microsoft', MicrosoftLoginView.as_view(), name='microsoft_login'),
    path('twitter', TwitterLoginView.as_view(), name='twitter_login'),
    path('facebook', FacebookLoginView.as_view(), name='facebook_login'),
    path('instagram', InstagramLoginView.as_view(), name='instagram_login'),

    # API Endpoints - Traditional Authentication
    path('login', LoginView.as_view(), name='login'),
    path('signup', RegisterView.as_view(), name='signup'),
]
