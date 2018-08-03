import json
import logging
from .models import ReferencedOnepayObject
from .payment import Onepay
from django.contrib import messages
from django.core import signing
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from pretix.base.models import Order, Quota, RequiredAction
from pretix.base.payment import PaymentException
from pretix.base.services.orders import mark_order_paid
from pretix.control.permissions import event_permission_required
from pretix.multidomain.urlreverse import eventreverse


logger = logging.getLogger('pretix.plugins.onepay')





def success(request, *args, **kwargs):
    if request.GET.get('order'):
        order = Order.objects.get(code=request.GET.get('order'))
    else:
        order = None
    print("order",order.total)
    if order:
        return redirect(eventreverse(request.event, 'presale:event.order', kwargs={
            'order': order.code,
            'secret': order.secret
        }) + ('?paid=yes' if order.status == Order.STATUS_PAID else ''))
    else:
        return redirect(eventreverse(request.event, 'presale:event.checkout', kwargs={'step': 'payment'}))

    

def error(request, *args, **kwargs):

    if request.GET.get('order'):
        order = Order.objects.get(code=request.GET.get('order'))
    else:
        order = None

    if order:
        return redirect(eventreverse(request.event, 'presale:event.order', kwargs={
            'order': order.code,
            'secret': order.secret
        }) + ('?paid=yes' if order.status == Order.STATUS_PAID else ''))
    else:
        return redirect(eventreverse(request.event, 'presale:event.checkout', kwargs={'step': 'payment'}))


@csrf_exempt
@require_POST
def callback(request, *args, **kwargs):
    data = json.loads(request.body)

    print('__')
    print('__')
    print('__')
    print('__')
    print('__')
    print('__')
    onepay=ReferencedOnepayObject.objects.get(reference=data["orderId"])
    if(data["status"]==1):
        mark_order_paid(onepay.order, 'onepay', data["transaction"])
    else:
        onepay.order.status = Order.STATUS_CANCELED
        onepay.order.save()



    return HttpResponse(onepay.order.status)