from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import sqlite3
import openpyxl
from io import BytesIO
import random

app = Flask(__name__)
app.secret_key = 'vanes_secret_key'

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS enquiry_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT,
        enquiry_type TEXT,
        contractor_type TEXT
    )''')

    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    conn.commit()
    conn.close()

# ---------- Auth ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (uname, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = uname
            flash("Login successful", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out", "info")
    return redirect(url_for('login'))

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    modules = [
        {"name": "Management", "url": "/management"},
        {"name": "Accounts", "url": "/accounts"},
        {"name": "Project", "url": "/project"},
        {"name": "Production", "url": "/production"},
        {"name": "Sales / Design", "url": "/sales"},
        {"name": "Customer", "url": "/customer"}
    ]
    return render_template("dashboard.html", modules=modules)

# ---------- Management ----------
@app.route('/management')
def management():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("management.html")

# ---------- Sales: New Enquiry ----------
@app.route('/new-enquiry')
def new_enquiry_page():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Auto generate enquiry_id
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM enquiries")
    count = c.fetchone()[0] + 1
    enquiry_id = f"TEI/Enquiry/{count:03}"
    c.execute("INSERT INTO enquiries (enquiry_id) VALUES (?)", (enquiry_id,))
    conn.commit()
    conn.close()

    return render_template('new_enquiry.html', enquiry_id=enquiry_id)

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    if 'username' not in session:
        return redirect(url_for('login'))

    enquiry_id = request.form.get("enquiry_id")
    enquiry_type = request.form.get("enquiry_type")
    contractor_type = request.form.get("contractor_type")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO enquiry_details (enquiry_id, enquiry_type, contractor_type)
                 VALUES (?, ?, ?)''', (enquiry_id, enquiry_type, contractor_type))
    conn.commit()
    conn.close()
    return jsonify({"message": "Enquiry submitted successfully!"})

# ---------- Sales: Progress / Award ----------
@app.route('/progress-award')
def progress_award():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT enquiry_id, enquiry_type, contractor_type FROM enquiry_details")
    enquiries = c.fetchall()
    conn.close()
    return render_template("progress_award.html", enquiries=enquiries)

# ---------- Other Modules ----------
@app.route('/accounts')
def accounts():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("accounts.html")

@app.route('/project')
def project():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("project.html")

@app.route('/production')
def production():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("production.html")

@app.route('/sales')
def sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("sales.html")

@app.route('/customer')
def customer():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("customer.html")

# ---------- Run ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
