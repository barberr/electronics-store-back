from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = 'Original-client-pass-934!'


class CustomerAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='customer', email='customer@example.com', password=PASSWORD,
            is_email_verified=True,
        )

    def login(self):
        response = self.client.post('/login/', {'username': 'customer', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        return response.data

    def authorize(self, tokens):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])

    def test_rotation_rejects_reused_refresh(self):
        tokens = self.login()
        rotated = self.client.post('/token/refresh/', {'refresh': tokens['refresh']})
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(rotated.data['refresh'], tokens['refresh'])
        self.assertEqual(self.client.post('/token/refresh/', {'refresh': tokens['refresh']}).status_code, 401)
        self.authorize(rotated.data)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_logout_revokes_current_session_only(self):
        first, second = self.login(), self.login()
        self.assertEqual(self.client.post('/logout/', {'refresh': first['refresh']}).status_code, 200)
        self.authorize(first)
        self.assertEqual(self.client.get('/profile/').status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post('/token/refresh/', {'refresh': first['refresh']}).status_code, 401)
        self.authorize(second)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_logout_after_rotation(self):
        tokens = self.login()
        rotated = self.client.post('/token/refresh/', {'refresh': tokens['refresh']}).data
        self.assertEqual(self.client.post('/logout/', {'refresh': rotated['refresh']}).status_code, 200)
        self.authorize(tokens)
        self.assertEqual(self.client.get('/profile/').status_code, 401)
        self.authorize(rotated)
        self.assertEqual(self.client.get('/profile/').status_code, 401)

    def test_change_password_post_revokes_all_sessions(self):
        first, second = self.login(), self.login()
        self.authorize(first)
        response = self.client.post('/change-password/', {'old_password': PASSWORD, 'new_password': 'New-client-pass-836!'})
        self.assertEqual(response.status_code, 200)
        self.authorize(second)
        self.assertEqual(self.client.get('/profile/').status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post('/token/refresh/', {'refresh': second['refresh']}).status_code, 401)
        self.assertEqual(self.client.post('/login/', {'username':'customer', 'password':'New-client-pass-836!'}).status_code, 200)

    def test_wrong_old_password_keeps_session(self):
        self.authorize(self.login())
        self.assertEqual(self.client.post('/change-password/', {'old_password':'wrong', 'new_password':'New-client-pass-836!'}).status_code, 400)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_email_change_requires_verification_and_revokes_session(self):
        tokens = self.login()
        self.authorize(tokens)
        response = self.client.patch('/profile/', {'email': 'Changed@Example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['verification_required'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        self.assertFalse(self.user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.get('/profile/').status_code, 401)
        self.client.credentials()
        verified = self.client.post('/verify-email-pin/', {'email':'changed@example.com', 'pin':self.user.email_verification_pin})
        self.assertEqual(verified.status_code, 200)
        self.authorize(verified.data)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_email_unique_case_insensitive_on_update(self):
        User.objects.create_user(username='other', email='other@example.com', password=PASSWORD)
        self.authorize(self.login())
        self.assertEqual(self.client.patch('/profile/', {'email':'OTHER@example.com'}).status_code, 400)

    def test_unverified_user_rejected_by_all_token_endpoints(self):
        tokens = self.login()
        self.user.is_email_verified = False
        self.user.save()
        self.client.credentials()
        for path in ('/login/', '/token/'):
            self.assertIn(self.client.post(path, {'username':'customer', 'password':PASSWORD}).status_code, (400,401))
        for path in ('/token/refresh/', '/token/custom-refresh/'):
            self.assertEqual(self.client.post(path, {'refresh':tokens['refresh']}).status_code, 401)
        self.authorize(tokens)
        self.assertEqual(self.client.get('/profile/').status_code, 401)

    def test_already_verified_pin_does_not_report_login_success(self):
        self.assertEqual(self.client.post('/verify-email-pin/', {'email':self.user.email,'pin':'000000'}).status_code, 400)

    def test_registration_verification_flow(self):
        response = self.client.post('/register/', {'username':'new', 'email':'New@Example.com', 'password':PASSWORD, 'password2':PASSWORD})
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='new')
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(self.client.post('/verify-email-pin/', {'email':user.email,'pin':'invalid'}).status_code, 400)
        response = self.client.post('/verify-email-pin/', {'email':user.email,'pin':user.email_verification_pin})
        self.assertEqual(response.status_code, 200)
        self.authorize(response.data)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_logout_with_rotated_old_refresh_revokes_descendants(self):
        tokens = self.login()
        rotated = self.client.post('/token/refresh/', {'refresh': tokens['refresh']}).data
        self.assertEqual(self.client.post('/logout/', {'refresh': tokens['refresh']}).status_code, 200)
        self.authorize(rotated)
        self.assertEqual(self.client.get('/profile/').status_code, 401)

    def test_email_send_failure_rolls_back_email_and_session(self):
        from unittest.mock import patch
        self.authorize(self.login())
        with patch('apps.authentication.views.send_mail', side_effect=RuntimeError('SMTP unavailable')):
            response = self.client.patch('/profile/', {'email':'changed@example.com'})
        self.assertEqual(response.status_code, 500)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'customer@example.com')
        self.assertTrue(self.user.is_email_verified)
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_resend_replaces_pin_and_expired_pin_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        self.user.is_email_verified = False
        self.user.is_active = False
        self.user.email_verification_pin = '123456'
        self.user.email_verification_pin_expires_at = timezone.now() - timedelta(seconds=1)
        self.user.save()
        self.assertEqual(self.client.post('/verify-email-pin/', {'email':self.user.email, 'pin':'123456'}).status_code, 400)
        self.assertEqual(self.client.post('/resend-email-pin/', {'email':self.user.email}).status_code, 200)
        self.user.refresh_from_db()
        self.assertGreater(self.user.email_verification_pin_expires_at, timezone.now())
        self.assertEqual(self.client.post('/verify-email-pin/', {'email':self.user.email, 'pin':self.user.email_verification_pin}).status_code, 200)

    def test_database_rejects_duplicate_email_identity(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username='duplicate', email='CUSTOMER@example.com', password=PASSWORD)

    def test_same_email_case_change_keeps_verified_session(self):
        self.authorize(self.login())
        result = self.client.patch('/profile/', {'email':'CUSTOMER@example.com'})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.data['verification_required'])
        self.assertTrue(result.data['is_email_verified'])
        self.assertEqual(self.client.get('/profile/').status_code, 200)

    def test_legacy_tokens_without_session_are_rejected(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(token.access_token))
        self.assertEqual(self.client.get('/profile/').status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post('/token/refresh/', {'refresh': str(token)}).status_code, 401)
