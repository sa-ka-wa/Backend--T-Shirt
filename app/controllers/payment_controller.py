from flask import request, jsonify
from app.extensions import db
from app.models.payment import Payment
from app.models.order import Order
from app.services.payment_service import PaymentService
from app.utils.mpesa_service import lipa_na_mpesa_stk
from app.utils.jwt_helper import get_current_user_id


class PaymentController:
    @staticmethod
    def get_payments():
        payments = PaymentService.get_all_payments()
        return jsonify([payment.to_dict() for payment in payments])

    @staticmethod
    def get_payment(payment_id):
        payment = PaymentService.get_payment_by_id(payment_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        return jsonify(payment.to_dict())

    @staticmethod
    def create_payment():
        data = request.get_json()

        required_fields = ['order_id', 'amount', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401

        order_id = data['order_id']
        amount = data['amount']
        payment_method = data['payment_method']
        status = data.get('status', 'pending')
        phone_number = data.get('phone_number')

        if payment_method == "mpesa_stk" and not phone_number:
            return jsonify({'error': 'Phone number required for M-Pesa STK push'}), 400

        payment = PaymentService.create_payment(
            user_id, order_id, amount, payment_method, status
        )

        # Trigger M-Pesa STK Push if method is mpesa_stk
        if payment_method == "mpesa_stk":
            stk_response = lipa_na_mpesa_stk(payment.amount, payment.id, phone_number)

            # Save both IDs if available
            if "CheckoutRequestID" in stk_response:
                payment.transaction_id = stk_response["CheckoutRequestID"]
            if "MerchantRequestID" in stk_response:
                payment.merchant_request_id = stk_response["MerchantRequestID"]

            # ✅ Commit before returning
            db.session.commit()

            print(f"💾 Saved Payment ID {payment.id} with CheckoutRequestID={payment.transaction_id}")

            return jsonify({
                "payment": payment.to_dict(),
                "stk_push_response": stk_response
            }), 201

        return jsonify(payment.to_dict()), 201

    @staticmethod
    def update_payment(payment_id):
        data = request.get_json()
        payment = PaymentService.update_payment(payment_id, data)

        if not payment:
            return jsonify({'error': 'Payment not found'}), 404

        return jsonify(payment.to_dict())

    @staticmethod
    def mpesa_callback():
        """Handle M-Pesa STK Push callback"""
        data = request.get_json()
        print("📩 M-PESA CALLBACK DATA:", data)

        try:
            stk_callback = data["Body"]["stkCallback"]
            result_code = stk_callback["ResultCode"]
            checkout_request_id = stk_callback.get("CheckoutRequestID")
            merchant_request_id = stk_callback.get("MerchantRequestID")
            result_desc = stk_callback["ResultDesc"]

            # 🔍 Try to find payment using either transaction_id or merchant_request_id
            payment = Payment.query.filter(
                (Payment.transaction_id == checkout_request_id) |
                (Payment.merchant_request_id == merchant_request_id)
            ).first()

            if not payment:
                print("❌ Payment not found for transaction:", checkout_request_id or merchant_request_id)
                return jsonify({"error": "Payment not found"}), 404

            # ✅ Handle success or failure
            if result_code == 0:
                payment.status = "success"

                order = Order.query.get(payment.order_id)
                if order:
                    order.status = "paid"

                # Optional: Save MpesaReceiptNumber
                metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
                for item in metadata:
                    if item["Name"] == "MpesaReceiptNumber":
                        payment.mpesa_receipt = item["Value"]

                db.session.commit()
                print(f"✅ Payment {payment.id} marked as SUCCESS (Receipt: {getattr(payment, 'mpesa_receipt', None)})")
                return jsonify({"message": "Payment successful"}), 200

            else:
                payment.status = "failed"
                db.session.commit()
                print(f"❌ Payment failed: {result_desc}")
                return jsonify({"message": result_desc}), 200

        except Exception as e:
            print("❌ Callback error:", str(e))
            return jsonify({"error": "Invalid callback data"}), 400
