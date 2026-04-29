#!/usr/bin/env python3
"""
SICE Monitor — Alertas automáticas de licitaciones del rubro cerramientos
en compras estatales de Uruguay.

Consulta el RSS de comprasestatales.gub.uy, filtra por keywords del rubro,
y envía email a ventas@arcosuy.com cuando aparecen licitaciones nuevas.
"""

import feedparser
import json
import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

KEYWORDS = [
    "cerramiento",
    "cerco perimetral",
    "tejido perimetral",
    "alambrado olímpico",
    "muro premoldeado",
    "cerco modular",
    "alambrado romboidal",
    "vallado",
    "tejido romboidal",
    "malla electrosoldada",
    "perimetral",
    "cerco olímpico",
    "columnas",
    "muros",
    "cerca perimetral",
    "tatami",  # TEMPORAL — solo para test de validación SMTP. REVERTIR después del test.
]

EMAIL_TO = "ventas@arcosuy.com"

NOTIFIED_FILE = Path(__file__).parent / "notified.json"

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))


def get_rss_url() -> str:
    """RSS de cambios de hoy en SICE.

    TEMPORAL: ampliado a últimos 7 días para test de validación SMTP.
    REVERTIR a solo el día actual después del test.
    """
    from datetime import timedelta
    today = date.today()
    seven_days_ago = today - timedelta(days=7)
    return (
        f"https://www.comprasestatales.gub.uy/consultas/rss/"
        f"tipo-pub/ALL/tipo-fecha/MOD/orden/ORD_MOD/tipo-orden/DESC/"
        f"rango-fecha/{seven_days_ago.isoformat()}+00%3A00%3A00_{today.isoformat()}+23%3A59%3A59"
    )


# ============================================================
# LÓGICA
# ============================================================

def load_notified() -> set:
    if NOTIFIED_FILE.exists():
        return set(json.loads(NOTIFIED_FILE.read_text(encoding="utf-8")))
    return set()


def save_notified(notified: set) -> None:
    NOTIFIED_FILE.write_text(
        json.dumps(sorted(notified), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def matches_keywords(text: str) -> list:
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw.lower() in text_lower]


def fetch_feed():
    url = get_rss_url()
    print(f"Fetching: {url}", file=sys.stderr)
    feed = feedparser.parse(url)
    if feed.bozo:
        print(f"Warning: feed parse error: {feed.bozo_exception}", file=sys.stderr)
    print(f"Total entries in feed: {len(feed.entries)}", file=sys.stderr)
    return feed.entries


def find_new_matches(entries, notified: set) -> list:
    matches = []
    for entry in entries:
        entry_id = entry.get("id") or entry.link
        if entry_id in notified:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        text = f"{title} {summary}"

        matched_kws = matches_keywords(text)
        if matched_kws:
            matches.append({
                "id": entry_id,
                "title": title,
                "link": entry.link,
                "matched_keywords": matched_kws,
                "published": entry.get("published", ""),
                "summary": summary[:600],
            })
    return matches


def build_email_body(matches: list) -> str:
    today = date.today().isoformat()
    parts = [
        f"<h2>SICE — {len(matches)} nueva(s) licitación(es) detectada(s) — {today}</h2>",
        "<p>El monitor automático encontró las siguientes licitaciones que matchean keywords del rubro de cerramientos.</p>",
    ]
    for m in matches:
        parts.append("<hr>")
        parts.append(f"<h3>{m['title']}</h3>")
        parts.append(
            f"<p><b>Keywords coincidentes:</b> {', '.join(m['matched_keywords'])}</p>"
        )
        if m["published"]:
            parts.append(f"<p><b>Publicado:</b> {m['published']}</p>")
        if m["summary"]:
            parts.append(f"<p><b>Resumen:</b> {m['summary']}</p>")
        parts.append(
            f'<p><a href="{m["link"]}">Ver pliego completo en SICE →</a></p>'
        )
    return "\n".join(parts)


def send_email(subject: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASSWORD environment variables are required"
        )

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def main() -> int:
    notified = load_notified()
    entries = fetch_feed()
    new_matches = find_new_matches(entries, notified)

    if not new_matches:
        print("No new matches.", file=sys.stderr)
        return 0

    today = date.today().isoformat()
    subject = f"SICE Alert: {len(new_matches)} licitación(es) — {today}"
    body = build_email_body(new_matches)

    send_email(subject, body)
    print(f"Sent alert for {len(new_matches)} new matches.", file=sys.stderr)

    for m in new_matches:
        notified.add(m["id"])
    save_notified(notified)

    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
SICE Monitor — Alertas automáticas de licitaciones del rubro cerramientos
en compras estatales de Uruguay.

Consulta el RSS de comprasestatales.gub.uy, filtra por keywords del rubro,
y envía email a ventas@arcosuy.com cuando aparecen licitaciones nuevas.
"""

import feedparser
import json
import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

KEYWORDS = [
    "cerramiento",
    "cerco perimetral",
    "tejido perimetral",
    "alambrado olímpico",
    "muro premoldeado",
    "cerco modular",
    "alambrado romboidal",
    "vallado",
    "tejido romboidal",
    "malla electrosoldada",
    "perimetral",
    "cerco olímpico",
    "columnas",
    "muros",
    "cerca perimetral",
]

EMAIL_TO = "ventas@arcosuy.com"

NOTIFIED_FILE = Path(__file__).parent / "notified.json"

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))


def get_rss_url() -> str:
    """RSS de cambios de hoy en SICE."""
    today = date.today().isoformat()
    return (
        f"https://www.comprasestatales.gub.uy/consultas/rss/"
        f"tipo-pub/ALL/tipo-fecha/MOD/orden/ORD_MOD/tipo-orden/DESC/"
        f"rango-fecha/{today}+00%3A00%3A00_{today}+23%3A59%3A59"
    )


# ============================================================
# LÓGICA
# ============================================================

def load_notified() -> set:
    if NOTIFIED_FILE.exists():
        return set(json.loads(NOTIFIED_FILE.read_text(encoding="utf-8")))
    return set()


def save_notified(notified: set) -> None:
    NOTIFIED_FILE.write_text(
        json.dumps(sorted(notified), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def matches_keywords(text: str) -> list:
    text_lower = text.lower()
    return [kw for kw in KEYWORDS if kw.lower() in text_lower]


def fetch_feed():
    url = get_rss_url()
    print(f"Fetching: {url}", file=sys.stderr)
    feed = feedparser.parse(url)
    if feed.bozo:
        print(f"Warning: feed parse error: {feed.bozo_exception}", file=sys.stderr)
    print(f"Total entries in feed: {len(feed.entries)}", file=sys.stderr)
    return feed.entries


def find_new_matches(entries, notified: set) -> list:
    matches = []
    for entry in entries:
        entry_id = entry.get("id") or entry.link
        if entry_id in notified:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "") or entry.get("description", "")
        text = f"{title} {summary}"

        matched_kws = matches_keywords(text)
        if matched_kws:
            matches.append({
                "id": entry_id,
                "title": title,
                "link": entry.link,
                "matched_keywords": matched_kws,
                "published": entry.get("published", ""),
                "summary": summary[:600],
            })
    return matches


def build_email_body(matches: list) -> str:
    today = date.today().isoformat()
    parts = [
        f"<h2>SICE — {len(matches)} nueva(s) licitación(es) detectada(s) — {today}</h2>",
        "<p>El monitor automático encontró las siguientes licitaciones que matchean keywords del rubro de cerramientos.</p>",
    ]
    for m in matches:
        parts.append("<hr>")
        parts.append(f"<h3>{m['title']}</h3>")
        parts.append(
            f"<p><b>Keywords coincidentes:</b> {', '.join(m['matched_keywords'])}</p>"
        )
        if m["published"]:
            parts.append(f"<p><b>Publicado:</b> {m['published']}</p>")
        if m["summary"]:
            parts.append(f"<p><b>Resumen:</b> {m['summary']}</p>")
        parts.append(
            f'<p><a href="{m["link"]}">Ver pliego completo en SICE →</a></p>'
        )
    return "\n".join(parts)


def send_email(subject: str, body: str) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASSWORD environment variables are required"
        )

    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def main() -> int:
    notified = load_notified()
    entries = fetch_feed()
    new_matches = find_new_matches(entries, notified)

    if not new_matches:
        print("No new matches.", file=sys.stderr)
        return 0

    today = date.today().isoformat()
    subject = f"SICE Alert: {len(new_matches)} licitación(es) — {today}"
    body = build_email_body(new_matches)

    send_email(subject, body)
    print(f"Sent alert for {len(new_matches)} new matches.", file=sys.stderr)

    for m in new_matches:
        notified.add(m["id"])
    save_notified(notified)

    return 0


if __name__ == "__main__":
    sys.exit(main())
