import json
import os
import shutil
import datetime
import tempfile
from flask import Flask,render_template,request,redirect,flash,url_for


def loadClubs():
    with open('clubs.json') as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs


def loadCompetitions():
    with open('competitions.json') as comps:
         listOfCompetitions = json.load(comps)['competitions']
         return listOfCompetitions


app = Flask(__name__)
app.secret_key = 'something_special'
# Toggle persistence: can be enabled by setting the PERSIST environment variable to
# '1', 'true' or 'yes'. It remains disabled by default to keep tests reproducible.
env_persist = os.environ.get('PERSIST', 'false').lower()
app.config['PERSIST'] = env_persist in ('1', 'true', 'yes')

competitions = loadCompetitions()
clubs = loadClubs()


@app.before_request
def reload_fixtures():
    """Reload JSON fixtures before every request so manual edits are picked up
    immediately without restarting the server. This is intentionally simple and
    safe for development; for production a more efficient watcher or caching
    strategy would be preferable.
    """
    global competitions, clubs
    competitions = loadCompetitions()
    clubs = loadClubs()


def save_state():
    """Write current in-memory clubs and competitions back to their JSON files.
    This is only called when `app.config['PERSIST']` is True to avoid surprising
    writes during tests/development.
    """
    if not app.config.get('PERSIST'):
        return

    # Create timestamped backups before writing
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    try:
        shutil.copy2('clubs.json', f'clubs.json.bak.{ts}')
    except Exception:
        # If backup fails, proceed cautiously — still attempt write
        pass
    try:
        shutil.copy2('competitions.json', f'competitions.json.bak.{ts}')
    except Exception:
        pass

    # Write atomically: write to temp file then replace
    def _atomic_write(path, obj):
        dirn = os.path.dirname(path) or '.'
        fd, tmp = tempfile.mkstemp(dir=dirn)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(obj, f, indent=4)
            os.replace(tmp, path)
        finally:
            # ensure temp removed if something went wrong
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass

    _atomic_write('clubs.json', {'clubs': clubs})
    _atomic_write('competitions.json', {'competitions': competitions})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    email = request.form.get('email', '').strip()
    if not email:
        flash('Please provide an email')
        return redirect(url_for('index'))

    matched = [c for c in clubs if c.get('email') == email]
    if not matched:
        flash('Email not found')
        return redirect(url_for('index'))

    club = matched[0]
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = next((c for c in clubs if c.get('name') == club), None)
    foundCompetition = next((c for c in competitions if c.get('name') == competition), None)
    if foundClub and foundCompetition:
        return render_template('booking.html', club=foundClub, competition=foundCompetition)

    flash('Club or competition not found')
    return redirect(url_for('index'))


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    competition_name = request.form.get('competition')
    club_name = request.form.get('club')
    try:
        placesRequired = int(request.form.get('places', 0))
    except ValueError:
        flash('Invalid number of places')
        return redirect(url_for('index'))

    competition = next((c for c in competitions if c.get('name') == competition_name), None)
    club = next((c for c in clubs if c.get('name') == club_name), None)

    if not competition or not club:
        flash('Club or competition not found')
        return redirect(url_for('index'))

    available = int(competition.get('numberOfPlaces', 0))
    if placesRequired <= 0:
        flash('You must book at least one place')
        return redirect(url_for('index'))
    if placesRequired > available:
        flash('Not enough places available')
        return redirect(url_for('index'))

    # Check max per booking (12)
    if placesRequired > 12:
        flash('Cannot book more than 12 places')
        return redirect(url_for('index'))

    # Check club has enough points
    try:
        club_points = int(club.get('points', 0))
    except (ValueError, TypeError):
        club_points = 0
    if placesRequired > club_points:
        flash('Not enough points available')
        return redirect(url_for('index'))

    # perform booking (in-memory only)
    competition['numberOfPlaces'] = available - placesRequired
    # Deduct points from club (in-memory)
    club['points'] = str(club_points - placesRequired)

    # Persist state when enabled
    save_state()

    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/points')
def points():
    """Afficher une page listant les clubs et leurs points."""
    # clubs est rechargé par reload_fixtures() en mode dev
    return render_template('points.html', clubs=clubs)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))