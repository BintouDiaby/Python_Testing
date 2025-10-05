Phase 2 - Persistance

But: Nous voulons permettre d'enregistrer les modifications (réservations) dans les fichiers JSON
mais en gardant:
- sécurité (backup automatique avant écriture)
- désactivation par défaut pour les tests

Comment utiliser:
- Faire un backup des fixtures (optionnel si vous utilisez le script):
  python scripts/backup_fixtures.py

- Activer la persistance localement (PAR PRUDENCE, faites un backup avant):
  set PERSIST=true    # PowerShell
  # or
  $env:PERSIST = 'true'

- Lancer l'application:
  python app.py

Notes:
- Les sauvegardes sont horodatées et placées dans le même dossier.
- Les écritures sont atomiques pour éviter la corruption de fichiers.
- Par défaut, la persistance est désactivée (PERSIST=false)."