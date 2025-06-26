from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import sqlite3
import openpyxl
from io import BytesIO
import random

app = Flask(__name__)
app.secret_key = 'vanes_secret_key'

# ---------- DB Initialization ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Create necessary tables
    c.execute('''CREATE TABLE IF NOT EXISTS enquiry_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT,
        enquiry_type TEXT,
        contractor_type TEXT,
        client_name TEXT,
        project_title TEXT,
        status TEXT DEFAULT 'In Progress'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')

    # Insert default admin user if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    conn.commit()
    conn.close()

# ---------- Routes ----------
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
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

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
    return render_template('dashboard.html', modules=modules)

@app.route('/management')
def management():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('management.html')

@app.route('/sales')
def sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('sales.html')

# ---------- New Enquiry ----------
@app.route('/get_enquiry_id')
def get_enquiry_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM enquiry_details")
    count = c.fetchone()[0] + 1
    enquiry_id = f"TEI/Enquiry/{count:03}"
    conn.close()
    return jsonify({"enquiry_id": enquiry_id})

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    data = request.form
    enquiry_id = data.get("enquiry_id")
    enquiry_type = data.get("enquiry_type")
    contractor_type = data.get("contractor_type")
    client_name = data.get("client_name")
    project_title = data.get("project_title")

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO enquiry_details (
        enquiry_id, enquiry_type, contractor_type, client_name, project_title, status
    ) VALUES (?, ?, ?, ?, ?, ?)''', (
        enquiry_id, enquiry_type, contractor_type, client_name, project_title, 'In Progress'
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": "Enquiry submitted successfully!"})

# ---------- Progress / Award ----------
@app.route('/progress-award')
def progress_award():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, enquiry_id, client_name, project_title, status FROM enquiry_details")
    enquiries = c.fetchall()
    conn.close()
    return render_template('progress_award.html', enquiries=enquiries)

# ---------- Forgot Password ----------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        session['otp'] = str(random.randint(100000, 999999))
        session['username_reset'] = request.form['username']
        flash(f"OTP sent to your email: {session['otp']} (simulated)", "info")
        return redirect(url_for('verify_otp'))
    return render_template('forgot.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered = request.form['otp']
        if 'otp' in session and entered == session['otp']:
            flash("OTP verified! You can now reset your password.", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP.", "danger")
    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_pass = request.form['password']
        username = session.get('username_reset')
        if username:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE username=?", (new_pass, username))
            conn.commit()
            conn.close()
            flash("Password updated. Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Session expired. Try again.", "danger")
            return redirect(url_for('forgot'))
    return render_template('reset_password.html')

# ---------- Other Module Placeholders ----------
@app.route('/accounts')
def accounts():
    return render_template("accounts.html")

@app.route('/project')
def project():
    return render_template("project.html")

@app.route('/production')
def production():
    return render_template("production.html")

@app.route('/customer')
def customer():
    return render_template("customer.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out", "info")
    return redirect(url_for('login'))

# ---------- Run ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
