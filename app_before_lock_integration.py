from flask import Flask, render_template, request, session

app = Flask(__name__)

app.secret_key = "living-invitation-secret-key"


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/question")
def question():
    return render_template("question.html")


@app.route("/date")
def date():
    return render_template("date.html")


@app.route("/menu")
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
def confirmation():
    return render_template(
        "confirmation.html",
        place=session.get("place", ""),
        date=session.get("date", ""),
        meals=session.get("meals", []),
        desserts=session.get("desserts", []),
        drinks=session.get("drinks", []),
        transport=session.get("transport", "")
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
