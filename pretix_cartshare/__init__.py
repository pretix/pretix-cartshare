from django.apps import AppConfig
from pretix.base.plugins import PluginType


class CartshareApp(AppConfig):
    name = 'pretix_cartshare'
    verbose_name = "Cartshare"

    class PretixPluginMeta:
        name = 'Cart sharing'
        author = 'Raphael Michel'
        description = 'Allows you to prepare a cart and share it with a customer.'
        visible = True
        version = '1.0'
        type = PluginType.ADMINFEATURE

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_cartshare.CartshareApp'
