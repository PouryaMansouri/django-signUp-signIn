import re
import time

from rest_framework.serializers import (
    Serializer,
    EmailField,
    CharField,
    ChoiceField,
    ValidationError,
)
from django.contrib.auth.hashers import make_password

from accounts.models import AuthRequest


class SignUpAPISerializer(Serializer):
    """Send Verify Code Serializer

    This serializer validate user data and create AuthRequest record
    This is only for Venus app

    """
    email = EmailField(error_messages={'blank': 'Email cannot be blank',
                                       'null': 'Email cannot be null',
                                       'required': 'Email is required'})
    password = CharField(max_length=250, error_messages={'blank': 'password cannot be blank',
                                                         'null': 'password cannot be null',
                                                         'required': 'password is required'})
    password_confirm = CharField(max_length=250, error_messages={'blank': 'password_confirm cannot be blank',
                                                                 'null': 'password_confirm cannot be null',
                                                                 'required': 'password_confirm is required'})
    device_uuid = CharField(max_length=250, error_messages={'blank': 'device_uuid cannot be blank',
                                                            'null': 'device_uuid cannot be null',
                                                            'required': 'device_uuid is required'})

    def validate(self, attrs):
        email = attrs.get('email')
        device_uuid = attrs.get('device_uuid')
        #TODO: check this email with this uuid has less than 5 request in last 24 hours
        self._check_email_regex(email)
        # TODO : need to be completed
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password != password_confirm:
            raise ValidationError("Password and Password Confirm not match")
        self._check_password(password)
        return attrs

    def _check_email_regex(self, email):
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if re.fullmatch(regex, email) is None:
            raise ValidationError("Email is not valid")

    def _check_password(self, password):
        pattern = "((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W]).{8,64})"
        if not re.fullmatch(pattern, password):
            raise ValidationError("Password is not valid")

    def create(self, validated_data):
        # username is epoch time with 13 digits in milliseconds (13 digits)
        username = str(int(time.time() * 1000))
        email = validated_data.get('email')
        password = validated_data.get('password')
        device_uuid = validated_data.get('device_uuid')
        request_type = AuthRequest.REQUEST_TYPE.REGISTER
        # Check email is already registered
        user = AuthRequest.get_user_by_email(email)
        if user is None:
            user = AuthRequest.create_inactive_user(username, email, password)
        elif user.is_active:
            raise ValidationError("Email is already registered")
        auth_request = AuthRequest.objects.create(
            email=user.email,
            device_uuid=device_uuid,
            request_type=request_type,
        )
        return auth_request


class SignInAPISerializer(Serializer):
    """Send Verify Code Serializer

    This serializer validate user data and create AuthRequest record
    This is only for Venus app

    """
    identifier = CharField(max_length=250, error_messages={'blank': 'identifier cannot be blank',
                                                           'null': 'identifier cannot be null',
                                                           'required': 'identifier is required'})
    password = CharField(max_length=250, error_messages={'blank': 'password cannot be blank',
                                                         'null': 'password cannot be null',
                                                         'required': 'password is required'})

    def validate(self, attrs):
        identifier = attrs.get('identifier')
        identifier_type = self._find_identifier_type(identifier)
        user = AuthRequest.get_user_by_identifier(identifier=identifier, identifier_type=identifier_type)
        if not user:
            raise ValidationError('User not found')
        password = attrs.get('password')
        if not user.check_password(password):
            raise ValidationError('password is incorrect')
        return attrs

    @staticmethod
    def _find_identifier_type(identifier):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if re.match(email_regex, identifier):
            return AuthRequest.IDENTIFIER_TYPE.EMAIL
        return AuthRequest.IDENTIFIER_TYPE.USERNAME

    def create(self, validated_data):
        identifier = validated_data.get('identifier')
        identifier_type = self._find_identifier_type(identifier)
        user_is_registered = True
        user = AuthRequest.get_user_by_identifier(identifier=identifier, identifier_type=identifier_type)
        request_type = AuthRequest.REQUEST_TYPE.LOGIN
        auth_request = AuthRequest.objects.create(
            username=user.username,
            identifier_type=identifier_type,
            identifier=user.email,
            user_is_registered=user_is_registered,
            request_type=request_type,
        )
        return auth_request


class VerifyCodeAPISerializer(Serializer):
    """Verify Code Serializer

    This serializer validate user data and verify code
    This is only for Venus app

    """
    username = CharField(max_length=250, error_messages={'blank': 'username cannot be blank',
                                                         'null': 'username cannot be null',
                                                         'required': 'username is required'})
    email = EmailField(error_messages={'blank': 'Email cannot be blank',
                                       'null': 'Email cannot be null',
                                       'required': 'Email is required'})
    code = CharField(max_length=250, error_messages={'blank': 'code cannot be blank',
                                                     'null': 'code cannot be null',
                                                     'required': 'code is required'})

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        code = attrs.get('code')
        auth_request = AuthRequest.objects.filter(username=username, identifier=email, code=code)
        if not auth_request.exists():
            raise ValidationError('Code is not valid')
        return attrs

    def create(self, validated_data):
        username = validated_data.get('username')
        email = validated_data.get('email')
        code = validated_data.get('code')
        auth_request = AuthRequest.objects.filter(username=username, identifier=email, code=code).first()
        auth_request.close_request()
        if auth_request.request_type == AuthRequest.REQUEST_TYPE.REGISTER:
            user = auth_request.create_new_user()
            return user, auth_request.request_type
        if auth_request.request_type == AuthRequest.REQUEST_TYPE.LOGIN:
            user = auth_request.get_user()
            return user, auth_request.request_type
        # TODO: add other request type
        user = auth_request.get_user()
        return user, auth_request.request_type
