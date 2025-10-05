import shutil, datetime

ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
shutil.copy2('clubs.json', f'clubs.json.bak.{ts}')
shutil.copy2('competitions.json', f'competitions.json.bak.{ts}')
print('Backups created:', f'clubs.json.bak.{ts}', f'competitions.json.bak.{ts}')
