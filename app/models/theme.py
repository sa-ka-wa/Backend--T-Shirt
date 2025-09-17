from app.extensions import db


class Theme(db.Model):
    __tablename__ = 'themes'

    id = db.Column(db.Integer, primary_key=True)
    style_tag = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "artsy", "afrobeat", "rock"
    name = db.Column(db.String(100), nullable=False)
    colors = db.Column(db.JSON, nullable=False)  # {primary: "#color", secondary: "#color", ...}
    fonts = db.Column(db.JSON, nullable=False)  # {primary: "Font Name", secondary: "Font Name"}
    layout_config = db.Column(db.JSON, nullable=False)  # UI layout preferences
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'style_tag': self.style_tag,
            'name': self.name,
            'colors': self.colors,
            'fonts': self.fonts,
            'layout_config': self.layout_config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }