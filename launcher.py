from __future__ import annotations

import errno
import ipaddress
import logging
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import webview
from platformdirs import user_data_dir, user_desktop_dir
from waitress import create_server

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
logger = logging.getLogger("dark_canvas_launcher")


def _powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _desktop_exec_argument(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("Il percorso dell'app non può contenere righe nuove.")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    return f'"{escaped}"'


def create_desktop_shortcut() -> None:
    if not getattr(sys, "frozen", False):
        return

    try:
        desktop_dir = Path(user_desktop_dir())
        desktop_dir.mkdir(parents=True, exist_ok=True)

        executable = Path(sys.executable).resolve()
        if sys.platform == "darwin":
            app_bundle = executable.parents[2]
            if app_bundle.suffix != ".app" or not app_bundle.is_dir():
                raise RuntimeError(f"Bundle macOS non trovato: {app_bundle}")
            shortcut = desktop_dir / "Operation Mareggiata.app"
            if shortcut.exists() or shortcut.is_symlink():
                if shortcut.is_symlink() and shortcut.resolve() == app_bundle:
                    return
                logger.warning("Collegamento non creato: esiste già %s", shortcut)
                return
            shortcut.symlink_to(app_bundle, target_is_directory=True)
            return

        if sys.platform == "win32":
            shortcut = desktop_dir / "Operation Mareggiata.lnk"
            if shortcut.exists() or shortcut.is_symlink():
                logger.warning("Collegamento non creato: esiste già %s", shortcut)
                return
            script = (
                "$shell = New-Object -ComObject WScript.Shell; "
                f"$shortcut = $shell.CreateShortcut({_powershell_literal(str(shortcut))}); "
                f"$shortcut.TargetPath = {_powershell_literal(str(executable))}; "
                f"$shortcut.WorkingDirectory = {_powershell_literal(str(executable.parent))}; "
                "$shortcut.Description = 'Operation Mareggiata'; "
                "$shortcut.Save()"
            )
            subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return

        if sys.platform.startswith("linux"):
            shortcut = desktop_dir / "Operation Mareggiata.desktop"
            if shortcut.exists() or shortcut.is_symlink():
                logger.warning("Collegamento non creato: esiste già %s", shortcut)
                return
            shortcut.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Operation Mareggiata\n"
                f"Exec={_desktop_exec_argument(str(executable))}\n"
                "Terminal=false\n"
                "Categories=Game;\n",
                encoding="utf-8",
            )
            shortcut.chmod(0o755)
            return

        logger.warning("Creazione collegamento Desktop non supportata su %s", sys.platform)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        logger.error(
            "Creazione collegamento Desktop non riuscita: %s",
            detail or error,
            exc_info=True,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
        logger.exception("Creazione collegamento Desktop non riuscita")


def configure_data_directory() -> Path:
    data_dir = Path(user_data_dir("Operation Mareggiata"))
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DARK_CANVAS_DB", str(data_dir / "dark_canvas.sqlite3"))
    os.environ.setdefault("DARK_CANVAS_LOG", str(data_dir / "dark_canvas.log"))
    logging.basicConfig(
        filename=data_dir / "dark_canvas.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return data_dir


def configure_host_secret(data_dir: Path) -> None:
    if os.environ.get("DARK_CANVAS_SECRET"):
        return
    secret_path = data_dir / "session_secret"
    try:
        secret = secret_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        secret = secrets.token_urlsafe(48)
        try:
            with secret_path.open("x", encoding="utf-8") as secret_file:
                secret_file.write(secret)
        except FileExistsError:
            secret = secret_path.read_text(encoding="utf-8").strip()
        else:
            if os.name != "nt":
                secret_path.chmod(0o600)
    if not secret:
        raise RuntimeError(f"Il secret di sessione è vuoto: {secret_path}")
    os.environ["DARK_CANVAS_SECRET"] = secret


def local_network_url(port: int) -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 9))
            address = probe.getsockname()[0]
        address_info = ipaddress.ip_address(address)
        if not address_info.is_private or address_info.is_loopback or address_info.is_link_local:
            return None
    except OSError:
        return None
    return f"http://{address}:{port}"


def normalize_local_url(address: str) -> str:
    candidate = address.strip()
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("Indirizzo del server non valido.") from error
    if parsed.scheme != "http" or not hostname or parsed.username or parsed.password:
        raise ValueError("Inserisci l'indirizzo HTTP locale condiviso dal Director.")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("La porta del server non è valida.")
    try:
        address_info = ipaddress.ip_address(hostname)
    except ValueError:
        normalized_host = hostname.lower().rstrip(".")
        if normalized_host != "localhost" and not normalized_host.endswith(".local"):
            raise ValueError("Usa un indirizzo IP privato o un nome host della rete locale.")
    else:
        if not (
            address_info.is_private
            or address_info.is_loopback
            or address_info.is_link_local
        ):
            raise ValueError("L'indirizzo deve appartenere alla rete locale.")
    return urlunsplit(("http", parsed.netloc, "/", "", ""))


def wait_until_ready(port: int, server_thread: threading.Thread) -> None:
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and server_thread.is_alive():
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError("Il server locale non è diventato disponibile. Controlla che la porta 5055 sia libera.")


class DesktopApplication:
    def __init__(self) -> None:
        self.window: webview.Window | None = None
        self.server = None
        self.server_thread: threading.Thread | None = None
        self.server_stopping = threading.Event()
        self.local_url: str | None = None
        self.join_url: str | None = None
        self.mode = "launcher"

    def start_host(self) -> dict[str, str | bool]:
        if self.mode != "launcher":
            return {"ok": False, "error": "Questa app è già collegata a una partita."}
        self.mode = "starting"
        try:
            data_dir = configure_data_directory()
            configure_host_secret(data_dir)
            port = int(os.environ.get("PORT", "5055"))

            from main import app

            self.server = create_server(app, host="0.0.0.0", port=port, threads=8)
            self.server_stopping.clear()
            self.server_thread = threading.Thread(
                target=self._run_server,
                name="dark-canvas-server",
                daemon=True,
            )
            self.server_thread.start()
            wait_until_ready(port, self.server_thread)
            self.local_url = f"http://127.0.0.1:{port}"
            self.join_url = local_network_url(port)
            self.mode = "hosting"
            return {
                "ok": True,
                "localUrl": self.local_url,
                "joinUrl": self.join_url or "",
            }
        except (OSError, RuntimeError, ValueError) as error:
            logger.exception("Unable to start game server")
            if self.server:
                self.server_stopping.set()
                self.server.close()
                self.server = None
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=3)
            self.server_thread = None
            self.mode = "launcher"
            return {"ok": False, "error": str(error)}

    def join_game(self, address: str) -> dict[str, str | bool]:
        if self.mode != "launcher":
            return {"ok": False, "error": "Questa app è già collegata a una partita."}
        try:
            url = normalize_local_url(address)
        except ValueError as error:
            return {"ok": False, "error": str(error)}
        self.mode = "joining"
        return {"ok": True, "url": url}

    def get_join_url(self) -> str:
        if self.mode != "hosting":
            return ""
        return self.join_url or ""

    def _run_server(self) -> None:
        server = self.server
        if not server:
            return
        try:
            server.run()
        except OSError as error:
            if not (self.server_stopping.is_set() and error.errno == errno.EBADF):
                logger.exception("Game server stopped unexpectedly")

    def _close(self) -> None:
        if self.server:
            self.server_stopping.set()
            self.server.close()
            self.server = None
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=3)


def main() -> None:
    configure_data_directory()
    create_desktop_shortcut()
    app = DesktopApplication()
    launcher_html = (BASE_DIR / "launcher.html").read_text(encoding="utf-8")
    app.window = webview.create_window(
        "Operation Mareggiata",
        html=launcher_html,
        js_api=app,
        width=760,
        height=720,
        min_size=(420, 560),
        background_color="#080d16",
    )
    try:
        webview.start(debug=False)
    finally:
        app._close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        logger.exception("Unable to launch desktop application")
        print(f"Impossibile avviare Operation Mareggiata: {error}", file=sys.stderr)
        raise SystemExit(1) from error
