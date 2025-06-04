from rest_framework import serializers
from .models import Token, User

class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['access_token', 'refresh_token']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'provider']
        read_only_fields = ['id', 'provider']