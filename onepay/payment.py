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
                         ('live', 'Live'),
                         ('test', 'Test'),
                     ),
                 )),
                ('service_id',
                 forms.CharField(
                     label=_('Service Id'),
                     max_length=80,
                 )),
                ('account',
                 forms.CharField(
                     label=_('Account'),
                     max_length=80,
                    
                 )),
                ('password',
                 forms.CharField(
                     label=_('Password'),
                     max_length=80,
                     widget = (forms.PasswordInput())
                
                    
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
        
        return "<div class='alert alert-info'>%s<br /></div>" % (
            _(build_absolute_uri(request.event, 'plugins:onepay:success')+"?order=123")
        )

    def order_pending_render(self, request, order) -> str:
        retry = True
        try:
            if order.payment_info and json.loads(order.payment_info)['state'] == 'pending':
                retry = True
        except KeyError:
            pass
        template = get_template('onepay/pending.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings,
               'retry': retry, 'order': order}
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

        r = requests.post('http://widget.test.stel.kz/order/create',auth=('1138', 'onepaykassa'), data={
            "serviceId":"4344", 
            "account":"test",
            "sum":int(order.total),
            "successUrl":build_absolute_uri(request.event, 'plugins:onepay:success')+"?order="+order.code,
            "errorUrl": build_absolute_uri(request.event, 'plugins:onepay:error')+"?order="+order.code,
        })
        print(r.json())
        pay_response=r.json()
        pay=ReferencedOnepayObject.objects.get_or_create(order=order, reference=pay_response["orderId"])
        print(pay)
        
        return  pay_response["formUrl"] 