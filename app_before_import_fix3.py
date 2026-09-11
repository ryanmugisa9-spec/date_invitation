from functools import wraps
import os

from flask import Flask, render_template, request, session, redirect, url_for

from invitation_db import (
    initialize_database,
    create_invitation,
    get_invitation,
    save_answers,
    complete_invitation
)


app = Flask(__name__)

app.secret_key = "living-invitation-secret-key"

initialize_database()


def require_invitation(view_function):
    @wraps(view_function)
    def protected_page(*args, **kwargs):
        token = session.get("invitation_token")

        if not token:
            return (
                "This invitation can only be opened using a valid invitation link.",
                403
            )

        invitation_data = get_invitation(token)

        if invitation_data is None:
            session.clear()
            return "This invitation does not exist.", 404

        if invitation_data["completed"]:
            return render_template("confirmation.html")

        return view_function(*args, **kwargs)

    return protected_page


@app.route("/")
@require_invitation
def welcome():
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
    place = request.args.get("place", "")
    date_value = request.args.get("date", "")

    session["place"] = place
    session["date"] = date_value

    return render_template(
        "menu.html",
        place=place,
        date=date_value
    )


@app.route("/transport")
@require_invitation
def transport():
    meals = request.args.getlist("meal")
    desserts = request.args.getlist("dessert")
    drinks = request.args.getlist("drink")

    session["meals"] = meals
    session["desserts"] = desserts
    session["drinks"] = drinks

    return render_template(
        "transport.html",
        place=session.get("place", ""),
        date=session.get("date", ""),
        meals=meals,
        desserts=desserts,
        drinks=drinks
    )


@app.route("/thank-you")
@require_invitation
def thank_you():
    transport_amount = request.args.get("transport", "")

    session["transport"] = transport_amount

    return render_template(
        "thank_you.html",
        place=session.get("place", ""),
        date=session.get("date", ""),
        meals=session.get("meals", []),
        desserts=session.get("desserts", []),
        drinks=session.get("drinks", []),
        transport=transport_amount
    )


@app.route("/confirmation")
@require_invitation
def confirmation():
    token = session.get("invitation_token")

    place = session.get("place", "")
    date_value = session.get("date", "")
    meals = session.get("meals", [])
    desserts = session.get("desserts", [])
    drinks = session.get("drinks", [])
    transport = session.get("transport", "")

    save_answers(
        token,
        place,
        date_value,
        ", ".join(meals),
        ", ".join(desserts),
        ", ".join(drinks),
        transport
    )

    complete_invitation(token)

    return render_template(
        "confirmation.html",
        place=place,
        date=date_value,
        meals=meals,
        desserts=desserts,
        drinks=drinks,
        transport=transport
    )


@app.route("/results")
def results():
    auth = request.authorization
    admin_password = os.environ.get("RESULTS_PASSWORD")

    if (
        not admin_password
        or not auth
        or auth.username != "admin"
        or auth.password != admin_password
    ):
        return (
            "Private results. Authentication required.",
            401,
            {
                "WWW-Authenticate": 'Basic realm="Private Results"'
            }
        )

    invitations = get_completed_invitations()

    return render_template(
        "results.html",
        invitations=invitations
    )


@app.route("/create-invitation")
def create_invitation_link():
    token = create_invitation()

    invitation_url = url_for(
        "invitation",
        token=token,
        _external=True
    )

    return (
        "Invitation created successfully.<br><br>"
        f"Your invitation token is:<br>{token}<br><br>"
        f"Open this link:<br>"
        f"<a href='{invitation_url}'>{invitation_url}</a>"
    )


@app.route("/i/<token>")
def invitation(token):
    invitation_data = get_invitation(token)

    if invitation_data is None:
        return "This invitation does not exist.", 404

    if invitation_data["completed"]:
        return render_template("confirmation.html")

    session.clear()
    session["invitation_token"] = token

    return redirect(url_for("welcome"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
