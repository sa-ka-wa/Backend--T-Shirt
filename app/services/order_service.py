from app.extensions import db
from app.models.order import Order
from app.models.product import Product


class OrderService:
    @staticmethod
    def get_all_orders():
        return Order.query.all()

    @staticmethod
    def get_order_by_id(order_id):
        return Order.query.get(order_id)

    @staticmethod
    def create_order(user_id, product_id, quantity, shipping_address):
        # Get tshirt price
        product = Product.query.get(product_id)
        if not product:
            return None

        total_amount = product.price * quantity

        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total_amount=total_amount,
            shipping_address=shipping_address
        )

        db.session.add(order)
        db.session.commit()
        return order

    @staticmethod
    def update_order(order_id, data):
        order = Order.query.get(order_id)
        if not order:
            return None

        for key, value in data.items():
            if hasattr(order, key) and key != 'id':
                setattr(order, key, value)

        db.session.commit()
        return order