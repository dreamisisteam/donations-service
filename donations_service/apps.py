from django.apps import AppConfig


class DonationsConfig(AppConfig):
    """ Сервис донатов """
    name = 'donations_service'
    verbose_name = 'Service of donations'

    def ready(self):
        try:
            from donations_service import tasks  # noqa: F401
        except ImportError:
            pass
