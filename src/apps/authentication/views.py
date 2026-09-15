from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError, UntypedToken
from rest_framework_simplejwt.views import TokenRefreshView
from .models import CustomerSession
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer, ChangePasswordSerializer,
    VerifyEmailPinSerializer, ResendEmailPinSerializer, CustomerTokenRefreshSerializer,
)
from .sessions import issue_tokens

User = get_user_model()


def send_verification_pin_email(user):
    try:
        send_mail(
            'Подтверждение email',
            f'Ваш PIN: {user.email_verification_pin}\nКод действует {settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES} минут.',
            settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False,
        )
    except Exception as exc:
        raise APIException('Не удалось отправить PIN. Попробуйте позже.') from exc


def session_response(user):
    return {'user': UserSerializer(user).data, **issue_tokens(user)}


class PublicAuthView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = serializer.save()
                user.set_email_verification_pin(settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES)
                user.save()
                send_verification_pin_email(user)
        except IntegrityError:
            raise serializers.ValidationError({'email': 'Username или email уже используется'})
        return Response({'message': 'PIN отправлен на email', 'email': user.email, 'verification_required': True}, status=201)


class LoginView(PublicAuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=serializer.validated_data.pk)
            if not user.check_password(request.data.get('password', '')):
                raise serializers.ValidationError('Неверные учетные данные')
            return Response(session_response(user))


class VerifyEmailPinView(PublicAuthView):
    def post(self, request):
        serializer = VerifyEmailPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=serializer.validated_data['email']).first()
            if user is None:
                raise serializers.ValidationError({'email': 'Пользователь не найден'})
            if user.is_email_verified:
                raise serializers.ValidationError({'code': 'email_already_verified', 'detail': 'Email уже подтвержден. Войдите с паролем.'})
            if not user.is_email_verification_pin_valid(serializer.validated_data['pin']):
                raise serializers.ValidationError({'pin': 'Неверный или просроченный PIN'})
            user.is_email_verified = True
            user.is_active = True
            user.clear_email_verification_pin()
            user.save()
            return Response({'message': 'Email подтвержден', **session_response(user)})


class ResendEmailPinView(PublicAuthView):
    def post(self, request):
        serializer = ResendEmailPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().filter(email__iexact=serializer.validated_data['email']).first()
            if user is None:
                raise serializers.ValidationError({'email': 'Пользователь не найден'})
            if user.is_email_verified:
                raise serializers.ValidationError({'detail': 'Email уже подтвержден. Войдите с паролем.'})
            user.set_email_verification_pin(settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES)
            user.save()
            send_verification_pin_email(user)
        return Response({'message': 'PIN отправлен повторно', 'email': user.email})


class LogoutView(PublicAuthView):
    def post(self, request):
        try:
            refresh = UntypedToken(request.data.get('refresh', ''))
            if refresh.get('token_type') != 'refresh':
                raise TokenError('Expected a refresh token')
        except TokenError:
            raise serializers.ValidationError({'refresh': 'Неверный или просроченный токен'})
        with transaction.atomic():
            user = User.objects.select_for_update().filter(pk=refresh.get('user_id')).first()
            CustomerSession.objects.filter(pk=refresh.get('sid'), user=user).update(revoked=True)
            try:
                RefreshToken(request.data['refresh']).blacklist()
            except TokenError:
                pass  # A concurrent refresh may already have blacklisted this token.
        return Response({'message': 'Сессия завершена'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                serializer = self.get_serializer(user, data=request.data, partial=kwargs.get('partial', False))
                serializer.is_valid(raise_exception=True)
                email_changed = serializer.validated_data.get('email', user.email).lower() != user.email.lower()
                user = serializer.save()
                if email_changed:
                    user.is_email_verified = False
                    user.is_active = False
                    user.set_email_verification_pin(settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES)
                    user.save()
                    CustomerSession.objects.filter(user=user).update(revoked=True)
                    send_verification_pin_email(user)
                return Response({**self.get_serializer(user).data, 'verification_required': email_changed})
        except IntegrityError:
            raise serializers.ValidationError({'email': 'Этот email уже используется'})


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if not user.check_password(serializer.validated_data['old_password']):
                raise serializers.ValidationError({'old_password': 'Неверный текущий пароль'})
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password'])
            CustomerSession.objects.filter(user=user).update(revoked=True)
        return Response({'message': 'Пароль изменен. Войдите снова.'})


class CustomerTokenRefreshView(TokenRefreshView):
    serializer_class = CustomerTokenRefreshSerializer
