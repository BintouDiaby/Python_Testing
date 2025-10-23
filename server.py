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


@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.utcnow().year}

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


@app.route('/tests')
def tests_list():
    """Lister les fichiers de test et extraire une courte description.

    Recherche les fichiers matching tests/test_*.py et lit leur première
    docstring ou première ligne de commentaire pour l'afficher comme
    description. Cette vue est destinée à l'inspection locale/dev.
    """
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    entries = []
    if os.path.isdir(test_dir):
        for fname in sorted(os.listdir(test_dir)):
            if fname.startswith('test_') and fname.endswith('.py'):
                path = os.path.join(test_dir, fname)
                desc = ''
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        src = f.read()
                    # Attempt to extract module docstring
                    import ast
                    try:
                        mod = ast.parse(src)
                        doc = ast.get_docstring(mod)
                        if doc:
                            desc = doc.strip().splitlines()[0]
                        else:
                            # fallback: first non-empty comment line
                            for line in src.splitlines():
                                s = line.strip()
                                if s.startswith('#'):
                                    desc = s.lstrip('#').strip()
                                    break
                    except Exception:
                        # best-effort fallback
                        for line in src.splitlines():
                            s = line.strip()
                            if s.startswith('#'):
                                desc = s.lstrip('#').strip()
                                break
                except Exception:
                    desc = 'Impossible de lire le fichier'

                entries.append({'file': fname, 'path': path, 'description': desc})

    return render_template('tests.html', tests=entries)


@app.route('/static/tests/<path:filename>')
def serve_test_file(filename):
    """Servir en lecture seule les fichiers de tests pour inspection via le navigateur.

    Cette route renvoie le contenu du fichier sous forme de text/plain. Elle
    vérifie que le fichier demandé se trouve bien dans le dossier tests/ et
    évite l'accès arbitraire à d'autres chemins.
    """
    safe_dir = os.path.join(os.path.dirname(__file__), 'tests')
    requested = os.path.normpath(os.path.join(safe_dir, filename))
    # Ensure requested is inside safe_dir
    if not requested.startswith(os.path.abspath(safe_dir)):
        return "Accès refusé", 403

    if not os.path.exists(requested) or not os.path.isfile(requested):
        return "Fichier non trouvé", 404

    try:
        with open(requested, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return "Impossible de lire le fichier", 500

    from flask import Response
    return Response(content, mimetype='text/plain; charset=utf-8')


@app.route('/logout')
def logout():
    return redirect(url_for('index'))