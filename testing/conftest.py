from flask.testing import FlaskClient

from pytest import fixture

from main import app


@fixture
def client() -> FlaskClient:
    app.config.update(SERVER_NAME="server.org")
    with app.test_client() as client:
        with app.app_context():
            yield client
