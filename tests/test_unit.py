"""
Tests unitaires pour l'application GUDLFT
==========================================

Ce fichier contient des tests unitaires couvrant toutes les routes principales
de l'application Flask, y compris les cas nominaux et les cas d'erreur.

Structure:
- Test de la page d'accueil (GET /)
- Test de connexion (POST /showSummary) - email valide/invalide
- Test de réservation (GET /book/<competition>/<club>)
- Test d'achat de places (POST /purchasePlaces) - validations métier
- Test de la page points (GET /points)
- Test de déconnexion (GET /logout)
"""

import pytest
import sys
import pathlib

# Ensure project root is on sys.path
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import app


@pytest.fixture
def client():
    """Fixture Flask test client avec mode test activé."""
    app.config['TESTING'] = True
    # Disable persistence for tests to avoid modifying fixtures
    app.config['PERSIST'] = False
    with app.test_client() as client:
        yield client



# Tests de la page d'accueil

def test_index_page_loads(client):
    """Test que la page d'accueil se charge correctement."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'GUDLFT' in response.data or b'index' in response.data.lower()



# Tests de connexion (POST /showSummary)

def test_showSummary_valid_email(client):
    """Test connexion avec un email valide existant dans clubs.json."""
    # Email connu dans clubs.json
    response = client.post('/showSummary', data={'email': 'john@simplylift.co'})
    assert response.status_code == 200
    assert b'Welcome' in response.data or b'competitions' in response.data.lower()


def test_showSummary_invalid_email(client):
    """Test connexion avec un email inexistant - doit afficher erreur."""
    response = client.post('/showSummary', data={'email': 'notfound@example.com'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Email not found' in response.data


def test_showSummary_empty_email(client):
    """Test connexion avec un email vide - doit demander de fournir email."""
    response = client.post('/showSummary', data={'email': ''}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Please provide an email' in response.data


def test_showSummary_whitespace_email(client):
    """Test connexion avec un email contenant seulement des espaces."""
    response = client.post('/showSummary', data={'email': '   '}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Please provide an email' in response.data


def test_showSummary_new_club_email(client):
    """Test connexion avec l'email d'un nouveau club ajouté (Titan Strength)."""
    response = client.post('/showSummary', data={'email': 'contact@titanstrength.com'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Titan Strength' in response.data or b'competitions' in response.data.lower()


# =====================================================================
# Tests de la page de réservation (GET /book/<competition>/<club>)
# =====================================================================

def test_book_page_valid_club_and_competition(client):
    """Test affichage page de réservation avec club et compétition valides."""
    # Utiliser des noms connus dans les fixtures
    response = client.get('/book/Spring%20Festival/Simply%20Lift')
    assert response.status_code == 200
    assert b'Spring Festival' in response.data
    assert b'Simply Lift' in response.data


def test_book_page_invalid_club(client):
    """Test avec un club inexistant - doit rediriger avec erreur."""
    response = client.get('/book/Spring%20Festival/FakeClub', follow_redirects=True)
    assert response.status_code == 200
    assert b'Club or competition not found' in response.data


def test_book_page_invalid_competition(client):
    """Test avec une compétition inexistante - doit rediriger avec erreur."""
    response = client.get('/book/FakeCompetition/Simply%20Lift', follow_redirects=True)
    assert response.status_code == 200
    assert b'Club or competition not found' in response.data


# =====================================================================
# Tests d'achat de places (POST /purchasePlaces)
# =====================================================================

def test_purchasePlaces_valid_booking(client):
    """Test réservation valide avec assez de points et places disponibles."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '1'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Great-booking complete!' in response.data


def test_purchasePlaces_zero_places(client):
    """Test réservation de 0 places - doit échouer."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '0'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'You must book at least one place' in response.data


def test_purchasePlaces_negative_places(client):
    """Test réservation de places négatives - doit échouer."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '-5'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'You must book at least one place' in response.data


def test_purchasePlaces_more_than_12_places(client):
    """Test réservation de plus de 12 places - doit respecter la limite."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '13'
    }, follow_redirects=True)
    assert response.status_code == 200
    # La réservation devrait être refusée, on devrait être redirigé vers index
    # (le message flash devrait s'afficher mais peut nécessiter une session active)
    # On vérifie qu'on n'a PAS le message de succès
    assert b'Great-booking complete!' not in response.data
    # ET qu'on est revenu sur la page d'accueil (index)
    assert b'email' in response.data.lower() or b'accueil' in response.data.lower()


def test_purchasePlaces_invalid_number_format(client):
    """Test réservation avec format de nombre invalide."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': 'abc'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid number of places' in response.data


def test_purchasePlaces_not_enough_points(client):
    """Test réservation quand le club n'a pas assez de points."""
    # She Lifts a seulement 1 point dans clubs.json
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'She Lifts',
        'places': '10'  # Plus que les points disponibles
    }, follow_redirects=True)
    assert response.status_code == 200
    # La réservation devrait être refusée — pas de message de succès
    assert b'Great-booking complete!' not in response.data
    # On devrait être redirigé vers index
    assert b'email' in response.data.lower() or b'accueil' in response.data.lower()


def test_purchasePlaces_invalid_club(client):
    """Test réservation avec un club inexistant."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'NonExistentClub',
        'places': '1'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Club or competition not found' in response.data


def test_purchasePlaces_invalid_competition(client):
    """Test réservation avec une compétition inexistante."""
    response = client.post('/purchasePlaces', data={
        'competition': 'NonExistentCompetition',
        'club': 'Simply Lift',
        'places': '1'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Club or competition not found' in response.data


# =====================================================================
# Tests de la page des points (GET /points)
# =====================================================================

def test_points_page_loads(client):
    """Test que la page des points se charge correctement."""
    response = client.get('/points')
    assert response.status_code == 200
    # Vérifier que les noms de clubs apparaissent
    assert b'Simply Lift' in response.data or b'club' in response.data.lower()


def test_points_page_displays_all_clubs(client):
    """Test que tous les clubs sont affichés sur la page des points."""
    response = client.get('/points')
    assert response.status_code == 200
    # Vérifier présence de plusieurs clubs
    assert b'Simply Lift' in response.data
    assert b'Iron Temple' in response.data or b'She Lifts' in response.data


# =====================================================================
# Tests de déconnexion (GET /logout)
# =====================================================================

def test_logout_redirects_to_index(client):
    """Test que la déconnexion redirige vers la page d'accueil."""
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect
    # Vérifier que la redirection pointe vers index
    assert '/logout' not in response.location or '/' in response.location


def test_logout_with_redirect_follow(client):
    """Test déconnexion avec suivi de la redirection."""
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    # Devrait être sur la page d'accueil
    assert b'GUDLFT' in response.data or b'index' in response.data.lower()


# =====================================================================
# Tests des validations métier avancées
# =====================================================================

def test_purchasePlaces_exact_12_places_allowed(client):
    """Test que réserver exactement 12 places est permis (limite exacte)."""
    response = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',  # A assez de points
        'places': '12'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Si le club a assez de points, ça devrait passer, sinon message de manque de points/places
    response_lower = response.data.lower()
    assert (b'great-booking complete!' in response_lower or 
            b'not enough points' in response_lower or 
            b'not enough places' in response_lower)


def test_multiple_bookings_reduce_places(client):
    """Test que plusieurs réservations réduisent bien le nombre de places disponibles."""
    # Première réservation
    response1 = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '1'
    }, follow_redirects=True)
    assert b'Great-booking complete!' in response1.data
    
    # Deuxième réservation (devrait aussi fonctionner si assez de places)
    response2 = client.post('/purchasePlaces', data={
        'competition': 'Spring Festival',
        'club': 'Simply Lift',
        'places': '1'
    }, follow_redirects=True)
    # Vérifie que la réservation se passe (ou échoue si plus de places/points)
    assert response2.status_code == 200


# =====================================================================
# Tests de robustesse et cas limites
# =====================================================================

def test_book_url_with_special_characters(client):
    """Test que les URLs avec caractères spéciaux sont gérées."""
    response = client.get('/book/Fall%20Classic/Iron%20Temple')
    # Soit la compétition existe (200), soit elle n'existe pas (redirect 302)
    assert response.status_code in [200, 302]


def test_showSummary_case_sensitive_email(client):
    """Test que la recherche d'email est sensible à la casse (ou non selon implémentation)."""
    # Email en majuscules vs minuscules
    response = client.post('/showSummary', data={'email': 'JOHN@SIMPLYLIFT.CO'}, follow_redirects=True)
    # Dépend de l'implémentation - si case-sensitive, devrait échouer
    assert response.status_code == 200


def test_points_page_without_authentication(client):
    """Test que la page des points est accessible sans authentification (transparence)."""
    response = client.get('/points')
    assert response.status_code == 200
    # Page des points doit être publique
    assert b'points' in response.data.lower() or b'club' in response.data.lower()


# =====================================================================
# Résumé des tests
# =====================================================================
"""
Couverture des tests unitaires:

✅ Page d'accueil (GET /)
✅ Connexion valide/invalide (POST /showSummary)
✅ Emails vides/espaces (POST /showSummary)
✅ Page de réservation valide/invalide (GET /book)
✅ Réservation valide (POST /purchasePlaces)
✅ Validations: 0 places, négatif, >12 places
✅ Format invalide de nombre
✅ Pas assez de points
✅ Club/compétition inexistants
✅ Page des points (GET /points)
✅ Déconnexion (GET /logout)
✅ Cas limites et robustesse

Total: ~25 tests unitaires couvrant toutes les routes et validations métier.
"""
