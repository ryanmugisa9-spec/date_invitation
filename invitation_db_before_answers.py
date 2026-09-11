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
            completed INTEGER NOT NULL DEFAULT 0
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
        "SELECT id, token, completed FROM invitations WHERE token = ?",
        (token,)
    ).fetchone()

    connection.close()

    return invitation


def complete_invitation(token):
    connection = get_connection()

    connection.execute(
        """
        UPDATE invitations
        SET completed = 1
        WHERE token = ?
        """,
        (token,)
    )

    connection.commit()
    connection.close()
