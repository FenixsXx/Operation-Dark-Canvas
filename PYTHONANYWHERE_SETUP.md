# PythonAnywhere

## File da caricare

Carica nella stessa directory PythonAnywhere di `main.py` questi file e cartelle:

```text
main.py
index.html
dossier_447_gn_player.html
manifest.json
icon-192.svg
icon-512.svg
approved.mp3
rejected.mp3
click.mp3
notify.mp3
(NEW) EV-04.png
(NEW) EV-05.png
(NEW) planimetria della Sala Blu.png
assets/
    social_mockup.svg
    evidence/
```

Carica anche `dark_canvas.sqlite3` se vuoi conservare lo stato attuale del caso.
Non sono necessari `dark_canvas.sqlite3-shm`, `dark_canvas.sqlite3-wal`, `backup_db/`,
`venv/` o i file di archivio. `requirements.txt` serve per installare le dipendenze,
mentre `backup_db.sh` è opzionale per il backup programmato.

## WSGI

Se il sito mostra `Hello from Flask!`, la web app sta ancora usando il WSGI di
esempio di PythonAnywhere. Apri **Web → WSGI configuration file**, elimina il
contenuto predefinito e sostituiscilo interamente con:

```python
import sys
path = '/home/Fenixs'
if path not in sys.path:
    sys.path.insert(0, path)
from main import app as application
```

In **Web** imposta anche:

```text
Source code: /home/Fenixs
Working directory: /home/Fenixs
Virtualenv: /home/Fenixs/venv
```

Salva il file WSGI e premi **Reload**. Non incollare nel WSGI le righe Markdown,
`Set ...`, `chmod` o il comando del backup.

## Variabili d'ambiente

Se nel pannello **Web** non compare la sezione **Environment variables**, impostale nel file WSGI, prima dell'import di `main`:

```python
import os
os.environ['DARK_CANVAS_SECRET'] = 'INCOLLA_QUI_UN_SEGRETO_LUNGO_E_CASUALE'
os.environ['FLASK_ENV'] = 'production'
os.environ['SESSION_COOKIE_SECURE'] = 'true'
```

Il file WSGI completo deve quindi contenere questi import e impostazioni, seguiti dal codice di importazione dell'app. Non pubblicare il valore del secret.

## Virtualenv

La voce **Virtualenv:** nella scheda **Web** riguarda solo l'ambiente Python dell'app, non i backup programmati. Se hai creato l'ambiente nella home, inserisci:

```text
/home/Fenixs/venv
```

Se invece non esiste ancora, crealo dalla Bash console e installa Flask:

```bash
python3.13 -m venv /home/Fenixs/venv
/home/Fenixs/venv/bin/pip install -r /home/Fenixs/requirements.txt
```

Dopo aver compilato il campo **Virtualenv:**, salva e fai **Reload** della web app.

## Database backup

Prima carica `backup_db.sh` nella stessa directory che contiene `main.py` e `dark_canvas.sqlite3`, usando il pannello **Files** di PythonAnywhere.

Nella console Bash puoi verificare la posizione con:

```bash
pwd
ls -l /home/Fenixs/backup_db.sh
```

Se `ls` risponde "No such file", il file non è ancora stato caricato in quella directory. Dopo l'upload, esegui una sola volta:

```bash
chmod +x /home/Fenixs/backup_db.sh
```

Se il tuo account mostra **Tasks** nel dashboard PythonAnywhere, apri la pagina **Tasks** e aggiungi un task programmato ogni 15 minuti con questo comando:

```bash
/home/Fenixs/backup_db.sh >> /home/Fenixs/backup_db.log 2>&1
```

I backup vengono scritti in `backup_db/` e quelli più vecchi di 7 giorni vengono rimossi. `DARK_CANVAS_BACKUP_DIR` è opzionale e serve solo se vuoi usare un'altra directory.

Se **Tasks** non compare, il tuo piano non espone i task programmati: in quel caso il backup automatico non può essere attivato dal pannello e va eseguito manualmente oppure con un piano che includa gli Scheduled Tasks.
