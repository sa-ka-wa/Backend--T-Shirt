import base64, requests, datetime, os
from requests.auth import HTTPBasicAuth

MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_TEST_PHONE = os.getenv("MPESA_TEST_PHONE")
MPESA_ENV = os.getenv("MPESA_ENV", "sandbox")
PROCESS_REQUEST_URL = os.getenv("PROCESS_REQUEST_URL")
MPESA_CALLBACK_URL= os.getenv("MPESA_CALLBACK_URL")



def get_access_token():
    if MPESA_ENV == "production":
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    r = requests.get(url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
    return r.json().get("access_token")


def lipa_na_mpesa_stk(amount, order_id, phone_number):
    access_token = get_access_token()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()


    # ✅ Normalize phone number
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    elif phone_number.startswith("+"):
        phone_number = phone_number.replace("+", "")


    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": MPESA_TEST_PHONE,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "processrequestUrl": PROCESS_REQUEST_URL,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": f"Order{order_id}",
        "TransactionDesc": f"Payment for Order {order_id}"
    }

    stk_url = (
        "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        if MPESA_ENV == "production"
        else "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(stk_url, json=payload, headers=headers)
    return response.json()
