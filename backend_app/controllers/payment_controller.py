import requests
import json
import base64
from datetime import datetime
from backend_app.extensions import db
from backend_app.models.payment import Payment
from backend_app.models.order import Order
import logging
import os

logger = logging.getLogger(__name__)


class MpesaService:
    def __init__(self, env='sandbox'):
        self.env = env
        self.base_url = 'https://sandbox.safaricom.co.ke' if env == 'sandbox' else 'https://api.safaricom.co.ke'

        # Load credentials from environment variables
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.shortcode = os.getenv('MPESA_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL')

        if not all([self.consumer_key, self.consumer_secret, self.shortcode, self.passkey]):
            logger.warning("M-Pesa credentials not fully configured")

    def get_access_token(self):
        """Get M-Pesa access token"""
        try:
            # Encode credentials
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            # Request token
            headers = {
                'Authorization': f'Basic {encoded_credentials}'
            }

            response = requests.get(
                f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials',
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                logger.error(f"Failed to get access token: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return None

    def initiate_stk_push(self, phone_number, amount, order_id, description="Payment"):
        """Initiate STK Push payment"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                raise Exception("Failed to get access token")

            # Format phone number (remove leading 0 if present and add 254)
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
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()

            # Prepare payload
            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": str(int(amount)),  # Convert to integer string
                "PartyA": phone_number,
                "PartyB": self.shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": f"ORDER{order_id}",
                "TransactionDesc": description[:20]  # Max 20 chars
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'{self.base_url}/mpesa/stkpush/v1/processrequest',
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code == 200:
                response_data = response.json()

                if response_data.get('ResponseCode') == '0':
                    logger.info(f"STK Push initiated for order {order_id}")
                    return {
                        'success': True,
                        'MerchantRequestID': response_data.get('MerchantRequestID'),
                        'CheckoutRequestID': response_data.get('CheckoutRequestID'),
                        'ResponseCode': response_data.get('ResponseCode'),
                        'ResponseDescription': response_data.get('ResponseDescription'),
                        'CustomerMessage': response_data.get('CustomerMessage')
                    }
                else:
                    error_msg = response_data.get('ResponseDescription', 'STK Push failed')
                    logger.error(f"STK Push error: {error_msg}")
                    raise Exception(error_msg)
            else:
                logger.error(f"STK Push request failed: {response.text}")
                raise Exception(f"STK Push request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Error initiating STK Push: {str(e)}")
            raise

    def check_payment_status(self, checkout_request_id):
        """Query payment status"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                raise Exception("Failed to get access token")

            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Generate password
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'{self.base_url}/mpesa/stkpushquery/v1/query',
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Payment status check failed: {response.text}")
                raise Exception("Failed to check payment status")

        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            raise

    def process_b2c_payment(self, phone_number, amount, remarks="Payment"):
        """Process B2C payment (for refunds or payouts)"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                raise Exception("Failed to get access token")

            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]

            # Generate security credentials
            initiator_password = os.getenv('MPESA_INITIATOR_PASSWORD', '')
            security_credential = self.generate_security_credential(initiator_password)

            payload = {
                "InitiatorName": os.getenv('MPESA_INITIATOR_NAME', 'testapi'),
                "SecurityCredential": security_credential,
                "CommandID": "BusinessPayment",
                "Amount": str(int(amount)),
                "PartyA": self.shortcode,
                "PartyB": phone_number,
                "Remarks": remarks[:100],
                "QueueTimeOutURL": os.getenv('MPESA_QUEUE_TIMEOUT_URL', 'https://your-domain.com/timeout'),
                "ResultURL": os.getenv('MPESA_RESULT_URL', 'https://your-domain.com/result'),
                "Occasion": ""
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'{self.base_url}/mpesa/b2c/v1/paymentrequest',
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"B2C payment failed: {response.text}")
                raise Exception("B2C payment failed")

        except Exception as e:
            logger.error(f"Error processing B2C payment: {str(e)}")
            raise

    def generate_security_credential(self, initiator_password):
        """Generate security credential for B2C transactions"""
        # This requires proper encryption with Safaricom's public key
        # For sandbox, you can use plain password
        # For production, implement proper RSA encryption
        if self.env == 'sandbox':
            return base64.b64encode(initiator_password.encode()).decode()
        else:
            # TODO: Implement RSA encryption for production
            raise NotImplementedError("Production security credential generation not implemented")