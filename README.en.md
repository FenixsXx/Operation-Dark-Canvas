# Operation Mareggiata

[Italiano](README.md) | [English](README.en.md)

A web application for playing **Operation Mareggiata** over a local network.
The Director's computer hosts the game server and database; other participants
connect from a browser using the same Wi-Fi or Ethernet network.

No PythonAnywhere, public server, relay service, or router port forwarding is
required. The host computer's firewall may ask you to allow connections on
private networks.

> **Note:** all participants, including the Director, must be able to reach the
> host computer over the same network. Some guest Wi-Fi networks isolate
> connected devices and are not suitable.

## Features

- The desktop app can host a game or connect to an existing Director.
- The Director hosts the server in the app; others can use the desktop app or
  join from a browser, including on phones.
- The desktop app is available for Windows, macOS, and Linux; Android players
  use a browser.
- Tailwind CSS and Lucide icons are bundled locally, so the interface does not
  depend on external CDNs.
- The database and session key are stored on the host computer, separately
  from the application files.
- Local terminal builds by cloning the GitHub repository.

## Requirements for building

The commands clone the public GitHub repository directly from the terminal and
then build the app on your computer. You do not need to manually download files
from the browser or open the project folder first. Windows and macOS require
Python 3.13; Ubuntu Linux uses its system Python (3.12 on Ubuntu 24.04) to
integrate GTK. On the first build, `pip` downloads dependencies from PyPI.

- Python **3.13** on Windows/macOS, or the system Python on Linux;
- Git;
- `pip`;
- an Internet connection to clone the repository and install dependencies
  from PyPI;
- the operating system and architecture you want to build for.

The desktop app also needs the system WebView components: WebView2 on Windows
(normally installed with Edge), WKWebView on macOS (built into the system), and
GTK 3 with WebKit2GTK on Linux. PyInstaller Linux builds do not include the
system WebKit engine; install it on the Linux computer that runs the app.

PyInstaller does not reliably cross-compile for a different operating system:
build the package on the system it targets. For example, build the Windows
package on Windows, the macOS package on macOS, and the Linux package on Linux.

Python is not required to run a prebuilt app. To create a build, Python must be
installed on the computer running the commands.

## Build locally

You can start from any directory: open a terminal, run the block for your
operating system, and Git will clone the project from
[GitHub](https://github.com/FenixsXx/Operation-Dark-Canvas/tree/main). The
block creates the build environment, installs dependencies, and builds the app.
You do not need to open the project folder first or download files from the
GitHub website.

The first build requires an Internet connection to clone the repository and
download Python packages from PyPI. To rebuild later, enter the already-cloned
`Operation-Dark-Canvas` folder and rerun the build commands without the first
two lines (`git clone` and `cd`/`Set-Location`).

### Windows (PowerShell)

```powershell
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
Set-Location Operation-Dark-Canvas
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean DarkCanvas.spec
```

The build will be created in:

```text
dist\OperationMareggiata\
```

To run it:

```powershell
.\dist\OperationMareggiata\OperationMareggiata.exe
```

Distribute the entire `OperationMareggiata` folder, not just the `.exe` file.

### macOS (Intel or Apple Silicon)

```bash
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
cd Operation-Dark-Canvas
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

The macOS build will be `dist/OperationMareggiata.app`. To run it:

```bash
open dist/OperationMareggiata.app
```

You can distribute it as a regular `.app`. Local builds are not signed or
notarized, so macOS may show a security warning the first time the app is
opened. Distributing a signed and notarized macOS app requires configuring code
signing with an Apple Developer account.

### Linux

On Ubuntu/Debian, first install the WebView components and Python GTK bindings:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Then use the system Python so the virtual environment can access the
distribution-provided PyGObject package:

```bash
git clone https://github.com/FenixsXx/Operation-Dark-Canvas.git
cd Operation-Dark-Canvas
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

The build will be in `dist/OperationMareggiata/`. To run it:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribute the entire folder. Every Linux computer that runs the app must have
GTK 3 and WebKit2GTK installed.

### Regenerate the CSS (optional)

The compiled CSS is already included in the repository; Node.js is not needed
to build the app. If you change Tailwind classes in the interface, regenerate
the stylesheet from the project folder with:

```bash
npm ci
npm run build:css
```

## Optional: automated builds with GitHub Actions

If you prefer to have GitHub create the builds, the workflow in
`.github/workflows/build.yml` creates four separate packages:

| Runner operating system | Artifact |
| --- | --- |
| Windows x64 | `operation-mareggiata-windows-x64` |
| Intel macOS | `operation-mareggiata-macos-intel` |
| Apple Silicon macOS | `operation-mareggiata-macos-apple-silicon` |
| Linux x64 | `operation-mareggiata-linux-x64` |

To start the builds:

1. Publish the project to GitHub and make sure the workflow is present at
   `.github/workflows/build.yml`.
2. Open the repository's **Actions** tab and select **Build desktop app**.
3. Click **Run workflow** to start all builds manually.
4. When the run completes, open it and download the artifact for the desired
   operating system.
5. Extract the downloaded archive and distribute the entire
   `OperationMareggiata` folder.

The workflow also runs on pushes to the `main` branch and when a tag starting
with `v` is published (for example, `v1.0.0`). Artifacts are attached to the
GitHub Actions run; the workflow does **not** automatically create a GitHub
Release.

## Host or join a game

1. Launch the desktop app on the Director's computer and select **Avvia come
   Director**. The game opens in an app window, not an external browser; the
   LAN address to share is shown on the startup screen and in the Director
   interface.
2. Other players can open the same desktop app, select **Collegati a una
   partita**, and enter that address. Alternatively, they can open it directly
   in a browser on their phone or computer; they do not have to install the
   app.
3. All devices must be on the same network. If the firewall asks for
   permission, allow connections on private networks. Do not configure router
   port forwarding or expose the port to the Internet.

The Director must keep the host computer powered on and connected: the server
and game state reside there. If the app cannot start, for example because port
`5055` is already in use, close the other program using that port and try
again.

### Interface assets

Tailwind CSS and Lucide are served by the Director's computer, so Internet
access is not needed to load styles or icons. Browsers must still be able to
reach the host computer on the local network.

## Data and backups

The SQLite database, logs, and session key are created in the operating
system's user data directory, not inside the app's build folder. Do not delete
that directory if you want to preserve game data. Back up the database while
the app is closed, or use a SQLite backup method that supports WAL mode.

## Before making the repository public

The source code and case files may contain the solution, confidential game
information, or other materials you do not want to distribute. Review the
files and Git history before publishing: adding a file to `.gitignore` does
not remove it from history if it has already been tracked or published. Do not
add real databases, credentials, session keys, or personal data to the
repository.

## Key files

```text
main.py                         Flask server and APIs
launcher.py                     Desktop app: host or join a game
launcher.html                   Desktop app startup screen
desktop-client.js               Displays the LAN address in the Director app
DarkCanvas.spec                 PyInstaller configuration
requirements.txt                Runtime dependencies
.github/workflows/build.yml     Automated multi-platform builds
index.html                      Web interface
assets/                         Case images and resources
assets/vendor/                  Tailwind CSS, Lucide, and their licenses
tailwind.config.cjs              CSS source and configuration
package.json                     Tailwind development dependency
```
