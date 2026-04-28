from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(BaseBackend):
    """Admin logs in with email + password."""
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=identifier, role='admin')
            if not user.is_active:
                return None
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class StaffNumberBackend(BaseBackend):
    """Cashier logs in with staff number + password."""
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        try:
            user = User.objects.get(staff_number=identifier, role='cashier')
            if not user.is_active:
                return None
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class UsernameBackend(BaseBackend):
    """Customer logs in with username + password."""
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=identifier, role='customer')
            if not user.is_active:
                return None
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
