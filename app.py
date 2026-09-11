import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, abort


app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-only-secret"
)

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "invitations.db"
)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

def using_postgres():
    return bool(DATABASE_URL)


def get_db():
    if using_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor

        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )

    connection = sqlite3.connect(SQLITE_DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()

    cursor = connection.cursor()

    if using_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                id SERIAL PRIMARY KEY,
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
    else:
        cursor.execute("""
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
    cursor.close()
    connection.close()


init_db()


# ---------------------------------------------------------
# INVITATION DATABASE FUNCTIONS
# ---------------------------------------------------------

def create_invitation():
    token = secrets.token_urlsafe(16)

    connection = get_db()
    cursor = connection.cursor()

    if using_postgres():
        cursor.execute(
            "INSERT INTO invitations (token) VALUES (%s)",
            (token,)
        )
    else:
        cursor.execute(
            "INSERT INTO invitations (token) VALUES (?)",
            (token,)
        )

    connection.commit()
    cursor.close()
    connection.close()

    return token


def get_invitation(token):
    connection = get_db()
    cursor = connection.cursor()

    if using_postgres():
        cursor.execute("""
            SELECT id, token, completed, place, date,
                   meals, desserts, drinks, transport, completed_at
            FROM invitations
            WHERE token = %s
        """, (token,))
    else:
        cursor.execute("""
            SELECT id, token, completed, place, date,
                   meals, desserts, drinks, transport, completed_at
            FROM invitations
            WHERE token = ?
        """, (token,))

    invitation = cursor.fetchone()

    cursor.close()
    connection.close()

    return invitation


def save_answers(
    token,
    place,
    date_value,
    meals,
    desserts,
    drinks,
    transport
):
    connection = get_db()
    cursor = connection.cursor()

    if using_postgres():
        cursor.execute("""
            UPDATE invitations
            SET place = %s,
                date = %s,
                meals = %s,
                desserts = %s,
                drinks = %s,
                transport = %s
            WHERE token = %s
        """, (
            place,
            date_value,
            meals,
            desserts,
            drinks,
            transport,
            token
        ))
    else:
        cursor.execute("""
            UPDATE invitations
            SET place = ?,
                date = ?,
                meals = ?,
                desserts = ?,
                drinks = ?,
                transport = ?
            WHERE token = ?
        """, (
            place,
            date_value,
            meals,
            desserts,
            drinks,
            transport,
            token
        ))

    connection.commit()
    cursor.close()
    connection.close()


def complete_invitation(token):
    connection = get_db()
    cursor = connection.cursor()

    completed_at = datetime.now()

    if using_postgres():
        cursor.execute("""
            UPDATE invitations
            SET completed = TRUE,
                completed_at = %s
            WHERE token = %s
            AND completed = FALSE
        """, (completed_at, token))
    else:
        cursor.execute("""
            UPDATE invitations
            SET completed = 1,
                completed_at = ?
            WHERE token = ?
            AND completed = 0
        """, (
            completed_at.isoformat(timespec="seconds"),
            token
        ))

    connection.commit()
    cursor.close()
    connection.close()


def get_completed_invitations():
    connection = get_db()
    cursor = connection.cursor()

    if using_postgres():
        cursor.execute("""
            SELECT id, token, place, date,
                   meals, desserts, drinks,
                   transport, completed_at
            FROM invitations
            WHERE completed = TRUE
            ORDER BY completed_at DESC
        """)
    else:
        cursor.execute("""
            SELECT id, token, place, date,
                   meals, desserts, drinks,
                   transport, completed_at
            FROM invitations
            WHERE completed = 1
            ORDER BY completed_at DESC
        """)

    invitations = cursor.fetchall()

    cursor.close()
    connection.close()

    return invitations


# ---------------------------------------------------------
# INVITATION ACCESS CONTROL
# ---------------------------------------------------------

def require_invitation(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        token = session.get("invitation_token")

        if not token:
            abort(404)

        invitation = get_invitation(token)

        if invitation is None:
            session.clear()
            abort(404)

        if invitation["completed"]:
            return render_template(
                "confirmation.html"
            )

        return function(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------
# START INVITATION
# ---------------------------------------------------------

@app.route("/i/<token>")
def invitation(token):
    invitation_data = get_invitation(token)

    if invitation_data is None:
        abort(404)

    if invitation_data["completed"]:
        return render_template("confirmation.html")

    session.clear()

    session["invitation_token"] = token

    return redirect(url_for("welcome"))


# ---------------------------------------------------------
# INVITATION PAGES
# ---------------------------------------------------------

@app.route("/")
def welcome():
    if not session.get("invitation_token"):
        abort(404)

    invitation_data = get_invitation(
        session["invitation_token"]
    )

    if invitation_data is None:
        session.clear()
        abort(404)

    if invitation_data["completed"]:
        return render_template("confirmation.html")

    return render_template("welcome.html")


@app.route("/question")
@require_invitation
def question():
    return render_template("question.html")


@app.route("/date")
@require_invitation
def date():
    return render_template("date.html")


@app.route("/menu")
@require_invitation
def menu():
    place = request.args.get("place", "").strip()
    date_value = request.args.get("date", "").strip()

    if not place or not date_value:
        return redirect(url_for("date"))

    session["place"] = place
    session["date"] = date_value

    return render_template("menu.html")


@app.route("/transport")
@require_invitation
def transport():
    meals = request.args.getlist("meal")
    desserts = request.args.getlist("dessert")
    drinks = request.args.getlist("drink")

    if len(meals) != 3:
        return redirect(
            url_for(
                "menu",
                place=session.get("place", ""),
                date=session.get("date", "")
            )
        )

    if len(desserts) != 2:
        return redirect(
            url_for(
                "menu",
                place=session.get("place", ""),
                date=session.get("date", "")
            )
        )

    if len(drinks) != 2 or "Water" not in drinks:
        return redirect(
            url_for(
                "menu",
                place=session.get("place", ""),
                date=session.get("date", "")
            )
        )

    session["meals"] = meals
    session["desserts"] = desserts
    session["drinks"] = drinks

    return render_template("transport.html")


@app.route("/thank-you")
@require_invitation
def thank_you():
    transport_amount = request.args.get(
        "transport",
        ""
    ).strip()

    if not transport_amount:
        return redirect(url_for("transport"))

    session["transport"] = transport_amount

    return render_template("thank_you.html")


@app.route("/confirmation")
def confirmation():
    token = session.get("invitation_token")

    if not token:
        abort(404)

    invitation_data = get_invitation(token)

    if invitation_data is None:
        session.clear()
        abort(404)

    if invitation_data["completed"]:
        return render_template("confirmation.html")

    place = session.get("place", "")
    date_value = session.get("date", "")
    meals = session.get("meals", [])
    desserts = session.get("desserts", [])
    drinks = session.get("drinks", [])
    transport_amount = session.get("transport", "")

    if (
        not place
        or not date_value
        or len(meals) != 3
        or len(desserts) != 2
        or len(drinks) != 2
        or "Water" not in drinks
        or not transport_amount
    ):
        abort(400)

    save_answers(
        token,
        place,
        date_value,
        ", ".join(meals),
        ", ".join(desserts),
        ", ".join(drinks),
        transport_amount
    )

    complete_invitation(token)

    return render_template(
        "confirmation.html",
        place=place,
        date=date_value,
        meals=meals,
        desserts=desserts,
        drinks=drinks,
        transport=transport_amount
    )


# ---------------------------------------------------------
# PRIVATE RESULTS
# ---------------------------------------------------------

@app.route("/results", methods=["GET", "POST"])
def results():
    admin_password = os.environ.get("RESULTS_PASSWORD")

    if request.method == "POST":
        password = request.form.get(
            "password",
            ""
        )

        if (
            admin_password
            and password == admin_password
        ):
            session["results_authenticated"] = True
            return redirect(url_for("results"))

        return render_template(
            "results.html",
            authenticated=False,
            error="Incorrect password."
        ), 401

    if not session.get("results_authenticated"):
        return render_template(
            "results.html",
            authenticated=False
        )

    invitations = get_completed_invitations()

    return render_template(
        "results.html",
        invitations=invitations,
        authenticated=True
    )


@app.route("/results/logout")
def results_logout():
    session.pop(
        "results_authenticated",
        None
    )

    return redirect(url_for("results"))


# ---------------------------------------------------------
# CREATE NEW INVITATION
# ---------------------------------------------------------

@app.route("/create-invitation")
def create_invitation_link():
    if not session.get("results_authenticated"):
        return (
            "Private invitation generator. "
            "Authentication required."
        ), 403

    token = create_invitation()

    invitation_url = url_for(
        "invitation",
        token=token,
        _external=True
    )

    return render_template(
        "new_invitation.html",
        invitation_url=invitation_url
    )


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
