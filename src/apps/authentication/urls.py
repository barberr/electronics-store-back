from django.urls import path
from .views import (
    RegisterView, LoginView, VerifyEmailPinView, ResendEmailPinView, LogoutView,
    UserProfileView, ChangePasswordView, CustomerTokenRefreshView,
)

urlpatterns = [
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomerTokenRefreshView.as_view(), name='token_refresh'),
    path('token/custom-refresh/', CustomerTokenRefreshView.as_view(), name='custom_token_refresh'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email-pin/', VerifyEmailPinView.as_view(), name='verify_email_pin'),
    path('resend-email-pin/', ResendEmailPinView.as_view(), name='resend_email_pin'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
