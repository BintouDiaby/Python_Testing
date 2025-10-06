# Intro
```
Hey,

Je viens de recevoir le rapport de QA pour la phase 1 du projet. Il y a plusieurs bogues, dont un qui fait planter l'application ! 
Malheureusement, je ne suis pas au bureau pour les prochains jours (un de mes enfants est tombé malade ce week-end). 
Je ne sais pas encore quand je pourrai être là dans la semaine. Pourriez-vous prendre en charge la mise en œuvre du projet ? 
Vous devrez régler les bogues de la phase 1 et mettre en œuvre les éléments de la phase 2 (j'ai ajouté le travail de la phase 2 et les bogues de la section “issues” du repo). 

Vous devrez cloner et forker le repo et le mettre en place sur votre machine locale (tout ce dont vous avez besoin se trouve dans le fichier README). 
Ensuite, passez en revue les bogues dans la section des problèmes, puis essayez de reproduire les problèmes sur votre machine locale pour résoudre les bogues et ajouter la gestion des erreurs. 
Pour gagner du temps de configuration, nous utilisons Flask et JSON pour éviter d'utiliser une base de données. 
La plupart des outils dont vous aurez besoin se trouvent dans le fichier requirements.txt dans le repo, 
mais vous devrez installer Flask et notre framework de test préféré, pytest, ainsi que notre outil de test de performance, Locust. 

Vous devrez également préparer un rapport de test et un rapport de performances, 
conformément au guide de développement à la fin des spécifications fonctionnelles ci-jointes. 
Veillez à suivre toutes les directives, car le QA nous reproche de ne pas respecter les normes. 
Vous devez tester de manière approfondie les résultats requis (à la fois les happy paths et les sad paths) pour toutes les fonctionnalités de l'application.  
Je vous encourage également à adopter une approche de TDD, car cela vous aidera à rationaliser votre travail. 

Une fois que vous aurez terminé, nous ferons un examen de ce que vous avez dans la branche QA du code. 
Nous examinerons les rapports et la manière dont vous avez résolu les problèmes, 
nous examinerons votre code et nous testerons la couverture de la nouvelle fonctionnalité. 

Merci !

```
1. Why


    This is a proof of concept (POC) project to show a light-weight version of our competition booking platform. The aim is the keep things as light as possible, and use feedback from the users to iterate.

2. Getting Started

    This project uses the following technologies:

    * Python v3.x+

    * [Flask](https://flask.palletsprojects.com/en/1.1.x/)

        Whereas Django does a lot of things for us out of the box, Flask allows us to add only what we need. 
     

    * [Virtual environment](https://virtualenv.pypa.io/en/stable/installation.html)

        This ensures you'll be able to install the correct packages without interfering with Python on your machine.

        Before you begin, please ensure you have this installed globally. 


3. Installation

    - After cloning, change into the directory and type <code>virtualenv .</code>. This will then set up a a virtual python environment within that directory.

    - Next, type <code>source bin/activate</code>. You should see that your command prompt has changed to the name of the folder. This means that you can install packages in here without affecting affecting files outside. To deactivate, type <code>deactivate</code>

    - Rather than hunting around for the packages you need, you can install in one step. Type <code>pip install -r requirements.txt</code>. This will install all the packages listed in the respective file. If you install a package, make sure others know by updating the requirements.txt file. An easy way to do this is <code>pip freeze > requirements.txt</code>

    - Flask requires that you set an environmental variable to the python file. However you do that, you'll want to set the file to be <code>server.py</code>. Check [here](https://flask.palletsprojects.com/en/1.1.x/quickstart/#a-minimal-application) for more details

    - You should now be ready to test the application. In the directory, type either <code>flask run</code> or <code>python -m flask run</code>. The app should respond with an address you should be able to go to using your browser.
# GUDLFT — mini-application Flask (état du projet)

Ce README a été mis à jour pour refléter l'état actuel du dépôt après les dernières itérations : ajout d'une page "Points", refonte HTML/CSS (branche `html`), validation côté serveur, et une option de persistance JSON (phase 2).

## Résumé rapide

- Application Flask utilisant des fixtures JSON (`clubs.json`, `competitions.json`).
- Routes principales :
  - `/` : page de connexion (index)
  - `/showSummary` : affichage du tableau de bord pour un club (welcome)
  - `/book/<competition>/<club>` : page de réservation
  - `/purchasePlaces` : endpoint pour effectuer une réservation (validation + déduction de points)
  - `/points` : nouvelle page publique listant les clubs et leurs points

## Fichiers importants

- `app.py` : point d'entrée pour lancer l'application
- `server.py` : logique principale (chargement des fixtures, routes, persistance optionnelle)
- `templates/` : templates Jinja2 (maintenant basés sur `templates/base.html`)
- `static/css/style.css` : styles (refonte visuelle, responsive)
- `tests/` : tests pytest (unitaires et d'intégration pour la persistance)

## Installation et exécution (PowerShell)

1) Créer et activer un virtualenv (si nécessaire)

```powershell
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
```

Si l'activation est bloquée par la politique PowerShell :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\\venv\\Scripts\\Activate.ps1
```

2) Installer les dépendances

```powershell
python -m pip install -r requirements.txt
```

3) Lancer le serveur

```powershell
# avec le venv activé
python app.py

# ou sans activer le venv (utiliser directement le python du venv)
.\\venv\\Scripts\\python.exe app.py
```

L'application écoute sur : `http://127.0.0.1:5000/`.

## Activer la persistance JSON (optionnel)

- Par défaut, l'application n'écrit pas dans les fichiers JSON (mode safe pour les tests).
- Pour autoriser l'écriture :

```powershell
$env:PERSIST = '1'
python app.py
```

- En mode persist, l'application crée des sauvegardes horodatées (`clubs.json.bak.YYYYMMDD...`) avant d'écrire et effectue des écritures atomiques.

> Attention : la persistance modifie les fixtures — ne l'active pas si tu veux conserver l'état d'origine pour des tests reproductibles.

## Notes sur le design et templates

- Les templates héritent d'un `base.html` et utilisent `templates/index.html`, `welcome.html`, `booking.html`, `points.html`.
- La branche `html` contient la refonte visuelle : CSS amélioré, layout responsive, et une page dédiée `points`.

## Comportement développement

- Branches utiles : `html` (UI), `phase2/persistence` (persistance JSON), `ci` (hook dev).
- La branche `ci` contient un `@app.before_request` qui recharge les fixtures JSON avant chaque requête — pratique pour éditer `clubs.json`/`competitions.json` sans redémarrer le serveur. C'est à considérer *development-only*.

## Tests

- Lancer les tests :

```powershell
pytest -q
```

- Quelques tests valident la persistance et créent des backups temporaires — assure-toi d'avoir les droits d'écriture.

## Points d'attention / recommandations

- Ne comite pas le dossier `venv/` (ajoute `venv/` à `.gitignore` si nécessaire).
- La persistance JSON est une solution de prototype ; pour de la production, migrer vers une vraie base de données.
- Les templates et messages sont majoritairement en français après la refonte.

## Prochaines actions proposées

- (A) Peaufiner le design : logo, couleurs, icônes, petites animations CSS.
- (B) Ouvrir une PR `html -> main` avec description et captures d'écran.
- (C) Nettoyer/amariner les tests instables (marquer xfail ou isoler les tests d'intégration). 
*** End Patch



