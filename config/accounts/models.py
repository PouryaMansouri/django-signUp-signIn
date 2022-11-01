import random
from datetime import timedelta

import boto3
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_expires_timestamp():
    return timezone.now() + timedelta(minutes=2)


def generate_code():
    return random.randint(111111, 999999)


# User model
class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('email',)
        db_table = 'users'


# AuthRequest model
class AuthRequest(models.Model):
    class Meta:
        verbose_name = _('Auth Request')
        verbose_name_plural = _('Auth Requests')
        db_table = 'auth_requests'

    class REQUEST_TYPE(models.IntegerChoices):
        REGISTER = 0, 'Register'
        LOGIN = 1, 'Login'
        FORGET_PASS = 2, 'Forget Password'
        RESET_PASS = 3, 'Reset Password'

    class STATUS(models.IntegerChoices):
        PENDING = 0, 'Pending'
        COMPLETE = 1, 'Complete'

    email = models.CharField(max_length=255)
    device_uuid = models.CharField(max_length=40)
    code = models.CharField(max_length=6, default=generate_code)
    request_status = models.IntegerField(choices=STATUS.choices, default=STATUS.PENDING)
    request_type = models.IntegerField(choices=REQUEST_TYPE.choices, default=REQUEST_TYPE.REGISTER)
    expires_at = models.DateTimeField(default=generate_expires_timestamp)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    time_try = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(3)])
    user_is_active = models.BooleanField(default=False)

    # TODO: Add Documentation
    def __str__(self):
        return f'{self.email} - {self.code}'

    def is_expired(self) -> bool:
        return self.expires_at < timezone.now()

    def close_request(self):
        self.request_status = self.STATUS.COMPLETE
        self.save()

    @staticmethod
    def check_user_is_active(email):
        user = User.objects.get(email=email)
        if user.is_active:
            return True
        return False

    @staticmethod
    def get_user_by_email(email):
        user_filter = User.objects.filter(email=email)
        return user_filter.first() if user_filter.exists() else None

    def send_code(self, service=None, provider=None):
        client = boto3.client("ses")

        try:
            response = client.send_email(
                Source='peridotpy@gmail.com',
                Destination={
                    'ToAddresses': [
                        f'{self.email}',
                    ],
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': 'UTF-8',
                            'Data': 'Your code is: {}'.format(self.code),
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': 'Verification Code',
                    },
                },
                SourceArn="arn:aws:ses:us-east-1:945380995132:identity/peridotpy@gmail.com"
            )
            response_code = response['ResponseMetadata']['HTTPStatusCode']
            error_message = ''
        except Exception as e:
            response_code = 500
            # email is not in SES verified email list
            error_message = 'Email is not in SES verified email list'
            print(e)
        print(f'code: {self.code}')
        return response_code, error_message

    @staticmethod
    def create_inactive_user(username, email, password):
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False
        user.save()
        return user
