from app.extensions import db
from app.models.theme import Theme


class StyleService:
    @staticmethod
    def get_theme_by_style_tag(style_tag):
        return Theme.query.filter_by(style_tag=style_tag, is_active=True).first()

    @staticmethod
    def get_all_themes():
        return Theme.query.filter_by(is_active=True).all()

    @staticmethod
    def create_theme(style_tag, name, colors, fonts, layout_config):
        theme = Theme(
            style_tag=style_tag,
            name=name,
            colors=colors,
            fonts=fonts,
            layout_config=layout_config
        )
        db.session.add(theme)
        db.session.commit()
        return theme