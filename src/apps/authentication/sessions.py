from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomerSession


def require_verified_user(user):
    if not user.is_active or not user.is_email_verified:
        raise AuthenticationFailed('Email не подтвержден или аккаунт отключен', code='email_not_verified')


def issue_tokens(user):
    require_verified_user(user)
    session = CustomerSession.objects.create(user=user)
    refresh = RefreshToken.for_user(user)
    refresh['sid'] = str(session.pk)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class CustomerJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        require_verified_user(user)
        if not CustomerSession.objects.filter(
            pk=validated_token.get('sid'), user=user, revoked=False,
        ).exists():
            raise AuthenticationFailed('Сессия завершена', code='session_revoked')
        return user
