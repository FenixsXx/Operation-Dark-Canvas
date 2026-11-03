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

- Flask game server bundled with the desktop app.
- Automatic server startup and browser launch on the host computer.
- The LAN address is displayed at startup so it can be shared with other
  participants.
- Players can join from a browser, including on phones.
- The database and session key are stored on the host computer, separately
  from the application files.
- Local builds from the terminal, without using GitHub.

## Requirements for building

The commands below use the project files already on your computer: they do not
clone the repository, download source code or build artifacts from GitHub, or
require a GitHub account. Python 3.13 must be installed on the computer that
runs the build. On the first build, `pip` downloads dependencies from PyPI.

- Python **3.13**;
- `pip`;
- an Internet connection to install dependencies from PyPI;
- the operating system and architecture you want to build for.

PyInstaller does not reliably cross-compile for a different operating system:
build the package on the system it targets. For example, build the Windows
package on Windows, the macOS package on macOS, and the Linux package on Linux.

Python is not required to run a prebuilt app. If Python 3.13 is not already
available, install it separately before running the build commands.

## Build locally

Open a terminal in the project directory containing `DarkCanvas.spec`,
`launcher.py`, and `requirements.txt`, then run the commands for your system.
The `.venv` and `dist/` folders are created locally; you do not need to
download a build artifact from GitHub.

### Windows (PowerShell)

```powershell
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

Open Terminal in the project directory:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

The build will be in `dist/OperationMareggiata/`. To run it:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribute the entire folder. Local builds are not signed or notarized, so
macOS may show a security warning the first time the app is opened. Distributing
a signed and notarized macOS app requires configuring code signing with an
Apple Developer account.

### Linux

On a distribution with Python 3.13 installed:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt pyinstaller
.venv/bin/pyinstaller --noconfirm --clean DarkCanvas.spec
```

The build will be in `dist/OperationMareggiata/`. To run it:

```bash
./dist/OperationMareggiata/OperationMareggiata
```

Distribute the entire folder. Some Linux distributions may require system
libraries compatible with those available on the computer that created the
build.

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

## Start a game

1. Launch the app on the computer chosen by the Director. Keep the app window
   open for the entire game.
2. The Director's browser opens automatically. The app window also displays
   the LAN address to share, in the format `http://address:5055`.
3. Players on the same network open that address in a browser on their phone
   or computer.
4. If the firewall asks for permission, allow connections on private networks.
   Do not configure router port forwarding or expose the port to the Internet.

The Director must keep the host computer powered on and connected: the server
and game state reside there. If the app cannot start, for example because port
`5055` is already in use, close the other program using that port and try
again.

### Browser Internet access

The game and APIs run on the host computer, but the page loads Tailwind CSS and
Lucide icons from external CDNs. Therefore, participants' browsers need
Internet access to load these interface elements correctly. The game server
itself is not hosted on those CDNs.

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
launcher.py                     Server, browser, and LAN address startup
DarkCanvas.spec                 PyInstaller configuration
requirements.txt                Runtime dependencies
.github/workflows/build.yml     Automated multi-platform builds
index.html                      Web interface
assets/                         Case images and resources
```
