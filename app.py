import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('responses.db')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    if DATABASE_URL:
        cur.execute("CREATE TABLE IF NOT EXISTS responses (id SERIAL PRIMARY KEY, name TEXT, date_choice TEXT, food TEXT, transport TEXT, created_at TIMESTAMP DEFAULT NOW())")
    else:
        cur.execute("CREATE TABLE IF NOT EXISTS responses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, date_choice TEXT, food TEXT, transport TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def welcome(): return render_template('welcome.html')
@app.route('/date')
def date_page(): return render_template('date.html')
@app.route('/menu')
def menu_page(): return render_template('menu.html')
@app.route('/transport')
def transport_page(): return render_template('transport.html')
@app.route('/confirmation')
def confirmation(): return render_template('confirmation.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        if DATABASE_URL:
            cur.execute("INSERT INTO responses (name, date_choice, food, transport) VALUES (%s, %s, %s, %s)", (data.get('name'), data.get('date'), data.get('food'), data.get('transport')))
        else:
            cur.execute("INSERT INTO responses (name, date_choice, food, transport) VALUES (?, ?, ?, ?)", (data.get('name'), data.get('date'), data.get('food'), data.get('transport')))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        print("DB Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__': app.run(debug=True)
