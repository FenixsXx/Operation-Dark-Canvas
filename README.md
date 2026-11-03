# Operation Mareggiata

[Italiano](README.md) | [English](README.en.md)

Applicazione web per giocare a **Operazione Mareggiata** in rete locale. Il
computer del Director ospita il server e il database della partita; gli altri
partecipanti si collegano dal browser usando la stessa rete Wi-Fi o Ethernet.

Non serve PythonAnywhere, un server pubblico, un servizio di relay o una porta
inoltrata sul router. Il firewall del computer host potrebbe chiedere di
consentire le connessioni sulla rete privata.

> **Nota:** tutti i partecipanti, compreso il Director, devono poter raggiungere
> il computer host sulla stessa rete. Alcune reti Wi-Fi per ospiti isolano i
> dispositivi e non sono adatte.

## Funzionalità

- Server di partita Flask incluso nell'app desktop.
- Avvio automatico del server e apertura dell'interfaccia sul computer host.
- Indirizzo LAN mostrato all'avvio da condividere con gli altri partecipanti.
- Accesso dei giocatori da browser, inclusi i browser su telefono.
- Database e chiave di sessione salvati sul computer host, separati dai file
  dell'applicazione.
- Build locali da terminale, clonando direttamente la repository GitHub.

## Requisiti per creare la build

I comandi clonano la repository pubblica GitHub direttamente nel terminale e
poi eseguono la build sul tuo computer. Non serve scaricare manualmente file
dal browser o aprire prima la cartella del progetto. Serve però Python 3.13
installato sul computer che esegue la build. Durante la prima build `pip`
scarica le dipendenze da PyPI.

- Python **3.13**;
- Git;
- `pip`;
- una connessione Internet per clonare la repository e installare le dipendenze
  da PyPI;
- il sistema operativo e l'architettura per cui si vuole generare l'app.

PyInstaller non crea in modo affidabile build per un altro sistema operativo:
genera il pacchetto sul sistema su cui viene eseguito. Per esempio, una build
Windows va creata su Windows, una build macOS su macOS e una build Linux su
Linux.

Per eseguire una build già pronta non serve installare Python. Per crearla,
Python 3.13 deve invece essere installato sul computer che esegue i comandi.

## Build locale

Puoi partire da una qualsiasi cartella: apri un terminale, esegui il blocco
relativo al tuo sistema operativo e Git clonerà il progetto da
[GitHub](https://github.com/FenixsXx/Operation-Dark-Canvas/tree/main). Il
blocco crea l'ambiente di build, installa le dipendenze e genera l'app senza
che tu debba aprire prima la cartella del progetto o scaricare file dal sito
GitHub.

La prima volta serve una connessione Internet per clonare la repository e
scaricare i pacchetti Python da PyPI. Per ricreare la build in futuro, entra
nella cartella `Operation-Dark-Canvas` già clonata e ripeti i comandi di build
senza le prime due righe (`git clone` e `cd`/`Set-Location`).

### Windows (PowerShell)

```powershell
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
Set-Location Operation-Dark-Canvas
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean DarkCanvas.spec
```

La build sarà in:

```text
dist\OperationMareggiata\
```

Per avviarla:

```powershell
.\dist\OperationMareggiata\OperationMareggiata.exe
```

Distribuisci l'intera cartella `OperationMareggiata`, non soltanto il file
`.exe`.

### macOS (Intel o Apple Silicon)

```bash
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
cd Operation-Dark-Canvas
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

La build sarà in `dist/OperationMareggiata/`. Per avviarla:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribuisci l'intera cartella. La build locale non è firmata né notarizzata:
macOS può mostrare un avviso di sicurezza al primo avvio. Per distribuire
un'app macOS firmata e notarizzata occorre configurare la firma con un account
Apple Developer.

### Linux

```bash
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
cd Operation-Dark-Canvas
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

La build sarà in `dist/OperationMareggiata/`. Per avviarla:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribuisci l'intera cartella. Su alcune distribuzioni Linux potrebbero essere
necessarie librerie di sistema compatibili con quelle presenti sul computer che
ha creato la build.

## Opzionale: build automatiche con GitHub Actions

Se preferisci far creare le build su GitHub, il workflow in
`.github/workflows/build.yml` crea quattro pacchetti separati:

| Sistema del runner | Artefatto |
| --- | --- |
| Windows x64 | `operation-mareggiata-windows-x64` |
| macOS Intel | `operation-mareggiata-macos-intel` |
| macOS Apple Silicon | `operation-mareggiata-macos-apple-silicon` |
| Linux x64 | `operation-mareggiata-linux-x64` |

Per avviare le build:

1. Pubblica il progetto su GitHub e assicurati che il workflow sia presente in
   `.github/workflows/build.yml`.
2. Vai alla scheda **Actions** della repository e seleziona **Build desktop
   app**.
3. Premi **Run workflow** per avviare manualmente tutte le build.
4. Al termine, apri la run completata e scarica l'artefatto corrispondente al
   sistema desiderato.
5. Estrai l'archivio scaricato e distribuisci l'intera cartella
   `OperationMareggiata`.

Il workflow parte anche quando si fa push sul branch `main` o si pubblica un
tag che inizia con `v` (per esempio `v1.0.0`). Gli artefatti sono allegati alla
run GitHub Actions; il workflow **non** crea automaticamente una GitHub
Release.

## Avviare una partita

1. Avvia il programma sul computer scelto dal Director. Lascia aperta la
   finestra del programma per tutta la partita.
2. Il browser del Director si apre automaticamente; la finestra mostra anche
   l'indirizzo LAN da condividere, nel formato `http://indirizzo:5055`.
3. I giocatori, collegati alla stessa rete, aprono quell'indirizzo nel browser
   del telefono o del computer.
4. Se il firewall chiede conferma, consenti le connessioni di rete privata.
   Non configurare il port forwarding del router e non esporre la porta a
   Internet.

Il Director deve mantenere acceso e connesso il computer host: il server e lo
stato della partita risiedono lì. Se il programma non riesce a partire, per
esempio perché la porta `5055` è già occupata, chiudi l'altro programma che la
sta usando e riprova.

### Connessione a Internet del browser

La partita e le API girano sul computer host, ma la pagina carica Tailwind CSS e
le icone Lucide da CDN esterne. Di conseguenza i browser dei partecipanti
devono poter raggiungere Internet per caricare correttamente questi elementi
dell'interfaccia. Il server di gioco non viene ospitato su tali CDN.

## Dati e backup

Il database SQLite, i log e la chiave di sessione sono creati nella cartella
dati utente del sistema operativo, non dentro la cartella della build. Non
cancellare quella cartella se si vogliono conservare i dati della partita. I
backup del database vanno fatti a programma chiuso oppure tramite una procedura
SQLite compatibile con WAL.

## Prima di rendere pubblica la repository

Il codice e i file del caso possono contenere la soluzione, informazioni
riservate del gioco o altri materiali che non vuoi distribuire. Controlla i
file e la cronologia Git prima della pubblicazione: aggiungere un file a
`.gitignore` non lo rimuove dalla cronologia se era già stato tracciato o
pubblicato. Non inserire nella repository database reali, credenziali, chiavi
di sessione o dati personali.

## Struttura essenziale

```text
main.py                         Server Flask e API
launcher.py                     Avvio server, browser e indirizzo LAN
DarkCanvas.spec                 Configurazione PyInstaller
requirements.txt                Dipendenze runtime
.github/workflows/build.yml     Build automatiche multipiattaforma
index.html                      Interfaccia web
assets/                         Immagini e risorse del caso
```
