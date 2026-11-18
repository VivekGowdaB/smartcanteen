import seed
from app.extensions import db
from app.models.menu import MenuItem
from app.models.order import PickupSlotConfig
from app.models.user import User


def test_seed_if_empty_creates_demo_data_once(app, monkeypatch):
    with app.app_context():
        db.session.query(PickupSlotConfig).delete()
        db.session.commit()

    monkeypatch.setattr(seed, "create_app", lambda config_name=None: app)

    seed.seed_if_empty()

    with app.app_context():
        admin = User.query.filter_by(username="admin").one()
        assert admin.check_password("Admin@123")
        dish = MenuItem.query.filter_by(name="Masala Dosa").one()
        dish.stock = 9
        db.session.commit()

    seed.seed_if_empty()

    with app.app_context():
        assert User.query.count() == 4
        assert MenuItem.query.filter_by(name="Masala Dosa").one().stock == 9
