from __future__ import annotations

import ipaddress
import os
import secrets
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from platformdirs import user_data_dir
from waitress import create_server


def configure_data_directory() -> None:
    data_dir = Path(user_data_dir("Operation Mareggiata"))
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DARK_CANVAS_DB", str(data_dir / "dark_canvas.sqlite3"))
    os.environ.setdefault("DARK_CANVAS_LOG", str(data_dir / "dark_canvas.log"))

    if not os.environ.get("DARK_CANVAS_SECRET"):
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
    raise RuntimeError("Il server locale non è diventato disponibile.")


def main() -> None:
    configure_data_directory()
    port = int(os.environ.get("PORT", "5055"))

    from main import app

    server = create_server(app, host="0.0.0.0", port=port, threads=8)
    server_thread = threading.Thread(target=server.run, name="dark-canvas-server", daemon=True)
    server_thread.start()
    try:
        wait_until_ready(port, server_thread)
        local_url = f"http://127.0.0.1:{port}"
        network_url = local_network_url(port)
        print("\nOperation Mareggiata è in esecuzione.")
        print(f"Director: {local_url}")
        if network_url:
            print(f"Giocatori sulla stessa rete: {network_url}")
        else:
            print("Indirizzo LAN non rilevato: controlla la connessione di rete.")
        print("Lascia aperta questa finestra durante la partita. Premi Ctrl+C per fermare il server.\n")
        webbrowser.open(local_url)
        server_thread.join()
    except KeyboardInterrupt:
        print("\nChiusura del server...")
    finally:
        server.close()
        server_thread.join(timeout=3)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Impossibile avviare Operation Mareggiata: {error}", file=sys.stderr)
        raise SystemExit(1) from error
