from backend_app.extensions import db
from backend_app.models.payment import Payment
from backend_app.models.order import Order
from backend_app.models.user import User
from datetime import datetime
import requests
import json
import base64
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self):
        self.init_mpesa_config()

    def init_mpesa_config(self):
        """Initialize M-Pesa configuration from environment variables"""
        self.mpesa_shortcode = os.getenv('MPESA_SHORTCODE', '174379')
        self.mpesa_passkey = os.getenv('MPESA_PASSKEY', '')
        self.mpesa_callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://your-domain.com/api/payments/callback')
        self.mpesa_consumer_key = os.getenv('MPESA_CONSUMER_KEY', '')
        self.mpesa_consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', '')
        self.env = os.getenv('MPESA_ENV', 'sandbox')  # sandbox or production

    def generate_access_token(self):
        """Generate M-Pesa access token"""
        if not self.mpesa_consumer_key or not self.mpesa_consumer_secret:
            raise ValueError("M-Pesa credentials not configured")

        # Encode consumer key and secret
        credentials = f"{self.mpesa_consumer_key}:{self.mpesa_consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Determine API URL based on environment
        base_url = 'https://sandbox.safaricom.co.ke' if self.env == 'sandbox' else 'https://api.safaricom.co.ke'

        # Request access token from Daraja API
        headers = {
            'Authorization': f'Basic {encoded_credentials}'
        }

        try:
            response = requests.get(
                f'{base_url}/oauth/v1/generate?grant_type=client_credentials',
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()['access_token']
            else:
                logger.error(f"Failed to get access token: {response.text}")
                raise Exception(f"Failed to get M-Pesa access token: {response.status_code}")

        except Exception as e:
            logger.error(f"Error generating access token: {str(e)}")
            raise

    def initiate_stk_push(self, phone_number, amount, order_id, description="T-shirt Purchase"):
        """Initiate M-Pesa STK Push"""
        try:
            access_token = self.generate_access_token()

            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number

            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Generate password
            password = base64.b64encode(
                f"{self.mpesa_shortcode}{self.mpesa_passkey}{timestamp}".encode()
            ).decode()

            # Prepare request payload
            payload = {
                "BusinessShortCode": self.mpesa_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(int(amount)),
                "PartyA": phone_number,
                "PartyB": self.mpesa_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.mpesa_callback_url,
                "AccountReference": f"ORDER-{order_id}",
                "TransactionDesc": description[:20]  # Max 20 chars
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            base_url = 'https://sandbox.safaricom.co.ke' if self.env == 'sandbox' else 'https://api.safaricom.co.ke'

            # Send STK Push request
            response = requests.post(
                f'{base_url}/mpesa/stkpush/v1/processrequest',
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('ResponseCode') == '0':
                    # Create payment record
                    payment = Payment(
                        order_id=order_id,
                        amount=amount,
                        phone_number=phone_number,
                        payment_method='mpesa',
                        provider='safaricom',
                        merchant_request_id=data.get('MerchantRequestID'),
                        checkout_request_id=data.get('CheckoutRequestID'),
                        status='pending',
                        payment_reference=f"MPESA-{order_id}-{timestamp}"
                    )

                    db.session.add(payment)
                    db.session.commit()

                    return {
                        'success': True,
                        'checkout_request_id': data.get('CheckoutRequestID'),
                        'merchant_request_id': data.get('MerchantRequestID'),
                        'response_code': data.get('ResponseCode'),
                        'response_description': data.get('ResponseDescription'),
                        'customer_message': data.get('CustomerMessage'),
                        'payment_id': payment.id
                    }
                else:
                    error_msg = data.get('ResponseDescription', 'STK Push failed')
                    logger.error(f"STK Push error: {error_msg}")
                    raise Exception(error_msg)
            else:
                logger.error(f"STK Push request failed: {response.text}")
                raise Exception(f"STK Push request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error in STK Push: {str(e)}")
            raise

    def check_payment_status(self, checkout_request_id: str):
        """Check M-Pesa payment status"""
        try:
            access_token = self.generate_access_token()

            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Generate password
            password = base64.b64encode(
                f"{self.mpesa_shortcode}{self.mpesa_passkey}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": self.mpesa_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            base_url = 'https://sandbox.safaricom.co.ke' if self.env == 'sandbox' else 'https://api.safaricom.co.ke'

            response = requests.post(
                f'{base_url}/mpesa/stkpushquery/v1/query',
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Find and update payment
                payment = Payment.query.filter_by(
                    checkout_request_id=checkout_request_id
                ).first()

                if payment:
                    result_code = data.get('ResultCode')
                    result_desc = data.get('ResultDesc')

                    if result_code == 0:
                        payment.status = 'completed'
                        payment.mpesa_receipt_number = data.get('MpesaReceiptNumber')
                        payment.transaction_id = data.get('TransactionID')
                        payment.completed_at = datetime.utcnow()
                        payment.result_code = result_code
                        payment.result_description = result_desc

                        # Update order status
                        order = Order.query.get(payment.order_id)
                        if order:
                            order.status = 'processing'
                            order.updated_at = datetime.utcnow()
                    else:
                        payment.status = 'failed'
                        payment.result_description = result_desc
                        payment.failed_at = datetime.utcnow()
                        payment.result_code = result_code

                    db.session.commit()

                return data
            else:
                logger.error(f"Payment status check failed: {response.text}")
                raise Exception("Failed to check payment status")

        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            raise

    def create_payment(self, order_id, amount, payment_method, **kwargs):
        """Create a new payment record"""
        try:
            order = Order.query.get(order_id)
            if not order:
                raise ValueError("Order not found")

            if order.status == 'cancelled':
                raise ValueError("Cannot create payment for cancelled order")

            # Create payment record
            payment = Payment(
                order_id=order_id,
                user_id=order.user_id,
                amount=amount,
                payment_method=payment_method,
                status='pending',
                currency='KES',
                payment_reference=f"PAY-{order_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                metadata=kwargs.get('metadata', {})
            )

            if payment_method == 'mpesa' and 'phone_number' in kwargs:
                payment.phone_number = kwargs['phone_number']
                payment.provider = 'safaricom'

            db.session.add(payment)
            db.session.commit()

            return payment

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise

    def update_payment_status(self, payment_id, status, transaction_data=None):
        """Update payment status"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise ValueError("Payment not found")

            payment.status = status
            payment.updated_at = datetime.utcnow()

            if status == 'completed':
                payment.completed_at = datetime.utcnow()

                # Update order status
                order = Order.query.get(payment.order_id)
                if order:
                    order.status = 'processing'
                    order.updated_at = datetime.utcnow()

            elif status == 'failed':
                payment.failed_at = datetime.utcnow()

            if transaction_data:
                if 'transaction_id' in transaction_data:
                    payment.transaction_id = transaction_data['transaction_id']
                if 'mpesa_receipt_number' in transaction_data:
                    payment.mpesa_receipt_number = transaction_data['mpesa_receipt_number']
                if 'result_code' in transaction_data:
                    payment.result_code = transaction_data['result_code']
                if 'result_description' in transaction_data:
                    payment.result_description = transaction_data['result_description']

            db.session.commit()
            return payment

        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}")
            raise

    def process_mpesa_callback(self, callback_data: Dict[str, Any]):
        """Process M-Pesa STK Push callback"""
        try:
            logger.info(f"Processing M-Pesa callback: {json.dumps(callback_data)}")

            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})

            checkout_request_id = stk_callback.get('CheckoutRequestID')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')

            if not checkout_request_id:
                logger.error("No CheckoutRequestID in callback")
                return {"ResultCode": 1, "ResultDesc": "Invalid callback data"}

            # Find payment
            payment = Payment.query.filter_by(
                checkout_request_id=checkout_request_id
            ).first()

            if not payment and merchant_request_id:
                payment = Payment.query.filter_by(
                    merchant_request_id=merchant_request_id
                ).first()

            if not payment:
                logger.error(f"Payment not found for callback: {checkout_request_id}")
                return {"ResultCode": 1, "ResultDesc": "Payment not found"}

            # Extract metadata from callback
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            metadata = {}
            mpesa_receipt_number = None
            transaction_id = None

            for item in callback_metadata:
                name = item.get('Name')
                value = item.get('Value')
                if name:
                    metadata[name] = value
                    if name == 'MpesaReceiptNumber':
                        mpesa_receipt_number = value
                    elif name == 'TransactionID':
                        transaction_id = value

            # Update payment based on result code
            if result_code == 0:
                # Payment successful
                transaction_data = {
                    'transaction_id': transaction_id,
                    'mpesa_receipt_number': mpesa_receipt_number,
                    'result_code': result_code,
                    'result_description': result_desc
                }

                self.update_payment_status(payment.id, 'completed', transaction_data)
                logger.info(f"Payment {payment.id} completed successfully. Receipt: {mpesa_receipt_number}")
            else:
                # Payment failed
                transaction_data = {
                    'result_code': result_code,
                    'result_description': result_desc
                }

                self.update_payment_status(payment.id, 'failed', transaction_data)
                logger.warning(f"Payment {payment.id} failed: {result_desc}")

            return {"ResultCode": 0, "ResultDesc": "Success"}

        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return {"ResultCode": 1, "ResultDesc": "Internal server error"}

    def get_payment_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID"""
        return Payment.query.get(payment_id)

    def get_payment_by_reference(self, payment_reference: str) -> Optional[Payment]:
        """Get payment by reference"""
        return Payment.query.filter_by(payment_reference=payment_reference).first()

    def get_order_payments(self, order_id: int):
        """Get all payments for an order"""
        return Payment.query.filter_by(order_id=order_id).order_by(Payment.created_at.desc()).all()

    def get_user_payments(self, user_id: int, limit: int = 50, offset: int = 0):
        """Get payments for a user"""
        query = Payment.query.filter_by(user_id=user_id)
        total = query.count()
        payments = query.order_by(Payment.created_at.desc()).limit(limit).offset(offset).all()

        return {
            'payments': payments,
            'total': total,
            'limit': limit,
            'offset': offset
        }