from django.conf.urls import include, url

from pretix.multidomain import event_url

from .views import error, callback, success

event_patterns = [
    url(r'^onepay/', include([
        url(r'^abort/$', error, name='error'),
        url(r'^success/$', success, name='success'),
        

        url(r'w/(?P<cart_namespace>[a-zA-Z0-9]{16})/error/', error, name='error'),
        url(r'w/(?P<cart_namespace>[a-zA-Z0-9]{16})/success/', success, name='success'),

        
    ])),
]


urlpatterns = [
    url(r'^onepay/callback/$', callback, name='callback'),
]
