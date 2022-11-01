from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    SignUpAPIView,
    SignInAPIView,
    VerifyCodeAPIView,
)

app_name = 'accounts'
urlpatterns = [
    path('signup/', SignUpAPIView.as_view(), name='signup'),
    path('signin/', SignInAPIView.as_view(), name='signin'),
    path('verify-code/', VerifyCodeAPIView.as_view(), name='verify-code'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
