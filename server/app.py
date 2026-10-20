from flask import Flask
from flask_migrate import Migrate

from models import db
from schemas import ma
from routes import api

migrate = Migrate()


def create_app(test_config=None):
    """Create and configure the Flask application.

    Tests pass their own config (for example an in-memory database)
    so they never touch your real app.db.
    """
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(api)

    return app


# Kept at module level so seed.py and `flask db` commands keep working.
app = create_app()


if __name__ == '__main__':
    app.run(port=5555, debug=True)