from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from accounts.api.serializers import (
    SignUpAPISerializer,
    VerifyCodeAPISerializer,
    SignInAPISerializer,
)
from accounts.models import AuthRequest


class SignUpAPIView(GenericAPIView):
    """SingUp API View

        This view get user username and email
        create record in AuthRequest model and send code to user
        """
    serializer_class = SignUpAPISerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            auth_request = serializer.save()
            response_code, error_message = auth_request.send_code()
            if response_code != status.HTTP_200_OK:
                return Response({'message': error_message}, status=response_code)
            return Response({'message': 'Code sent to your email'}, status=status.HTTP_200_OK)
        message = [0] * len(serializer.errors)
        for i, key in enumerate(serializer.errors):
            message[i] = serializer.errors[key][0]
        return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)


class SignInAPIView(GenericAPIView):
    """SignIn API View

    This view get user Identifier and password
    check user is registered and password is correct
    """
    serializer_class = SignInAPISerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            auth_request = serializer.save()
            response_code, error_message = auth_request.send_code()
            if response_code != status.HTTP_200_OK:
                return Response({'message': error_message}, status=response_code)
            response_data = {
                'message': 'Code sent to your email',
                'username': auth_request.username,
                'email': auth_request.identifier,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        message = [0] * len(serializer.errors)
        for i, key in enumerate(serializer.errors):
            message[i] = serializer.errors[key][0]
        return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeAPIView(GenericAPIView):
    """Verify Code API View

        This view get user username , email and code
        check code complete request status and with request_type do next step
        """
    serializer_class = VerifyCodeAPISerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user, request_type = serializer.save()
            response_data = {
                'user': {
                    'username': user.username,
                    'email': user.email,
                }
            }
            if request_type == AuthRequest.REQUEST_TYPE.REGISTER:
                response_data['message'] = 'your registration is complete'
            elif request_type == AuthRequest.REQUEST_TYPE.LOGIN:
                response_data['message'] = 'your login is complete'
                # login user in jwt and generate access and refresh token
                access_token = AccessToken.for_user(user)
                refresh_token = RefreshToken.for_user(user)
                response_data['access_token'] = str(access_token)
                response_data['refresh_token'] = str(refresh_token)
            return Response(response_data, status=status.HTTP_200_OK)
        message = [0] * len(serializer.errors)
        for i, key in enumerate(serializer.errors):
            message[i] = serializer.errors[key][0]
        return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)
