import http.client
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order, OrderItem,Cart  # Assuming your models are in orders/models.py
from django.db import transaction
import logging

logger = logging.getLogger(__name__)  # Initialize a logger


def verify_payment(transaction_id):
    """
    Verifies the transaction with Paystack and processes the order.
    """
    try:
        # 1. Verify the transaction with Paystack's API
        paystack_secret_key = settings.PAYSTACK_SECRET_KEY
        conn = http.client.HTTPSConnection("api.paystack.co")
        headers = {'Authorization': f'Bearer {paystack_secret_key}'}
        conn.request('GET', f'/transaction/verify/{transaction_id}', headers=headers)
        res = conn.getresponse()
        print(res.status, res.reason)
        res_body = res.read().decode('utf-8')
        conn.close()

        verification_data = json.loads(res_body)

        if not verification_data.get('status'):
            logger.error(f"Paystack verification failed: {res_body}")
            return False   #  Payment was not successful on Paystack

        if verification_data['data']['status'] != 'success':
            logger.warning(f"Paystack transaction was not successful: {res_body}")
            return False  #  Payment was not successful on Paystack
        # 2. Get the order
        try:
            order = Order.objects.get(order_id=transaction_id)
            status = order.confirm_payment(transaction_id)
            return status
            
        except Order.DoesNotExist:
            logger.error(f"Order not found for transaction reference: {transaction_id}")
            return HttpResponse(status=404)  # Order not found.  Potentially a serious issue.

       
    except Exception as e:
        logger.exception("Error processing Paystack webhook")
        return HttpResponse(status=500)  # Internal server error
