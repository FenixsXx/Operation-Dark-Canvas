from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory, session

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DARK_CANVAS_DB", BASE_DIR / "dark_canvas.sqlite3"))
LOG_FILE = Path(os.environ.get("DARK_CANVAS_LOG", BASE_DIR / "dark_canvas.log"))

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("dark_canvas")

app = Flask(__name__, static_folder=None)
if os.environ.get("FLASK_ENV") == "production" and not os.environ.get("DARK_CANVAS_SECRET"):
    raise RuntimeError("DARK_CANVAS_SECRET must be set in production.")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
app.secret_key = os.environ.get("DARK_CANVAS_SECRET", "change-this-dark-canvas-secret")

LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
LOGIN_ATTEMPTS_BY_BADGE: dict[str, list[float]] = defaultdict(list)
MAX_MANDATE_BYTES = 16_384
MAX_PENDING_MANDATES = 3
GAME_DURATION_SECONDS = int(os.environ.get("DARK_CANVAS_GAME_DURATION_SECONDS", "172800"))
GAME_TIME_SCALE = 9.6

ACCOUNTS = {
    "FBI-74291": {"name": "Camilla Moro", "alias": "BLIZZARD", "role": "AGENT"},
    "FBI-88304": {"name": "Pietro Lagorio", "alias": "PHANTOM", "role": "AGENT"},
    "FBI-51926": {"name": "Riccardo Orecchia", "alias": "ROOK", "role": "AGENT"},
    "FBI-30472": {"name": "Giulia Masullo", "alias": "GHOST", "role": "AGENT"},
    "FBI-66185": {"name": "Gabriele Cancedda", "alias": "GRANITE", "role": "AGENT"},
    "FBI-99210": {"name": "Azzurra", "alias": "AZURE", "role": "AGENT"},
    "FBI-44819": {"name": "Diletta", "alias": "DAGGER", "role": "AGENT"},
    "FBI-00001": {"name": "Director", "alias": "THE ARCHITECT", "role": "DIRECTOR"},
}


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def validate_payload_size(payload: dict[str, Any], maximum_bytes: int = MAX_MANDATE_BYTES) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) > maximum_bytes:
        raise ValueError("Payload della richiesta troppo grande.")


def new_csrf_token() -> str:
    return hashlib.sha256(os.urandom(32)).hexdigest()
    
def safe_json_loads(value: str, *, context: str) -> dict[str, Any]:
    try:
        result = json.loads(value)
        if not isinstance(result, dict):
            raise ValueError("JSON root is not an object")
        return result
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.error("Invalid JSON context=%s error=%s", context, exc)
        return {}


@app.before_request
def enforce_csrf() -> None:
    if request.method not in {"POST", "PUT", "DELETE", "PATCH"}:
        return
    if request.path in {"/api/login"}:
        return
    if request.path.startswith("/api/") and session.get("badge"):
        token = request.headers.get("X-CSRF-Token") or (request.get_json(silent=True) or {}).get("csrf_token")
        if not token or not hmac.compare_digest(str(token), str(session.get("csrf_token", ""))):
            return jsonify({"error": "Token CSRF non valido."}), 403


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; media-src 'self'; frame-src 'self'; frame-ancestors 'self'; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.path == "/api/state" and response.status_code < 400 and response.is_json:
        payload = response.get_json()
        if isinstance(payload, dict):
            payload["serverNow"] = datetime.now(timezone.utc).isoformat()
            response.set_data(app.json.dumps(payload))
    if response.status_code >= 400:
        logger.warning("HTTP %s %s badge=%s", response.status_code, request.path, session.get("badge", "anonymous"))
    return response


@app.errorhandler(500)
def handle_unexpected_error(error):
    logger.exception("Unhandled server error path=%s badge=%s", request.path, session.get("badge", "anonymous"))
    return jsonify({"error": "Errore interno del server."}), 500


def initialize_db() -> None:
    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mandates (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                owner_badge TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS game_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_evidence_unlocks (
                evidence_id TEXT NOT NULL,
                unlocked_by TEXT NOT NULL,
                unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                team_wide INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (evidence_id, team_wide)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS case_resolutions (
                owner_badge TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'DRAFT',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        resolution_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='case_resolutions'"
        ).fetchone()["sql"] or ""
        if "status TEXT" not in resolution_schema:
            connection.execute("ALTER TABLE case_resolutions ADD COLUMN status TEXT NOT NULL DEFAULT 'DRAFT'")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS board_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('note', 'event', 'hint')),
                owner_badge TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        board_schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='board_entries'"
        ).fetchone()["sql"] or ""
        if "'hint'" not in board_schema:
            connection.execute("ALTER TABLE board_entries RENAME TO board_entries_legacy")
            connection.execute(
                """
                CREATE TABLE board_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL CHECK(kind IN ('note', 'event', 'hint')),
                    owner_badge TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "INSERT INTO board_entries (id, kind, owner_badge, owner_name, text, created_at) SELECT id, kind, owner_badge, owner_name, text, created_at FROM board_entries_legacy"
            )
            connection.execute("DROP TABLE board_entries_legacy")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_badge TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO game_meta (key, value) VALUES ('version', '1')"
        )
        connection.commit()


def serialize_mandates(owner_badge: str | None = None) -> list[dict[str, Any]]:
    with connect_db() as connection:
        if owner_badge:
            rows = connection.execute(
                "SELECT payload, status, owner_badge FROM mandates WHERE owner_badge=? ORDER BY created_at, id",
                (owner_badge,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT payload, status, owner_badge FROM mandates ORDER BY created_at, id"
            ).fetchall()
    mandates = []
    for display_id, row in enumerate(rows, start=1):
        mandate = safe_json_loads(row["payload"], context="mandate")
        if not mandate.get("id"):
            logger.error("Skipping invalid mandate owner=%s", row["owner_badge"])
            continue
        mandate["displayId"] = display_id
        mandate["status"] = row["status"]
        mandate["ownerBadge"] = row["owner_badge"]
        mandate["ownerName"] = ACCOUNTS.get(row["owner_badge"], {}).get(
            "name", "Sconosciuto"
        )
        mandates.append(mandate)
    return mandates


def game_version(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT value FROM game_meta WHERE key='version'"
    ).fetchone()
    return int(row["value"]) if row else 1


def game_started_at(connection: sqlite3.Connection) -> str | None:
    row = connection.execute(
        "SELECT value FROM game_meta WHERE key='started_at'"
    ).fetchone()
    return row["value"] if row else None


def require_started_case(connection: sqlite3.Connection):
    if not game_started_at(connection):
        return jsonify({"error": "Il caso non è ancora stato avviato dal Director."}), 409
    return None


def require_open_case(connection: sqlite3.Connection):
    started_at = game_started_at(connection)
    if not started_at:
        return require_started_case(connection)

    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        logger.error("Invalid game start timestamp: %s", started_at)
        return jsonify({"error": "Timestamp di avvio del caso non valido; contattare il Director."}), 500

    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    deadline = started + timedelta(seconds=GAME_DURATION_SECONDS / GAME_TIME_SCALE)
    if datetime.now(timezone.utc) >= deadline:
        return jsonify({"error": "Scadenza del caso raggiunta: non è più possibile inviare richieste, note o teorie."}), 409
    return None


def serialize_board() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT kind, owner_badge, owner_name, text, created_at FROM board_entries ORDER BY created_at, id"
        ).fetchall()
    notes = [
        {"actorBadge": row["owner_badge"], "actorName": row["owner_name"], "text": row["text"], "at": row["created_at"]}
        for row in rows if row["kind"] == "note"
    ]
    events = [
        {"actorBadge": row["owner_badge"], "actorName": row["owner_name"], "text": row["text"], "at": row["created_at"]}
        for row in rows if row["kind"] == "event"
    ]
    return notes, events


def serialize_hints(recipient_badge: str | None = None) -> list[dict[str, Any]]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT id, owner_badge, owner_name, text, created_at FROM board_entries WHERE kind='hint' AND (owner_badge=? OR ?='FBI-00001') ORDER BY created_at, id",
            (recipient_badge or "", recipient_badge or ""),
        ).fetchall()
    return [
        {"id": row["id"], "actorBadge": row["owner_badge"], "actorName": row["owner_name"], "text": row["text"], "at": row["created_at"]}
        for row in rows
    ]


def serialize_resolution(badge: str) -> dict[str, Any] | None:
    with connect_db() as connection:
        row = connection.execute(
            "SELECT payload, status, updated_at FROM case_resolutions WHERE owner_badge=?",
            (badge,),
        ).fetchone()
    if not row:
        return None
    resolution = safe_json_loads(row["payload"], context="resolution")
    if not resolution:
        return None
    resolution["status"] = row["status"]
    resolution["updatedAt"] = row["updated_at"]
    return resolution


def serialize_resolutions() -> list[dict[str, Any]]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT owner_badge, payload, status, updated_at FROM case_resolutions ORDER BY updated_at, owner_badge"
        ).fetchall()
    resolutions = []
    for row in rows:
        resolution = safe_json_loads(row["payload"], context="resolution-list")
        if not resolution:
            continue
        resolutions.append({**resolution, "ownerBadge": row["owner_badge"], "ownerName": ACCOUNTS.get(row["owner_badge"], {}).get("name", "Sconosciuto"), "status": row["status"], "updatedAt": row["updated_at"]})
    return resolutions


def manual_evidence_unlocked(evidence_id: str, badge: str) -> bool:
    with connect_db() as connection:
        row = connection.execute(
            "SELECT 1 FROM manual_evidence_unlocks WHERE evidence_id=? AND (team_wide=1 OR unlocked_by=?)",
            (evidence_id, badge),
        ).fetchone()
    return row is not None


def serialize_manual_unlocks() -> list[dict[str, Any]]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT evidence_id, unlocked_by, unlocked_at, team_wide FROM manual_evidence_unlocks ORDER BY unlocked_at, evidence_id"
        ).fetchall()
    return [dict(row) for row in rows]


def evidence_summary(badge: str, is_director: bool) -> dict[str, Any]:
    manual_ids = {item["evidence_id"] for item in serialize_manual_unlocks() if item["team_wide"] or item["unlocked_by"] == badge}
    acquired_ids = (team_acquired_evidence(manual_ids) if is_director else approved_evidence_for_agent(badge) | manual_ids)
    authorized_ids = set(EVIDENCE) if is_director else PUBLIC_EVIDENCE | acquired_ids
    return {
        "catalogTotal": len(EVIDENCE),
        "authorizedTotal": len(authorized_ids),
        "acquiredTotal": len(acquired_ids),
        "acquiredIds": sorted(acquired_ids),
    }


def team_acquired_evidence(manual_ids: set[str] | None = None) -> set[str]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT payload FROM mandates WHERE status='APPROVED'"
        ).fetchall()
    acquired = {
        evidence_id
        for row in rows
        for evidence_id in EVIDENCE_BY_WARRANT.get(safe_json_loads(row["payload"], context="team-evidence").get("target"), [])
    }
    acquired.update(manual_ids if manual_ids is not None else {item["evidence_id"] for item in serialize_manual_unlocks() if item["team_wide"]})
    return acquired


def agent_evidence_summaries() -> dict[str, dict[str, Any]]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT owner_badge, payload FROM mandates WHERE status='APPROVED'"
        ).fetchall()
    acquired_by_agent: dict[str, set[str]] = {
        badge: set() for badge, account in ACCOUNTS.items() if account["role"] == "AGENT"
    }
    for row in rows:
        acquired_by_agent[row["owner_badge"]].update(
            EVIDENCE_BY_WARRANT.get(safe_json_loads(row["payload"], context="agent-evidence").get("target"), [])
        )
    manual_unlocks = serialize_manual_unlocks()
    for item in manual_unlocks:
        if item["team_wide"]:
            for badge, account in ACCOUNTS.items():
                if account["role"] == "AGENT":
                    acquired_by_agent[badge].add(item["evidence_id"])
        elif item["unlocked_by"] in acquired_by_agent:
            acquired_by_agent[item["unlocked_by"]].add(item["evidence_id"])
    return {
        badge: {
            "acquiredTotal": len(ids := acquired_by_agent[badge]),
            "acquiredIds": sorted(ids),
        }
        for badge, account in ACCOUNTS.items()
        if account["role"] == "AGENT"
    }


@app.get("/")
def homepage():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/state")
def get_state():
    if not session.get("badge"):
        return jsonify({"error": "Sessione non autenticata."}), 401
    with connect_db() as connection:
        version = game_version(connection)
        started_at = game_started_at(connection)
    notes, events = serialize_board()
    is_director = ACCOUNTS[session["badge"]]["role"] == "DIRECTOR"
    return jsonify({"requests": serialize_mandates() if is_director else serialize_mandates(session["badge"]), "notes": notes, "events": events, "hints": serialize_hints(session.get("badge")), "resolution": serialize_resolution(session["badge"]), "resolutions": serialize_resolutions() if is_director else [], "manualEvidence": serialize_manual_unlocks() if is_director else [item for item in serialize_manual_unlocks() if item["team_wide"] or item["unlocked_by"] == session["badge"]], "gameVersion": version, "gameStartedAt": started_at, "gameDurationSeconds": GAME_DURATION_SECONDS, "gameTimeScale": GAME_TIME_SCALE, "evidenceSummary": evidence_summary(session["badge"], is_director), "agentEvidenceSummary": agent_evidence_summaries() if is_director else {}})


@app.route("/api/activity", methods=["GET", "POST"])
def activity_state():
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401

    with connect_db() as connection:
        if request.method == "GET":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Director può leggere le attività."}), 403
            rows = connection.execute(
                "SELECT owner_badge, activity_type, value, created_at FROM activity_log ORDER BY id DESC LIMIT 500"
            ).fetchall()
            rows = list(reversed(rows))
            return jsonify({
                "activities": [
                    {
                        "ownerBadge": row["owner_badge"],
                        "type": row["activity_type"],
                        "value": row["value"],
                        "at": row["created_at"],
                    }
                    for row in rows
                ]
            })

        if actor["role"] != "AGENT":
            return jsonify({"error": "Solo un agente può registrare attività."}), 403
        payload = request.get_json(silent=True) or {}
        activity_type = payload.get("type")
        value = str(payload.get("value", "")).strip()
        if activity_type not in {"searches", "dossiers", "openedEvidence", "openedApps"} or not value:
            return jsonify({"error": "Attività non valida."}), 400
        connection.execute(
            "INSERT INTO activity_log (owner_badge, activity_type, value) VALUES (?, ?, ?)",
            (badge, activity_type, value),
        )
        connection.commit()
    return jsonify({"ok": True})


@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    badge = str(payload.get("badge", "")).strip()
    ip = request.remote_addr or "unknown"
    now = time.time()
    attempts = LOGIN_ATTEMPTS[ip]
    attempts[:] = [when for when in attempts if now - when < 300]
    badge_attempts = LOGIN_ATTEMPTS_BY_BADGE[badge]
    badge_attempts[:] = [when for when in badge_attempts if now - when < 300]
    if len(attempts) >= 5 or len(badge_attempts) >= 5:
        return jsonify({"error": "Troppi tentativi. Riprova tra 5 minuti."}), 429
    account = ACCOUNTS.get(badge)
    supplied_name = payload.get("name", "").strip().casefold()
    valid_names = (
        {account["name"].casefold(), account["alias"].casefold()}
        if account
        else set()
    )
    if not account or supplied_name not in valid_names:
        attempts.append(now)
        if account:
            badge_attempts.append(now)
        return jsonify({"error": "Credenziali non riconosciute."}), 401
    attempts.clear()
    badge_attempts.clear()
    session.permanent = True
    session["badge"] = badge
    session["role"] = account["role"]
    session["csrf_token"] = new_csrf_token()
    return jsonify({"badge": badge, "role": account["role"], "csrfToken": session["csrf_token"]})


EVIDENCE = {
    "EV-01": ("Bicchiere in cristallo", "REPERTO EV-01 — BICCHIERE IN CRISTALLO\n\nRinvenuto sul sottobicchiere della Sala Blu. Il profilo genetico della componente salivare è compatibile con il campione di riferimento di Matteo Rinaldi. Il risultato assume valore associativo insieme alla pulizia documentata del bicchiere, alla sovrapposizione delle tracce e agli altri elementi temporali; il solo DNA non consente di determinare l'ora del deposito."),
    "EV-02": ("Tablet Apple iPad Pro", "REPERTO EV-02 — ESTRATTO FORENSE TABLET PERSONALE\n\nDispositivo: Apple iPad Pro 12.9\" (grigio siderale) — proprietà Nathaniel Cross\nApplicazione: Notes (database SQLite)\nFile: Suicide_note_20261003_234712.txt\nRiferimento hash SHA-256: valore integrale non riportato in questo estratto\nTimestamp: 2026-10-03 23:47:12 CEST (UTC+02:00)\nLayout tastiera: IT-IT (dizionario predittivo italiano — ANOMALO)\nInput forense: latenza media intercarattere 412 ms; picco 1.240 ms sulla sequenza 'ogne'\nConteggio: 117 parole in lingua italiana\n\nCONTENUTO TESTUALE RIPRODOTTO\nNon ce la faccio piu. Il dolore è ormai insostenibile e questa malattia mi ha ridotto a un ombra di quello che ero. Isabella, tu lo sai che ho sempre cercato di proteggerti e sostenerti ma ho fallito in tutto. Il progetto Nettuno mi ha consumato anima e corpo e adesso non ho piu alcuna via di scampo. Ho deciso di partire. Prima che il cancro mi annienti del tutto. Non voglio piu essere un peso per nessuno di voi. Non cercate di capire o di giudicare, non ce redenzione possibile per quello che ho fatto e per i segreti oscuri che ho dovuto portare con me fino a questo giorno.\n\nLasciate ogne speranza voi ch intrate.\n\n[FINE ESTRATTO — timestamp file system: 2026-10-03T23:47:12+02:00]"),
    "EV-03": ("Glock 19 · GNN447US", "REPERTO EV-03 — PISTOLA SEMIAUTOMATICA\n\nCaricatore inserito e privo di cartucce; un bossolo repertato sulla scena e un proiettile recuperato dal pannello. Lividità dorsali parzialmente fisse, non coerenti con la posizione finale descritta negli atti come semiseduta, con il tronco inclinato in avanti: il dato è compatibile con un riposizionamento del corpo, ma non ne stabilisce l’ora né, da solo, la dinamica. Lesione termica sul palmo destro; nessun GSR rilevabile sulle mani della vittima. Ingresso alla tempia sinistra e uscita parietale destra. Lo schema BAL-447-GN-031-A è orientativo, non in scala (direzione generale, azimut 114°, inclinazione -4°), e non consente di stabilire postura, lateralità o identità dell'autore materiale."),
    "EV-04": ("Fibra tessile nera", "Fibra di 8 mm rinvenuta nella griglia del condotto di ventilazione. Presenta caratteristiche morfologiche, cromatiche e chimiche compatibili con il campione del cappotto Schneiders Loden di Rinaldi. La lacerazione rilevata sul capo è coerente per posizione e morfologia con il distacco della fibra."),
    "EV-05": ("Impronta su terrazzo bagnato", "Pattern esagonale regolare, taglia 44. L'impronta è compatibile per marca, modello, misura e disegno della suola con gli scarponcini Timberland sequestrati a Rinaldi; una caratteristica accidentale sul tacco destro aumenta il valore associativo. La stima del peso non è identificativa."),
    "EV-06": ("Scontrino Marina Park", "Scontrino emesso il 3 ottobre 2026 alle 22:15:07, durata quattro ore. Il timestamp documenta il pagamento; la posizione del veicolo a 180 metri dalla scena e l'ingresso al parcheggio sono riscontri separati da GPS e barriera."),
    "EV-07": ("Biglietto Teatro Carlo Felice", "Conferma l'ingresso di Isabella al posto palco D4, ma il codice a barre documenta solo l'accesso iniziale. Il registro dei posti mostra il posto vuoto durante il secondo atto, dopo l'intervallo."),
    "EV-08": ("Bozza al notaio", "REPERTO EV-08 — BOZZA EMAIL RECUPERATA DA CARTELLA CIFRATA\n\nProfilo utente: Nathaniel Cross\nDa: nathaniel.cross@nettuno.nato.int\nA: studio.bianchi-notaio@legal.ge.it\nDestinatario: Dott. Alessandro Bianchi, notaio\nOggetto: Disposizioni testamentarie e riconoscimento di paternità naturale\nData bozza: 2 ottobre 2026 14:30:22 CEST (UTC+02:00)\n\nLa bozza contiene una richiesta urgente relativa alle disposizioni testamentarie di Cross e alla sua intenzione di riconoscere Matteo Rinaldi come figlio naturale, attribuendogli una quota ereditaria e specifici diritti collegati al progetto Nettuno.\n\n[STATO: BOZZA NON INVIATA — recuperata da cartella cifrata protetta da password]"),
    "EV-09": ("Finestra temporale autoptica", "Stima del decesso compresa tra le 22:45 e le 23:15 del 3 ottobre 2026. Le 23:00 costituiscono il punto centrale convenzionale della stima e non un timestamp medico-legale esatto."),
    "EV-10": ("Log NVR locale · copia acquisita", "ESTRATTO LOG NVR — SESSIONE LOCALE [ALTERATA]\n\nAlle 01:05 del 4 ottobre una rotazione dei log è stata forzata da admin@192.168.1.47; una voce è stata eliminata e il checksum della partizione auth non coincide. Il log locale è stato alterato."),
    "EV-11": ("Log NVR cloud · backup originale", "ESTRATTO LOG NVR — SESSIONE CLOUD BACKUP [ORIGINALE]\n\n[2026-10-03 23:45:12] [NVR-AUTH] [ALERT] BADGE_SCAN: ID=CLONE-0x9F4A2B1C | READER=BLU_MAIN_01\n[2026-10-03 23:45:12] [NVR-AUTH] [ALERT] STATUS: ACCESS_DENIED | REASON: CLEARANCE_INVALID\n[2026-10-03 23:45:13] [NVR-ALERT] [WARN] Unauthorized entry attempt logged | SRC=LOCAL_BADGE_READER\n[2026-10-04 01:05:47] [NVR-ADMIN] [ALERT] REMOTE_LOGIN: USER=admin | SRC_IP=192.168.1.47\n[2026-10-04 01:05:48] [NVR-DB] [CRIT] ENTRY_MODIFIED: TABLE=access_logs | ID=447_231003_234512\n[2026-10-04 01:05:48] [NVR-DB] [CRIT] FIELD=event_status | OLD=ACCESS_DENIED | NEW=NULL\n[2026-10-04 01:05:49] [NVR-DB] [CRIT] RECORD_DELETED: ID=447_231003_234512 | BACKUP_FLAG=FALSE\n[2026-10-04 01:05:50] [NVR-SYS] [ERR] INTEGRITY_CHECK_FAIL: SHA256 mismatch on log segment 447-231003-2345\n\nNota analitica: il backup cloud conserva la traccia originale del tentativo di accesso alle 23:45 con badge clonato, successivamente cancellato dalla sessione remota."),
    "EV-12": ("Tabulati telefonici", "Il dispositivo di Isabella risulta compatibile con la presenza nell'area di copertura comprendente Palazzo Doria dalle 22:08 alle 22:26; il dato non dimostra ingresso, piano o accesso alla Sala Blu. Dalle 22:26 alle 23:58 risulta compatibile con l'area di Via del Campo. Alle 22:12 effettua una chiamata anonima di 45 secondi a Kyle Brennan. Il telefono di Rinaldi resta spento dalle 20:45 alle 23:56."),
    "EV-13": ("GPS veicolo GE-AB-447", "Traccia del veicolo: ingresso al Marina Park alle 22:15:07, partenza alle 00:02 e arrivo alla palestra FitActive alle 00:14. Conferma la presenza del veicolo nell'area della scena."),
    "EV-14": ("Dispositivi e accessi · camera Sharma", "Correlazione tra identificativo del dispositivo, rete Wi-Fi della camera 322 del Grand Hotel Savoia, orari di connessione e accesso remoto all'IP 192.168.1.47. Le fonti collegano il dispositivo alla sessione che ha alterato i log NVR, ma l'indirizzo IP non identifica da solo l'utilizzatore."),
    "EV-15": ("Chiamata al 112 · rapporto Brennan", "REPERTO EV-15 — REGISTRAZIONE CHIAMATA DI EMERGENZA\n\nCentrale operativa: NUE 112 Genova\nData: 4 ottobre 2026\nOra di inizio: 01:23:14\nDurata: 02:11\nChiamante dichiarato: Kyle Brennan\nOggetto: rinvenimento del corpo di Nathaniel Cross\n\nESTRATTO DELLA COMUNICAZIONE\n\nBrennan riferisce di essere entrato nell'area del terzo piano poco prima della chiamata e di aver trovato Nathaniel Cross privo di reazione nella Sala Blu. Il chiamante dichiara di non aver toccato l'arma e di avere verificato soltanto l'assenza di risposta della vittima prima di contattare i soccorsi.\n\nDATI DI CORRELAZIONE\n\nIl registro degli accessi EV-16 attribuisce alla credenziale KB-19 un ingresso al terzo piano alle 00:43:58. Tra l'accesso registrato e l'inizio della chiamata trascorrono circa 39 minuti.\n\nLa registrazione documenta l'orario della segnalazione e il contenuto delle dichiarazioni rese alla centrale. Non consente, isolatamente, di stabilire l'orario esatto del ritrovamento né le attività svolte dal chiamante nell'intervallo precedente."),
    "EV-16": ("Registro accessi verticali · Palazzo Doria", "20:14:51 — Chiamata ascensore dal piano 3 al piano terra, compatibile con la partenza iniziale di Isabella verso il teatro.\n22:07:43 — Porta vano scale S3 aperta con chiave residenziale; nessun accesso Sala Blu registrato.\n22:25:19 — Porta vano scale S3 aperta in uscita; permanenza nell'area residenziale circa 17 minuti.\n00:43:58 — Porta principale terzo piano aperta con credenziale sicurezza KB-19, compatibile con ingresso Brennan.\n\nConclusione limitata: il registro colloca Isabella nell'area del palazzo, ma non dimostra un ingresso nella Sala Blu. Il primo ingresso attribuibile con ragionevole certezza a Brennan avviene alle 00:44 circa."),
    "EV-17": ("Agenda cartacea di Nathaniel Cross", "Agenda professionale acquisita nell'ufficio privato di Nathaniel Cross. Nella pagina del 3 ottobre 2026 compaiono le annotazioni manoscritte «M.R. — parlare dopo la riunione.» e «Non rimandare ancora.». Le iniziali non identificano autonomamente una persona e il documento non specifica l'oggetto della conversazione."),
    "EV-18": ("Contratto tecnico HVAC · Sala Blu", "Commessa NETTUNO-SB-HVAC-2025-03. Revisione ventilazione secondaria Sala Blu, terzo piano. Matteo Rinaldi era responsabile dell'elettronica di controllo e dei sensori, partecipò ai collaudi e firmò la tavola con le quote della griglia occidentale. Altri sei tecnici ebbero accesso al progetto. Il documento dimostra conoscenza tecnica e opportunità, non presenza fisica nella notte dell'omicidio."),
    "EV-19": ("Inventario armeria · Progetto Nettuno", "Glock 19, matricola GNN447US, calibro 9×19 mm. Stato inventario: anomalia di custodia. Ultima verifica ordinaria: 30 settembre 2026; verifica successiva prevista: 7 ottobre 2026. La voce del 3 ottobre indica l'apertura dell'armadietto tecnico mediante credenziale di manutenzione, senza identificare con certezza l'utilizzatore materiale."),
    "EV-20": ("Rapporto meteorologico e limiti di datazione EV-05", "21:00 — precipitazioni moderate. 21:31 — aumento significativo. 22:10 — superficie del terrazzo progressivamente satura. 22:45–23:15 — pioggia intensa e vento forte. 00:30 — superficie ancora bagnata.\n\nEV-05 presenta contorni compatibili con deposizione su superficie satura. La morfologia dell'acqua non consente una datazione al minuto: l'intervallo prudente deve essere ristretto attraverso accessi, fibra, GPS e testimonianze."),
    "EV-21": ("Ricevuta taxi · Isabella Cross", "Ricevuta relativa a una corsa effettuata il 3 ottobre 2026, con partenza dall'area del Teatro Carlo Felice alle 21:56:18 e arrivo nell'area di Salita Santa Caterina alle 22:07:42. Il documento conferma lo spostamento verso l'area di Palazzo Doria, ma non dimostra l'ingresso nell'edificio, il piano raggiunto o l'accesso alla Sala Blu."),
    "EV-22": ("Registro occupazione palco D4", "20:16 — Biglietto EV-07 scansionato all'ingresso, posto palco D4. Primo atto: posto inizialmente occupato. Intervallo: movimento del pubblico non tracciato individualmente. Secondo atto: posto D4 non occupato durante il controllo di sala. Il biglietto dimostra l'ingresso iniziale, non la permanenza per l'intero spettacolo."),
    "EV-23": ("Log Wi-Fi · Camera 322", "Struttura: Grand Hotel Savoia. Camera: 322. Dispositivo coerente con quello acquisito a Priya Sharma. 20:21 circa — associazione alla rete Wi-Fi della camera. 00:58 circa — nuova sessione di rete. 01:05 circa — connessione correlata alla sessione amministrativa che altera i log NVR. Fonti: log Wi-Fi, lease DHCP e correlazione temporale con EV-10 ed EV-11. Le fonti collegano il dispositivo alla sessione remota, ma IP, rete e identificativo tecnico non dimostrano isolatamente chi lo utilizzasse."),
    "EV-24": ("Movimenti finanziari · pratica OC-24", "ESTRATTO MOVIMENTI FINANZIARI — OCEANIC CONSULTING LLC\n\n26 settembre 2026 — Beneficiario: Grand Hotel Savoia. Descrizione: permanenza operativa.\n28 settembre 2026 — Descrizione: acquisto dispositivo di rete. Categoria: materiale tecnico.\n2 ottobre 2026 — Descrizione: servizio di comunicazione cifrata. Categoria: consulenza informatica.\n4 ottobre 2026 — Operazione: tentativo di trasferimento sospeso. Destinatario: consulente estero.\n\nNota analitica: i movimenti sono compatibili con un'attività operativa coperta e rafforzano il filone della manipolazione informatica. Non collegano Priya Sharma alla dinamica materiale dello sparo."),
    "EV-25": ("Materiale fotografico Isabella Cross e Kyle Brennan", "Serie fotografica acquisita con relativi metadati tecnici. EV-25A documenta un incontro riservato nell'area di un ristorante il 18 settembre 2026; EV-25B documenta un secondo incontro nell'area di Via del Campo il 27 settembre 2026. EV-25C rileva continuità tecnica fra i file e compatibilità con il medesimo dispositivo di acquisizione. Il materiale sostiene l'esistenza di una frequentazione non dichiarata, ma non colloca i soggetti nella Sala Blu e non li collega alla dinamica materiale dello sparo."),
    "EV-26": ("Esclusione balistica · Arma Brennan", "Arma esaminata: Beretta M9 attribuita a Kyle Brennan. Il bossolo EV-03, il proiettile recuperato, canna, percussore ed estrattore sono incompatibili con l'arma sequestrata. Il caricatore era completo e non risultano dati significativi che la colleghino al colpo. Il risultato esclude la Beretta come arma utilizzata, ma non costituisce da solo un alibi personale completo per Brennan."),
    "EV-27": ("Analisi fibre · Cappotto Isabella Cross", "Campione: cappotto sequestrato a Isabella Cross. Il confronto con EV-04 non mostra compatibilità significativa: morfologia, diametro, composizione, colorazione e trattamento superficiale differiscono dal campione della griglia. Il risultato chiude la pista del condotto, ma non scagiona Isabella dalle menzogne sull'alibi e sulla relazione."),
    "EV-28": ("Verifica trasporti pubblici · Matteo Rinaldi", "Intervallo analizzato: 3 ottobre 2026, 20:30–00:30. Fonti: tornelli, titoli di viaggio associati, transazioni, telecamere disponibili e registro anomalie. Nessun passaggio attribuibile a Matteo Rinaldi nella finestra dichiarata. L'assenza di registrazione contraddice il percorso specifico dell'interrogatorio, ma non dimostra isolatamente la sua posizione."),
    "EV-29": ("Sequenza video e registri badge · FitActive", "La sequenza CCTV documenta l'utilizzo della credenziale FT-GE-447, associata a Matteo Rinaldi, da parte di una persona diversa dal titolare. EV-29B riprende la persona nella zona d'ingresso alle 20:58:41; EV-29A documenta l'accettazione della credenziale al tornello 02 alle 21:01:16. EV-29C rileva caratteristiche compatibili con il campione amministrativo attribuito a Luca Greco. La qualità dei fotogrammi non consente un'identificazione biometrica individualizzante, ma dimostra che il registro del badge non prova la presenza fisica di Rinaldi in palestra."),
    "EV-30": ("Memo vocale non inviato · Nathaniel Cross", "Memo vocale locale registrato il 2 ottobre 2026 e rimasto non inviato sul dispositivo personale di Nathaniel Cross. Nel messaggio Cross afferma di aver chiesto al notaio di preparare alcuni documenti e manifesta l'intenzione di parlare con Matteo il giorno seguente. Il memo chiarisce il significato emotivo delle annotazioni EV-17 e della bozza EV-08, ma non identifica autonomamente l'autore dell'omicidio."),
}
EVIDENCE_BY_WARRANT = {"rinaldiPerson": ["EV-01"], "rinaldiVehicle": ["EV-06"], "rinaldiTerrace": ["EV-04", "EV-05", "EV-20"], "crossTablet": ["EV-02"], "salaBluTerminal": ["EV-08"], "autopsyReport": ["EV-03"], "sharmaHotel": ["EV-14", "EV-23"], "nvrLogs": ["EV-10"], "nvrBackup": ["EV-11"], "phoneRecords": ["EV-12"], "brennanEmergencyCall": ["EV-15"], "vehicleGPS": ["EV-13"], "palazzoAccessLogs": ["EV-16"], "crossOffice": ["EV-17"], "hvacDocumentation": ["EV-18"], "nettunoArmory": ["EV-19"], "isabellaMovements": ["EV-21"], "isabellaTheatre": ["EV-07", "EV-22"], "sharmaFinancials": ["EV-24"], "crossBrennanRelationship": ["EV-25"], "brennanWeapon": ["EV-26"], "isabellaClothing": ["EV-27"], "rinaldiTransit": ["EV-28"], "rinaldiGym": ["EV-29"]}
INTERVIEW_TARGETS = {
    "interviewRinaldi": {"title": "Interrogatorio · Matteo Rinaldi", "person": "Matteo Rinaldi"},
    "interviewSharma": {"title": "Interrogatorio · Priya Sharma", "person": "Priya Sharma"},
    "interviewIsabella": {"title": "Interrogatorio · Isabella Cross", "person": "Isabella Cross"},
    "interviewBrennan": {"title": "Interrogatorio · Kyle Brennan", "person": "Kyle Brennan"},
}
VALID_REQUEST_TARGETS = set(EVIDENCE_BY_WARRANT) | set(INTERVIEW_TARGETS)
WARRANT_METADATA = {
    "rinaldiPerson": ("Matteo Rinaldi · Campioni di confronto", "Acquisizione dei campioni biologici e dei rilievi necessari alla comparazione forense."),
    "rinaldiVehicle": ("Veicolo GE-AB-447 · Marina Park", "Verifica del veicolo e dello scontrino di parcheggio."),
    "rinaldiTerrace": ("Terrazzo e condotto di ventilazione", "Rilievi sul percorso di accesso secondario alla Sala Blu."),
    "crossTablet": ("Tablet della vittima", "Acquisizione forense del dispositivo di Nathaniel Cross."),
    "salaBluTerminal": ("Terminale fisso Sala Blu", "Acquisizione della posta e dei documenti del terminale."),
    "autopsyReport": ("Arma e accertamenti balistici · Sala Blu", "Esame della Glock 19, del bossolo, del proiettile e della traiettoria."),
    "sharmaHotel": ("Camera Sharma · Grand Hotel Savoia", "Verifica dei dispositivi e degli accessi della soggetta Sharma."),
    "nvrLogs": ("Log NVR Palazzo Doria", "Confronto tra log originale cloud e copia locale."),
    "nvrBackup": ("Backup cloud NVR · Palazzo Doria", "Richiesta di confronto con il backup originale dei log."),
    "brennanEmergencyCall": ("Centrale 112 · segnalazione Brennan", "Acquisizione della registrazione, dei metadati e del rapporto cronologico relativi alla chiamata di emergenza."),
    "phoneRecords": ("Tabulati telefonici · 3 ottobre", "Acquisizione delle celle e delle chiamate dei soggetti."),
    "vehicleGPS": ("GPS veicolo GE-AB-447", "Localizzazione del veicolo collegato a Matteo Rinaldi."),
    "palazzoAccessLogs": ("Registri accessi verticali · Palazzo Doria", "Acquisizione dei registri di accesso al terzo piano."),
    "crossOffice": ("Ufficio e agenda di Nathaniel Cross", "Perquisizione degli effetti personali e dell'agenda della vittima."),
    "hvacDocumentation": ("Documentazione HVAC · Sala Blu", "Acquisizione di contratti, tavole tecniche e registri dei collaudi."),
    "nettunoArmory": ("Inventario armeria · Progetto Nettuno", "Verifica della custodia e movimentazione della Glock 19."),
    "isabellaMovements": ("Spostamenti Isabella Cross", "Acquisizione di taxi, pagamenti e tracciati degli spostamenti."),
    "isabellaTheatre": ("Teatro Carlo Felice · registri serata", "Acquisizione dei dati di biglietteria e controllo sala."),
    "sharmaFinancials": ("Movimenti finanziari pertinenti", "Acquisizione dei movimenti finanziari pertinenti all’indagine."),
    "crossBrennanRelationship": ("Contatti personali · accertamenti fotografici", "Acquisizione del materiale fotografico e dei metadati collegati."),
    "brennanWeapon": ("Arma di servizio · Kyle Brennan", "Sequestro e comparazione balistica dell'arma attribuita a Brennan."),
    "isabellaClothing": ("Indumenti Isabella Cross", "Comparazione del cappotto con la fibra repertata."),
    "rinaldiTransit": ("Trasporti pubblici · Matteo Rinaldi", "Verifica dei passaggi e dei titoli di viaggio."),
    "rinaldiGym": ("Registri della palestra FitActive", "Acquisizione dei filmati e dei dati del tornello nella finestra investigativa."),
}
PUBLIC_EVIDENCE = {"EV-09"}
EVIDENCE_FORMATS = {"EV-02": "document", "EV-04": "image", "EV-08": "document", "EV-10": "log", "EV-11": "log", "EV-16": "log", "EV-17": "image", "EV-18": "document", "EV-19": "log", "EV-20": "document", "EV-21": "image", "EV-22": "document", "EV-23": "log", "EV-24": "document", "EV-25": "gallery", "EV-26": "document", "EV-27": "document", "EV-28": "document", "EV-29": "gallery"}
EVIDENCE_IMAGES = {"EV-04": "(NEW) EV-04.png", "EV-05": "(NEW) EV-05.png", "EV-17": "assets/evidence/EV-17.png", "EV-21": "assets/evidence/EV-21.png"}
EVIDENCE_GALLERIES = {"EV-25": [("assets/evidence/EV-25A.png", "Scatto nell'area del ristorante"), ("assets/evidence/EV-25B.png", "Scatto nell'area di Via del Campo"), ("assets/evidence/EV-25C.png", "Estratto metadati")], "EV-29": [("assets/evidence/EV-29A.png", "Fotogramma tornello"), ("assets/evidence/EV-29B.png", "Fotogramma ingresso"), ("assets/evidence/EV-29C.png", "Fotogramma confronto") ]}
EVIDENCE_AUDIO = {}
EVIDENCE_BATES = {f"EV-{index:02d}": f"447-GN-{index:04d}" for index in range(1, 31)}
EVIDENCE_ATTACHMENTS = {
    "EV-03": [
        {
            "id": "BAL-447-GN-031-A",
            "type": "svg",
            "src": "assets/evidence/diagramma_balistico_EV03.svg",
            "title": "Schema tecnico della traiettoria balistica",
            "caption": "Ricostruzione tecnica della traiettoria dal punto di ingresso alla parete nord.",
        },
        {
            "id": "BAL-447-GN-031-B",
            "type": "image",
            "src": "(NEW) planimetria della Sala Blu.png",
            "title": "Localizzazione spaziale della scena",
            "caption": "Localizzazione della vittima, del punto d'impatto e degli accessi della Sala Blu.",
        },
    ]
}
MANUAL_EVIDENCE = {"EV-30"}


def validate_evidence_reachability() -> None:
    reachable = set(PUBLIC_EVIDENCE) | set(MANUAL_EVIDENCE)
    for evidence_ids in EVIDENCE_BY_WARRANT.values():
        reachable.update(evidence_ids)
    unreachable = set(EVIDENCE) - reachable
    unknown_unlocks = reachable - set(EVIDENCE)
    if unreachable:
        raise RuntimeError("Evidence non raggiungibili: " + ", ".join(sorted(unreachable)))
    if unknown_unlocks:
        raise RuntimeError("Sblocchi riferiti a evidence inesistenti: " + ", ".join(sorted(unknown_unlocks)))


validate_evidence_reachability()

ASSET_EVIDENCE_MAP = {
    "(NEW) EV-04.png": "EV-04",
    "(NEW) EV-05.png": "EV-05",
    "assets/evidence/EV-17.png": "EV-17",
    "assets/evidence/EV-21.png": "EV-21",
    "assets/evidence/EV-25A.png": "EV-25",
    "assets/evidence/EV-25B.png": "EV-25",
    "assets/evidence/EV-25C.png": "EV-25",
    "assets/evidence/EV-29A.png": "EV-29",
    "assets/evidence/EV-29B.png": "EV-29",
    "assets/evidence/EV-29C.png": "EV-29",
    "assets/evidence/diagramma_balistico_EV03.svg": "EV-03",
    "(NEW) planimetria della Sala Blu.png": "EV-03",
}


def approved_evidence_for_agent(badge: str) -> set[str]:
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT payload FROM mandates WHERE owner_badge=? AND status='APPROVED'",
            (badge,),
        ).fetchall()
    return {
        evidence_id
        for row in rows
        for evidence_id in EVIDENCE_BY_WARRANT.get(safe_json_loads(row["payload"], context="approved-evidence").get("target"), [])
    }


@app.get("/api/evidence")
def get_evidence():
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401
    allowed = set(EVIDENCE) if actor["role"] == "DIRECTOR" else PUBLIC_EVIDENCE | approved_evidence_for_agent(badge) | {evidence_id for evidence_id in MANUAL_EVIDENCE if manual_evidence_unlocked(evidence_id, badge)}
    return jsonify({"evidence": [{"id": evidence_id, "title": EVIDENCE[evidence_id][0], "details": EVIDENCE[evidence_id][1], "format": EVIDENCE_FORMATS.get(evidence_id, "standard"), "bates": EVIDENCE_BATES[evidence_id], "image": EVIDENCE_IMAGES.get(evidence_id), "images": [{"src": src, "caption": caption} for src, caption in EVIDENCE_GALLERIES.get(evidence_id, [])], "audio": EVIDENCE_AUDIO.get(evidence_id), "attachments": EVIDENCE_ATTACHMENTS.get(evidence_id, []), "releaseStage": "LATE_GAME" if evidence_id in MANUAL_EVIDENCE else "STANDARD"} for evidence_id in EVIDENCE if evidence_id in allowed], "summary": evidence_summary(badge, actor["role"] == "DIRECTOR")})


@app.get("/api/config")
def get_case_config():
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401
    return jsonify({
        "gameDurationSeconds": GAME_DURATION_SECONDS, "gameTimeScale": GAME_TIME_SCALE,
        "warrants": [
            {"id": target, "title": WARRANT_METADATA[target][0], "description": WARRANT_METADATA[target][1], "unlocks": evidence_ids, "requestKind": "WARRANT"}
            for target, evidence_ids in EVIDENCE_BY_WARRANT.items()
        ],
        "interviews": [
            {"id": target, "title": metadata["title"], "description": "Richiesta di autorizzazione all'interrogatorio.", "person": metadata["person"], "unlocks": [], "requestKind": "INTERVIEW"}
            for target, metadata in INTERVIEW_TARGETS.items()
        ],
    })


@app.get("/api/social")
def get_social():
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401
    if actor["role"] != "DIRECTOR" and not {"EV-04", "EV-08"} & approved_evidence_for_agent(badge):
        return jsonify({"error": "Accesso al profilo non autorizzato: serve un mandato approvato collegato a EV-04 o EV-08."}), 403
    return jsonify({
        "username": "matteo.rinaldi88",
        "bio": "Ingegnere · Genova · Lasciate ogne speranza",
        "caption": "Foto pubblicata il 2 ottobre 2026.",
        "image": "assets/social_mockup.svg",
    })


@app.get("/api/solution")
def get_solution():
    if session.get("role") != "DIRECTOR":
        return jsonify({"error": "Accesso riservato al Director."}), 403
    solution_path = BASE_DIR / "(NEW) soluzione Caso 447GN Mareggiata.txt"
    if not solution_path.is_file():
        return jsonify({"error": "Soluzione del caso non disponibile."}), 404
    return jsonify({"solution": solution_path.read_text(encoding="utf-8")})


@app.get("/api/interviews")
def get_interviews():
    if session.get("role") != "DIRECTOR":
        return jsonify({"error": "Accesso riservato al Director."}), 403
    source = BASE_DIR / "(NEW) FBI Dossier Interrogatori Completi.txt"
    if not source.is_file():
        return jsonify({"error": "Dossier interrogatori non disponibile."}), 404
    return jsonify({"interviews": source.read_text(encoding="utf-8")})


@app.get("/api/interviews/<path:name>")
def get_interview(name: str):
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401
    allowed_for_agents = {
        metadata["person"]: target for target, metadata in INTERVIEW_TARGETS.items()
    }
    if name not in allowed_for_agents:
        return jsonify({"error": "Verbale non trovato."}), 404
    if actor["role"] != "DIRECTOR":
        required_warrant = allowed_for_agents.get(name)
        if required_warrant not in {mandate.get("target") for mandate in serialize_mandates(badge) if mandate.get("status") == "APPROVED"}:
            return jsonify({"error": "Interrogatorio non ancora autorizzato."}), 403
    source = BASE_DIR / "(NEW) FBI Dossier Interrogatori Completi.txt"
    if not source.is_file():
        return jsonify({"error": "Dossier interrogatori non disponibile."}), 404
    content = source.read_text(encoding="utf-8")
    import re

    marker = re.compile(rf"^SOGGETTO:\s+{re.escape(name)}\s*$", re.MULTILINE)
    match = marker.search(content)
    if not match:
        return jsonify({"error": "Verbale non trovato."}), 404
    start = match.start()
    next_match = re.search(r"^SOGGETTO:\s+.+$", content[match.end():], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(content)
    return jsonify({"interview": content[start:end].split("POST-INTERROGATORIO")[0].strip()})


@app.post("/api/state")
def update_state():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action")
    badge = session.get("badge")
    actor = ACCOUNTS.get(badge)

    if not actor:
        return jsonify({"error": "Ruolo non riconosciuto."}), 401

    if actor["role"] == "DIRECTOR":
        logger.info("Director action=%s badge=%s", action, badge)

    with connect_db() as connection:
        if action not in {"reset", "start_case"}:
            start_error = require_started_case(connection)
            if start_error:
                return start_error
        if actor["role"] == "AGENT" and action in {"upsert", "add_note", "save_resolution"}:
            deadline_error = require_open_case(connection)
            if deadline_error:
                return deadline_error
        if action == "reset":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Game Master può azzerare il caso."}), 403
            connection.execute("DELETE FROM mandates")
            connection.execute("DELETE FROM case_resolutions")
            connection.execute("DELETE FROM manual_evidence_unlocks")
            connection.execute("DELETE FROM activity_log")
            connection.execute("DELETE FROM board_entries")
            connection.execute("DELETE FROM game_meta WHERE key='started_at'")
            current_version = game_version(connection)
            connection.execute(
                "INSERT INTO game_meta (key, value) VALUES ('version', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(current_version + 1),),
            )
        elif action == "start_case":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Ruolo non riconosciuto."}), 403
            connection.execute(
                "INSERT OR IGNORE INTO game_meta (key, value) VALUES ('started_at', ?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
        elif action == "upsert":
            mandate = payload.get("request") or {}
            mandate_id = mandate.get("id")
            if not mandate_id:
                return jsonify({"error": "Richiesta senza identificativo."}), 400
            owner_badge = mandate.get("ownerBadge") or badge
            if actor["role"] != "AGENT" or owner_badge != badge:
                return jsonify({"error": "Solo un agente può inviare una richiesta per sé."}), 403
            required_fields = {"id", "target", "name", "place", "reason"}
            if not isinstance(mandate, dict) or not required_fields.issubset(mandate.keys()):
                return jsonify({"error": "Payload della richiesta non valido."}), 400
            target = str(mandate.get("target", "")).strip()
            if target not in VALID_REQUEST_TARGETS:
                return jsonify({"error": "Fascicolo richiesto non valido."}), 400
            try:
                validate_payload_size(mandate)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            existing = connection.execute(
                "SELECT status, owner_badge FROM mandates WHERE id=?", (mandate_id,)
            ).fetchone()
            if existing:
                if existing["owner_badge"] != badge:
                    return jsonify({"error": "Richiesta non appartenente all'agente."}), 403
                if existing["status"] != "PENDING":
                    return jsonify({"error": "Una richiesta già valutata non è modificabile."}), 409
            else:
                pending = connection.execute(
                    "SELECT COUNT(*) AS count FROM mandates WHERE owner_badge=? AND status='PENDING'",
                    (badge,),
                ).fetchone()["count"]
                if pending >= MAX_PENDING_MANDATES:
                    return jsonify({"error": "Limite di tre richieste pendenti raggiunto."}), 409
            mandate["ownerBadge"] = badge
            mandate["requestKind"] = "INTERVIEW" if target in INTERVIEW_TARGETS else "WARRANT"
            mandate["status"] = "PENDING"
            connection.execute(
                """
                INSERT INTO mandates (id, payload, status, owner_badge)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET payload=excluded.payload,
                    owner_badge=excluded.owner_badge
                """,
                (mandate_id, json.dumps(mandate), "PENDING", badge),
            )

        elif action == "status":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Game Master può modificare lo stato."}), 403
            mandate_id = payload.get("id")
            status = payload.get("status")
            if status not in {"APPROVED", "REJECTED"}:
                return jsonify({"error": "Stato non valido."}), 400
            existing = connection.execute(
                "SELECT status FROM mandates WHERE id=?", (mandate_id,)
            ).fetchone()
            if not existing:
                return jsonify({"error": "Richiesta investigativa non trovata."}), 404
            if existing["status"] != "PENDING":
                return jsonify({"error": "La richiesta è già stata valutata."}), 409
            cursor = connection.execute(
                "UPDATE mandates SET status=? WHERE id=? AND status='PENDING'", (status, mandate_id)
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "Richiesta investigativa non trovata."}), 404
        elif action == "add_note":
            if actor["role"] != "AGENT":
                return jsonify({"error": "Solo un agente può pubblicare una nota."}), 403
            text = str(payload.get("text", "")).strip()
            if not text or len(text) > 500:
                return jsonify({"error": "Nota non valida."}), 400
            connection.execute(
                "INSERT INTO board_entries (kind, owner_badge, owner_name, text) VALUES ('note', ?, ?, ?)",
                (badge, actor["name"], text),
            )
        elif action == "publish_event":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Director può pubblicare un bollettino."}), 403
            text = str(payload.get("text", "")).strip()
            if not text or len(text) > 500:
                return jsonify({"error": "Bollettino non valido."}), 400
            connection.execute(
                "INSERT INTO board_entries (kind, owner_badge, owner_name, text) VALUES ('event', ?, ?, ?)",
                (badge, actor["name"], text),
            )
        elif action == "send_hint":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Director può inviare un hint."}), 403
            recipient = str(payload.get("recipientBadge", "")).strip()
            text = str(payload.get("text", "")).strip()
            if recipient not in ACCOUNTS or ACCOUNTS[recipient]["role"] != "AGENT" or not text or len(text) > 500:
                return jsonify({"error": "Hint non valido."}), 400
            connection.execute(
                "INSERT INTO board_entries (kind, owner_badge, owner_name, text) VALUES ('hint', ?, ?, ?)",
                (recipient, actor["name"], text),
            )
        elif action == "release_evidence":
            if actor["role"] != "DIRECTOR":
                return jsonify({"error": "Solo il Director può rilasciare evidence manuali."}), 403
            evidence_id = str(payload.get("evidenceId", "")).strip()
            recipient = str(payload.get("recipientBadge", "TEAM")).strip()
            if evidence_id not in MANUAL_EVIDENCE or recipient != "TEAM":
                return jsonify({"error": "Rilascio evidence non valido."}), 400
            connection.execute(
                "INSERT OR IGNORE INTO manual_evidence_unlocks (evidence_id, unlocked_by, team_wide) VALUES (?, ?, 1)",
                (evidence_id, badge),
            )
        elif action == "save_resolution":
            if actor["role"] != "AGENT":
                return jsonify({"error": "Solo un agente può salvare una risoluzione."}), 403
            resolution = payload.get("resolution") or {}
            required_fields = {"suspect", "motive", "evidence", "cleared", "custody", "custodyDetails"}
            if not isinstance(resolution, dict) or not required_fields.issubset(resolution):
                return jsonify({"error": "Risoluzione non valida."}), 400
            requested_status = str(resolution.get("status", "DRAFT")).upper()
            if requested_status not in {"DRAFT", "SUBMITTED"}:
                return jsonify({"error": "Stato della risoluzione non valido."}), 400
            previous = connection.execute("SELECT status FROM case_resolutions WHERE owner_badge=?", (badge,)).fetchone()
            if previous and previous["status"] == "SUBMITTED":
                return jsonify({"error": "La risoluzione è già stata consegnata."}), 409
            text_fields = {"suspect", "motive", "evidence", "cleared", "custodyDetails"}
            if requested_status == "SUBMITTED" and (not all(str(resolution.get(field, "")).strip() for field in text_fields) or not resolution.get("custody")):
                return jsonify({"error": "Risoluzione incompleta."}), 400
            resolution["status"] = requested_status
            try:
                validate_payload_size(resolution, 8_192)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            connection.execute(
                "INSERT INTO case_resolutions (owner_badge, payload, status) VALUES (?, ?, ?) ON CONFLICT(owner_badge) DO UPDATE SET payload=excluded.payload, status=excluded.status, updated_at=CURRENT_TIMESTAMP",
                (badge, json.dumps(resolution, ensure_ascii=False), requested_status),
            )
        else:
            return jsonify({"error": "Azione non valida."}), 400
        connection.commit()

    with connect_db() as state_connection:
        version = game_version(state_connection)
        started_at = game_started_at(state_connection)
    notes, events = serialize_board()
    is_director = ACCOUNTS[session["badge"]]["role"] == "DIRECTOR"
    return jsonify({"requests": serialize_mandates() if is_director else serialize_mandates(session["badge"]), "notes": notes, "events": events, "hints": serialize_hints(session.get("badge")), "resolution": serialize_resolution(session["badge"]), "resolutions": serialize_resolutions() if is_director else [], "manualEvidence": serialize_manual_unlocks() if is_director else [item for item in serialize_manual_unlocks() if item["team_wide"] or item["unlocked_by"] == session["badge"]], "gameVersion": version, "gameStartedAt": started_at, "gameDurationSeconds": GAME_DURATION_SECONDS, "gameTimeScale": GAME_TIME_SCALE, "evidenceSummary": evidence_summary(session["badge"], is_director), "agentEvidenceSummary": agent_evidence_summaries() if is_director else {}})


@app.get("/<path:filename>")
def static_files(filename: str):
    public_files = {
        "index.html", "client-fixes.js", "manifest.json",
        "icon-192.svg", "icon-512.svg", "approved.mp3", "rejected.mp3",
        "click.mp3", "notify.mp3",
    }
    if filename == "dossier_447_gn_player.html":
        if not ACCOUNTS.get(session.get("badge")):
            return jsonify({"error": "Sessione non autenticata."}), 401
        return send_from_directory(BASE_DIR, filename)
    if filename == "(NEW) Dossier operazione mareggiata.pdf":
        if not ACCOUNTS.get(session.get("badge")):
            return jsonify({"error": "Sessione non autenticata."}), 401
        return send_from_directory(BASE_DIR, filename)
    if filename == "assets/social_mockup.svg":
        if not ACCOUNTS.get(session.get("badge")):
            return jsonify({"error": "Sessione non autenticata."}), 401
        return send_from_directory(BASE_DIR, filename)
    if filename in public_files:
        return send_from_directory(BASE_DIR, filename)
    evidence_id = ASSET_EVIDENCE_MAP.get(filename)
    actor = ACCOUNTS.get(session.get("badge"))
    if not evidence_id:
        logger.warning("Blocked static file request path=%s badge=%s", filename, session.get("badge", "anonymous"))
        return jsonify({"error": "Risorsa non disponibile."}), 404
    if not actor:
        return jsonify({"error": "Sessione non autenticata."}), 401
    if actor["role"] != "DIRECTOR" and evidence_id not in PUBLIC_EVIDENCE | approved_evidence_for_agent(session["badge"]) | {item for item in MANUAL_EVIDENCE if manual_evidence_unlocked(item, session["badge"])}:
        return jsonify({"error": "Evidence non autorizzata."}), 403
    return send_from_directory(BASE_DIR, filename)


initialize_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5055")), debug=False)
