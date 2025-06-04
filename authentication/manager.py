from django.contrib.auth.models import BaseUserManager
from django.db.models import Q
from .email_validation import is_disposable_email, is_valid_email_format
from rest_framework.serializers import ValidationError
from django.utils.translation import gettext

# Create a custom usermanager
class UserManager(BaseUserManager):

    def get_queryset(self):
        return super().get_queryset().filter(Q(is_active=1))

    # For normal user
    def create_user(self, email, password=None, **extra_fields):
        
        """
            Create User
        """

        if not email:
            raise ValueError(gettext("User Email must be required"))
        
        email = self.normalize_email(email)
        
        if 'username' not in extra_fields or not extra_fields['username']:
            extra_fields['username'] = email
        
        if not is_valid_email_format(email):
            raise ValidationError(gettext('Invalid email format'))
        
        if is_disposable_email(email):
            raise ValidationError(gettext('Disposable email addresses are not allowed'))

        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        return user


    # For admin user
    def create_superuser(self, email, password=None, **extra_fields):

        """
            Create Admin User
        """

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(
            email=email,
            password=password,
            **extra_fields
        )