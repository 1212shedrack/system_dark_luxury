from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
# connect the signals to ensure they are registered when the app is


def ready(self):
    import accounts.signals  # noqa: F401
    ready
