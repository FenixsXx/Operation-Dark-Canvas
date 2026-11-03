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

- L'app desktop permette di ospitare una partita oppure collegarsi a un
  Director esistente.
- Al primo avvio della build, l'app crea automaticamente un collegamento sul
  Desktop: `.app` su macOS, `.lnk` su Windows e `.desktop` su Linux.
- Il Director ospita il server nella propria app; gli altri possono usare
  l'app desktop o collegarsi dal browser, anche da telefono.
- L'app desktop è disponibile per Windows, macOS e Linux; su Android si usa il
  browser.
- Tailwind CSS e le icone Lucide sono inclusi localmente; la UI non dipende da
  CDN esterne.
- Database e chiave di sessione salvati sul computer host, separati dai file
  dell'applicazione.
- Build locali da terminale, clonando direttamente la repository GitHub.

## Requisiti per creare la build

I comandi clonano la repository pubblica GitHub direttamente nel terminale e
poi eseguono la build sul tuo computer. Non serve scaricare manualmente file
dal browser o aprire prima la cartella del progetto. Per Windows e macOS serve
Python 3.13; su Ubuntu Linux si usa il Python di sistema (3.12 su Ubuntu 24.04)
per integrare GTK. Durante la prima build `pip` scarica le dipendenze da PyPI.

- Python **3.13** su Windows/macOS, oppure il Python di sistema su Linux;
- Git;
- `pip`;
- una connessione Internet per clonare la repository e installare le dipendenze
  da PyPI;
- il sistema operativo e l'architettura per cui si vuole generare l'app.

Per eseguire l'app desktop servono anche i componenti WebView del sistema:
WebView2 su Windows (normalmente già presente insieme a Edge), WKWebView su
macOS (integrato nel sistema) e GTK 3 con WebKit2GTK su Linux. Le build Linux
create con PyInstaller non includono il WebKit di sistema; installalo sul
computer Linux che esegue l'app.

PyInstaller non crea in modo affidabile build per un altro sistema operativo:
genera il pacchetto sul sistema su cui viene eseguito. Per esempio, una build
Windows va creata su Windows, una build macOS su macOS e una build Linux su
Linux.

Per eseguire una build già pronta non serve installare Python. Per crearla,
Python deve essere installato sul computer che esegue i comandi.

Al primo avvio, la build crea un collegamento sul Desktop che punta alla
posizione in cui si trova l'app. Se esiste già un elemento chiamato
`Operation Mareggiata`, non viene sovrascritto; su alcuni desktop Linux potrebbe
essere necessario autorizzare il file `.desktop` prima di aprirlo.

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

La build macOS sarà `dist/OperationMareggiata.app`. Per avviarla:

```bash
open dist/OperationMareggiata.app
```

Puoi distribuirla come normale app `.app`. La build locale non è firmata né
notarizzata: macOS può mostrare un avviso di sicurezza al primo avvio. Per
distribuire un'app macOS firmata e notarizzata occorre configurare la firma con
un account Apple Developer.

### Linux

Su Ubuntu/Debian installa prima i componenti WebView e il supporto Python per
GTK:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Poi usa il Python di sistema così l'ambiente virtuale possa accedere a PyGObject
fornito dalla distribuzione:

```bash
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
cd Operation-Dark-Canvas
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

La build sarà in `dist/OperationMareggiata/`. Per avviarla:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribuisci l'intera cartella. Ogni computer Linux su cui si avvia l'app deve
avere GTK 3 e WebKit2GTK installati.

### Rigenerare il CSS (facoltativo)

Il CSS compilato è già incluso nella repository; Node.js non serve per creare
una build dell'app. Se modifichi le classi Tailwind nell'interfaccia, puoi
rigenerarlo dalla cartella del progetto con:

```bash
npm ci
npm run build:css
```

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

## Avviare o raggiungere una partita

1. Avvia l'app desktop sul computer del Director e scegli **Avvia come
   Director**. La partita si apre in una finestra dell'app, senza browser
   esterno; l'indirizzo LAN da condividere è mostrato nella schermata iniziale
   e nell'interfaccia del Director.
2. Gli altri giocatori possono aprire la stessa app desktop, scegliere
   **Collegati a una partita** e inserire l'indirizzo. In alternativa possono
   visitarlo direttamente dal browser del telefono o del computer; non devono
   installare l'app.
3. Tutti i dispositivi devono essere sulla stessa rete. Se il firewall chiede
   conferma, consenti le connessioni di rete privata. Non configurare il port
   forwarding del router e non esporre la porta a Internet.

Il Director deve mantenere acceso e connesso il computer host: il server e lo
stato della partita risiedono lì. Se il programma non riesce a partire, per
esempio perché la porta `5055` è già occupata, chiudi l'altro programma che la
sta usando e riprova.

### Risorse dell'interfaccia

Tailwind CSS e Lucide sono serviti dal computer del Director, quindi non serve
Internet per caricare gli stili o le icone. I browser devono comunque poter
raggiungere il computer host sulla rete locale.

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
launcher.py                     App desktop: ospita o si collega alla partita
launcher.html                   Schermata iniziale dell'app desktop
desktop-client.js               Mostra l'indirizzo LAN nell'app Director
DarkCanvas.spec                 Configurazione PyInstaller
requirements.txt                Dipendenze runtime
.github/workflows/build.yml     Build automatiche multipiattaforma
index.html                      Interfaccia web
assets/                         Immagini e risorse del caso
assets/vendor/                  Tailwind CSS, Lucide e relative licenze
tailwind.config.cjs              Sorgenti e configurazione del CSS
package.json                     Dipendenza di sviluppo per Tailwind
```
