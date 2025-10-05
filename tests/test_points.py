import pytest
from server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_points_page_shows_club(client):
    res = client.get('/points')
    assert res.status_code == 200
    assert b"Simply Lift" in res.data