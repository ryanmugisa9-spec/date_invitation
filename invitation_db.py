
import os
import sqlite3
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SQLITE_DATABASE = BASE_DIR / "invitations.db"


def using_postgres():
    return bool(os.environ.get("DATABASE_URL"))


def get_sqlite_connection():
    connection = sqlite3.connect(SQLITE_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def get_postgres_connection():
    import psycopg
    from psycopg.rows import dict_row

    database_url = os.environ["DATABASE_URL"]

    return psycopg.connect(
        database_url,
        row_factory=dict_row
    )


def get_connection():
    if using_postgres():
        return get_postgres_connection()

    return get_sqlite_connection()


def initialize_database():
    if using_postgres():
        connection = get_connection()

        connection.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                token TEXT UNIQUE NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT FALSE,
                place TEXT,
                date TEXT,
                meals TEXT,
                desserts TEXT,
                drinks TEXT,
                transport TEXT,
                completed_at TIMESTAMP
            )
        """)

        connection.commit()
        connection.close()
        return

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

        if using_postgres():
            existing = connection.execute(
                "SELECT id FROM invitations WHERE token = %s",
                (token,)
            ).fetchone()
        else:
            existing = connection.execute(
                "SELECT id FROM invitations WHERE token = ?",
                (token,)
            ).fetchone()

        if existing is None:
            break

    if using_postgres():
        connection.execute(
            "INSERT INTO invitations (token) VALUES (%s)",
            (token,)
        )
    else:
        connection.execute(
            "INSERT INTO invitations (token) VALUES (?)",
            (token,)
        )

    connection.commit()
    connection.close()

    return token


def get_invitation(token):
    connection = get_connection()

    if using_postgres():
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
            WHERE token = %s
            """,
            (token,)
        ).fetchone()
    else:
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

    if using_postgres():
        connection.execute(
            """
            UPDATE invitations
            SET
                place = %s,
                date = %s,
                meals = %s,
                desserts = %s,
                drinks = %s,
                transport = %s
            WHERE token = %s
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
    else:
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

    if using_postgres():
        connection.execute(
            """
            UPDATE invitations
            SET
                completed = TRUE,
                completed_at = %s
            WHERE token = %s
            """,
            (
                datetime.now(),
                token
            )
        )
    else:
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

    connection.execute("""
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
        WHERE completed = TRUE
        ORDER BY completed_at DESC
    """) if using_postgres() else None

    if using_postgres():
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
            WHERE completed = TRUE
            ORDER BY completed_at DESC
            """
        ).fetchall()
    else:
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
