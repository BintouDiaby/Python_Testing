import json
import server
from server import app
import pytest


@pytest.fixture
def client():
    app.config['TESTING'] = True
    # reset global in-memory state before each test
    server.clubs = server.loadClubs()
    server.competitions = server.loadCompetitions()
    with app.test_client() as client:
        yield client


def _load_first_club_and_competition():
    with open('clubs.json') as f:
        clubs = json.load(f)['clubs']
    with open('competitions.json') as f:
        competitions = json.load(f)['competitions']
    return clubs[0], competitions[0]


def test_purchase_more_than_available(client):
    club, competition = _load_first_club_and_competition()
    available = int(competition.get('numberOfPlaces', 0))
    # try to book more places than available
    res = client.post('/purchasePlaces', data={
        'competition': competition['name'],
        'club': club['name'],
        'places': str(available + 1)
    }, follow_redirects=True)
    assert b'Not enough places available' in res.data


def test_purchase_more_than_max_per_booking(client):
    club, competition = _load_first_club_and_competition()
    # attempt to book 13 places (max allowed is 12)
    res = client.post('/purchasePlaces', data={
        'competition': competition['name'],
        'club': club['name'],
        'places': '13'
    }, follow_redirects=True)
    assert b'Cannot book more than 12 places' in res.data


def test_purchase_more_than_club_points(client):
    # pick a club that has fewer than 12 points so the points check is evaluated
    with open('clubs.json') as f:
        clubs = json.load(f)['clubs']
    with open('competitions.json') as f:
        competitions = json.load(f)['competitions']

    candidate = None
    for c in clubs:
        try:
            pts = int(c.get('points', 0))
        except (ValueError, TypeError):
            pts = 0
        if pts < 12:
            candidate = c
            break
    assert candidate is not None, "No club with <12 points in fixtures to test points check"
    club = candidate
    club_points = int(club.get('points', 0))

    # choose a competition that has enough available places for club_points+1
    competition = None
    for comp in competitions:
        try:
            avail = int(comp.get('numberOfPlaces', 0))
        except (ValueError, TypeError):
            avail = 0
        if avail >= (club_points + 1):
            competition = comp
            break
    assert competition is not None, "No competition with enough places to run this test"

    # try to book one more place than the club has points
    res = client.post('/purchasePlaces', data={
        'competition': competition['name'],
        'club': club['name'],
        'places': str(club_points + 1)
    }, follow_redirects=True)
    assert b'Not enough points available' in res.data


def test_purchase_valid_booking(client):
    club, competition = _load_first_club_and_competition()
    # compute a safe number of places to book: at least 1 and <= available, <= club points and <=12
    available = int(competition.get('numberOfPlaces', 0))
    try:
        club_points = int(club.get('points', 0))
    except (ValueError, TypeError):
        club_points = 0
    places = max(1, min(available, club_points, 12))

    res = client.post('/purchasePlaces', data={
        'competition': competition['name'],
        'club': club['name'],
        'places': str(places)
    }, follow_redirects=True)

    # On success the app renders the welcome page and shows updated points
    assert res.status_code == 200
    assert b'Great-booking complete!' in res.data or b'Welcome' in res.data
    # the club's remaining points should appear in the response (string)
    remaining = str(club_points - places)
    assert remaining.encode() in res.data
