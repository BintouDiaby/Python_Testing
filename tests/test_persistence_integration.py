import os
import glob
import json
import shutil
import tempfile
import pytest
import sys
import pathlib

# Ensure project root is on sys.path so tests can import application modules
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import app


@pytest.fixture
def client(tmp_path):
    app.config['TESTING'] = True
    # ensure persistence is enabled for this test
    app.config['PERSIST'] = True

    # backup current fixtures to tmp_path
    shutil.copy('clubs.json', str(tmp_path / 'clubs.json.bak'))
    shutil.copy('competitions.json', str(tmp_path / 'competitions.json.bak'))

    # remove any existing automatic backups created by the app
    for f in glob.glob('clubs.json.bak.*'):
        try:
            os.remove(f)
        except Exception:
            pass
    for f in glob.glob('competitions.json.bak.*'):
        try:
            os.remove(f)
        except Exception:
            pass

    with app.test_client() as client:
        yield client

    # restore original fixtures after test
    shutil.copy(str(tmp_path / 'clubs.json.bak'), 'clubs.json')
    shutil.copy(str(tmp_path / 'competitions.json.bak'), 'competitions.json')
    # cleanup generated backups
    for f in glob.glob('clubs.json.bak.*'):
        try:
            os.remove(f)
        except Exception:
            pass
    for f in glob.glob('competitions.json.bak.*'):
        try:
            os.remove(f)
        except Exception:
            pass


def test_persistence_writes_backup_and_updates_json(client):
    # load current fixtures to pick a valid club/competition
    with open('clubs.json') as f:
        clubs = json.load(f)['clubs']
    with open('competitions.json') as f:
        comps = json.load(f)['competitions']

    # choose first club with at least 1 point
    club = next((c for c in clubs if int(c.get('points', 0)) > 0), None)
    assert club is not None, "No club with points available for test"
    comp = next((c for c in comps if int(c.get('numberOfPlaces', 0)) > 0), None)
    assert comp is not None, "No competition with available places"

    club_name = club['name']
    comp_name = comp['name']
    club_points = int(club['points'])

    # perform booking of 1 place
    res = client.post('/purchasePlaces', data={
        'competition': comp_name,
        'club': club_name,
        'places': '1'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Great-booking complete!' in res.data

    # at least one backup file should exist
    clubs_baks = glob.glob('clubs.json.bak.*')
    assert len(clubs_baks) >= 1

    # clubs.json should reflect the deducted point
    with open('clubs.json') as f:
        new_clubs = json.load(f)['clubs']
    new_points = int(next(c for c in new_clubs if c['name'] == club_name)['points'])
    assert new_points == club_points - 1
