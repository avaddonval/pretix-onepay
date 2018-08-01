from django.apps import AppConfig
from django.utils.translation import ugettext_lazy


class OnepayApp(AppConfig):
    name = 'onepay'
    verbose_name = 'Onepay'

    class PretixPluginMeta:
        name = ugettext_lazy('Onepay')
        author = 'cybersec'
        description = ugettext_lazy('onepay kassa24 payments')
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'onepay.OnepayApp'
