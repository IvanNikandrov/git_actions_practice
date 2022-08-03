from http import HTTPStatus
from flask import url_for


def test_add_post(client):
    data = {
        "name": 'John Ivanov',
        "post": 'This man is legend of badminton',
        "url": 'urlurdfgl'
    }
    url = url_for('addPost')
    response = client.post(url, data=data)
    assert response.status_code < HTTPStatus.BAD_REQUEST
