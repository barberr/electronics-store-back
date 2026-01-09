# src/apps/authentication/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from django.views.decorators.csrf import csrf_exempt
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
    RefreshTokenView,
    LoginView
)

def api_no_csrf(view):
    """Универсальный csrf_exempt для url patterns"""
    if hasattr(view, 'as_view'):
        return csrf_exempt(view.as_view())
    return csrf_exempt(view)

urlpatterns = [
    # JWT endpoints
    path('token/', api_no_csrf(CustomTokenObtainPairView), name='token_obtain_pair'),
    path('token/refresh/', api_no_csrf(TokenRefreshView), name='token_refresh'),
    path('token/custom-refresh/', api_no_csrf(RefreshTokenView), name='custom_token_refresh'),
    
    # Auth endpoints
    #path('login/', LoginView.as_view(), name='login'),
    path('login/', api_no_csrf(LoginView), name='login'),
    path('register/', api_no_csrf(RegisterView), name='register'),
    path('logout/', api_no_csrf(LogoutView), name='logout'),
    
    # User endpoints
    path('profile/', api_no_csrf(UserProfileView), name='user_profile'),
    path('change-password/', api_no_csrf(ChangePasswordView), name='change_password'),
]