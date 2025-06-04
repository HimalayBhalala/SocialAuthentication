from django.db import models
from django.contrib.auth.models import AbstractUser
from .manager import UserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .email_validation import is_disposable_email, is_valid_email_format
from django.utils.translation import gettext


# Create your models here
class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=200,unique=False)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    is_terms_accepted = models.BooleanField(default=False)
    reset_password_otp_verify = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=100, null=True, blank=True)
    account_activate = models.BooleanField(default=1)
    anonymous_fingerprint = models.CharField(max_length=64, null=True, blank=True)
    is_anonymous_user = models.BooleanField(default=False)
    pending_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email_enabled = models.BooleanField(default=0)

    objects = UserManager()
    all_objects = models.Manager() 

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    class Meta:
        verbose_name_plural = 'User'
        db_table = 'user'

    def __str__(self):
        return self.email
    
    def clean(self):
        """Additional validation when saving through forms"""
        super().clean()
        
        if self.email:
            if not is_valid_email_format(self.email):
                raise ValidationError({'email': gettext('Invalid email format')})
            
            if is_disposable_email(self.email):
                raise ValidationError({'email': gettext('Disposable email addresses are not allowed')})

    def save(self, *args, **kwargs):
        """Override save to enforce validation even when not using forms"""
        self.clean()
        super().save(*args, **kwargs)



class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name_plural = "Token"
        db_table = "token"