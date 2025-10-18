from backend_app.extensions import db
from backend_app.models.tshirt import TShirt


class TShirtService:
    @staticmethod
    def get_all_tshirts():
        return TShirt.query.filter_by(is_active=True).all()

    @staticmethod
    def get_tshirts_by_style(style_tag):
        return TShirt.query.filter_by(style_tag=style_tag, is_active=True).all()

    @staticmethod
    def get_tshirt_by_id(tshirt_id):
        return TShirt.query.filter_by(id=tshirt_id, is_active=True).first()

    @staticmethod
    def create_tshirt(title, image_url, price, style_tag, description=None, category=None, artist=None):
        tshirt = TShirt(
            title=title,
            description=description,
            image_url=image_url,
            price=price,
            category=category,
            style_tag=style_tag,
            artist=artist
        )
        db.session.add(tshirt)
        db.session.commit()
        return tshirt

    @staticmethod
    def update_tshirt(tshirt_id, data):
        tshirt = TShirtService.get_tshirt_by_id(tshirt_id)
        if not tshirt:
            return None

        for key, value in data.items():
            if hasattr(tshirt, key):
                setattr(tshirt, key, value)

        db.session.commit()
        return tshirt

    @staticmethod
    def delete_tshirt(tshirt_id):
        tshirt = TShirtService.get_tshirt_by_id(tshirt_id)
        if not tshirt:
            return False

        tshirt.is_active = False
        db.session.commit()
        return True