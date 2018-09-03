import json
import logging
import urllib.parse
import requests
from collections import OrderedDict
from pprint import pprint
import paypalrestsdk
from django import forms
from django.contrib import messages
from django.core import signing
from django.template.loader import get_template
from django.utils.translation import ugettext as __, ugettext_lazy as _

from pretix.base.decimal import round_decimal
from pretix.base.models import Order, Quota, RequiredAction
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.services.mail import SendMailException
from pretix.base.services.orders import mark_order_paid, mark_order_refunded
from pretix.helpers.urls import build_absolute_uri as build_global_uri
from pretix.multidomain.urlreverse import build_absolute_uri
from .models import ReferencedOnepayObject
from pretix.base.settings import SettingsSandbox
logger = logging.getLogger('pretix.plugins.onepay')

ONEPAY_TEST_URL = 'http://widget.test.stel.kz/order/create'
ONEPAY_PRODUCTION_URL='https://onepay.kassa24.kz/transaction'
ONEPAY_TEST_ACCOUNT = 'test'
ONEPAY_TEST_SERVICE_ID = 4344
ONEPAY_TEST_USER = '1138'
ONEPAY_TEST_PASSWORD = 'onepaykassa'

class Onepay(BasePaymentProvider):
    identifier = 'onepay'
    verbose_name = _('Onepay')
    payment_form_fields = OrderedDict([
    ])
    

    @property
    def settings_form_fields(self):
        d = OrderedDict(
        [
                ('server',
                 forms.ChoiceField(
                     label=_('Server'),
                     initial='test',
                     choices=(
                         ('live', _('Live')),
                         ('test', _('Test')),
                     ),
                 )),
                ('service_id',
                 forms.CharField(
                     label=_('Service Id'),
                     max_length=80,
                     initial=ONEPAY_TEST_SERVICE_ID
                 )),
                ('account',
                 forms.CharField(
                     label=_('Account'),
                     max_length=80,
                     initial=ONEPAY_TEST_ACCOUNT
                 )),
                 ('login',
                 forms.CharField(
                     label=_('Login'),
                     max_length=80,
                     initial=ONEPAY_TEST_USER
                 )),
                ('password',
                 forms.CharField(
                     label=_('Password'),
                     max_length=80,
                     widget = (forms.PasswordInput()),
                     initial = ONEPAY_TEST_PASSWORD
                    
                 )),
                 ('site_url',
                 forms.CharField(
                     label=_('Site URL'),
                     max_length=80,
                 ))
            ] +list(super().settings_form_fields.items())
        )
        d.move_to_end('_enabled', last=False)
        return d
    def payment_is_valid_session(self, request):
        return True

    def payment_form_render(self, request) -> str:
        template = get_template('onepay/checkout_payment_form.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings}
        return template.render(ctx)


    def checkout_confirm_render(self,request):
        
        return "%s" % (
            _("ATTENTION! Payment system takes 2% when paying via credit card. If your card do not support 3D Secure, then you cannot pay using credit card. We recommend to pay via Kassa24 account.")
        )

    def order_pending_render(self, request, order) -> str:
        
        template = get_template('onepay/pending.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings,
             'order': order,'status':order.status}
        return template.render(ctx)


    def payment_perform(self, request, order) -> str:
        """
        Will be called if the user submitted his order successfully to initiate the
        payment process.

        It should return a custom redirct URL, if you need special behavior, or None to
        continue with default behavior.

        On errors, it should use Django's message framework to display an error message
        to the user (or the normal form validation error messages).

        :param order: The order object
        """
        kwargs = {}
        if request.resolver_match and 'cart_namespace' in request.resolver_match.kwargs:
            kwargs['cart_namespace'] = request.resolver_match.kwargs['cart_namespace']
        if(self.settings.get('server')=='test'):
            url=ONEPAY_TEST_URL
        else: 
            url=ONEPAY_PRODUCTION_URL
        url_back=self.settings.get('site_url')+'/'+order.event.organizer.slug+'/'+order.event.slug+'/onepay/'
        
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        print(url_back+"success/?order="+order.code)
        print(build_absolute_uri(request.event, 'plugins:onepay:success')+"?order="+order.code)
        
        r = requests.post(url, auth=(self.settings.get('login'), self.settings.get('password')), data={
            "serviceId": self.settings.get('service_id'), 
            "userId": self.settings.get('account'),
            "summ": int(order.total),
            "successUrl": url_back+"success/?order="+order.code,
            "errorUrl": url_back+"error/?order="+order.code,
            
        })
    
        pay_response=r.json()
        
        
        if(pay_response["orderId"]):
            pay=ReferencedOnepayObject.objects.get_or_create(order=order, reference=pay_response["orderId"])
            return  pay_response["formUrl"] 
        else:
            return build_absolute_uri(request.event,'presale:event.checkout.start')