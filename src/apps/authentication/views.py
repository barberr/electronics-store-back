# src/apps/authentication/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from .serializers import *
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


def send_verification_pin_email(user):
    subject = 'Email verification PIN'
    message = (
        f'Your verification PIN is: {user.email_verification_pin}\n'
        f'The PIN is valid for {settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES} minutes.'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.set_email_verification_pin(settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES)
        user.save(update_fields=['email_verification_pin', 'email_verification_pin_expires_at'])

        try:
            send_verification_pin_email(user)
        except Exception:
            user.delete()
            return Response(
                {'error': 'Unable to send verification PIN email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'message': 'User registered. Verification PIN has been sent to email.',
                'email': user.email,
                'verification_required': True,
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailPinView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = VerifyEmailPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        pin = serializer.validated_data['pin']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email was not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_email_verified:
            return Response(
                {'message': 'Email is already verified'},
                status=status.HTTP_200_OK
            )

        if not user.is_email_verification_pin_valid(pin):
            return Response(
                {'error': 'Invalid or expired PIN'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_email_verified = True
        user.is_active = True
        user.clear_email_verification_pin()
        user.save(update_fields=[
            'is_email_verified',
            'is_active',
            'email_verification_pin',
            'email_verification_pin_expires_at',
        ])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Email verified successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            status=status.HTTP_200_OK
        )


class ResendEmailPinView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ResendEmailPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email was not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_email_verified:
            return Response(
                {'message': 'Email is already verified'},
                status=status.HTTP_200_OK
            )

        user.set_email_verification_pin(settings.EMAIL_VERIFICATION_PIN_TTL_MINUTES)
        user.save(update_fields=['email_verification_pin', 'email_verification_pin_expires_at'])

        try:
            send_verification_pin_email(user)
        except Exception:
            return Response(
                {'error': 'Unable to send verification PIN email'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                'message': 'Verification PIN has been resent',
                'email': user.email,
            },
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # Просто подтверждаем logout, токены удаляются на фронте
        return Response({"message": "Logged out"}, status=status.HTTP_200_OK)
    
    # def post(self, request):
    #     try:
    #         refresh_token = request.data["refresh"]
    #         token = RefreshToken(refresh_token)
    #         token.blacklist()
    #         return Response(status=status.HTTP_205_RESET_CONTENT)
    #     except Exception as e:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response({"message": "Password updated successfully"}, 
                          status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, 
                          status=status.HTTP_400_BAD_REQUEST)
