import json
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

competitions = loadCompetitions()
clubs = loadClubs()

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
    flash('Great-booking complete!')
    return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))