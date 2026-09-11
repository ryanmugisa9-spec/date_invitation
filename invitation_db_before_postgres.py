import sqlite3
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "invitations.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            place TEXT,
            date TEXT,
            meals TEXT,
            desserts TEXT,
            drinks TEXT,
            transport TEXT,
            completed_at TEXT
        )
    """)

    connection.commit()
    connection.close()


def create_invitation():
    connection = get_connection()

    while True:
        token = secrets.token_urlsafe(16)

        existing = connection.execute(
            "SELECT id FROM invitations WHERE token = ?",
            (token,)
        ).fetchone()

        if existing is None:
            break

    connection.execute(
        "INSERT INTO invitations (token) VALUES (?)",
        (token,)
    )

    connection.commit()
    connection.close()

    return token


def get_invitation(token):
    connection = get_connection()

    invitation = connection.execute(
        """
        SELECT
            id,
            token,
            completed,
            place,
            date,
            meals,
            desserts,
            drinks,
            transport,
            completed_at
        FROM invitations
        WHERE token = ?
        """,
        (token,)
    ).fetchone()

    connection.close()

    return invitation


def save_answers(
    token,
    place,
    date,
    meals,
    desserts,
    drinks,
    transport
):
    connection = get_connection()

    connection.execute(
        """
        UPDATE invitations
        SET
            place = ?,
            date = ?,
            meals = ?,
            desserts = ?,
            drinks = ?,
            transport = ?
        WHERE token = ?
        """,
        (
            place,
            date,
            meals,
            desserts,
            drinks,
            transport,
            token
        )
    )

    connection.commit()
    connection.close()


def complete_invitation(token):
    from datetime import datetime

    connection = get_connection()

    connection.execute(
        """
        UPDATE invitations
        SET
            completed = 1,
            completed_at = ?
        WHERE token = ?
        """,
        (
            datetime.now().isoformat(timespec="seconds"),
            token
        )
    )

    connection.commit()
    connection.close()
def get_completed_invitations():
    connection = get_connection()

    invitations = connection.execute(
        """
        SELECT
            id,
            token,
            place,
            date,
            meals,
            desserts,
            drinks,
            transport,
            completed_at
        FROM invitations
        WHERE completed = 1
        ORDER BY completed_at DESC
        """
    ).fetchall()

    connection.close()

    return invitations
