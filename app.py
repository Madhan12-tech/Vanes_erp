from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import sqlite3
import openpyxl
from io import BytesIO
import random
import os

app = Flask(__name__)
app.secret_key = 'vanes_secret_key'

# ---------- DB Initialization ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, password TEXT
    )''')

    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    c.execute('''CREATE TABLE IF NOT EXISTS enquiry_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT, enquiry_type TEXT, contractor_type TEXT,
        client_name TEXT, project_title TEXT, status TEXT DEFAULT 'In Progress'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS project_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT, client_name TEXT, project_title TEXT, status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT, company_name TEXT, company_address TEXT,
        office_mobile TEXT, office_telephone TEXT, email TEXT,
        gstin TEXT, pan TEXT, tan TEXT,
        ben_name TEXT, ben_ac TEXT, ac_type TEXT,
        bank_name TEXT, ifsc TEXT, micr TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS vendor_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT,
        name TEXT, dept TEXT, desg TEXT, mob TEXT
    )''')

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
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out", "info")
    return redirect(url_for('login'))

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        session['otp'] = str(random.randint(100000, 999999))
        session['username_reset'] = request.form['username']
        flash(f"OTP sent: {session['otp']} (simulated)", "info")
        return redirect(url_for('verify_otp'))
    return render_template('forgot.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        if request.form['otp'] == session.get('otp'):
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP", "danger")
    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_pass = request.form['password']
        uname = session.get('username_reset')
        if uname:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET password=? WHERE username=?", (new_pass, uname))
            conn.commit()
            conn.close()
            flash("Password updated", "success")
            return redirect(url_for('login'))
    return render_template('reset_password.html')

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
    return render_template('dashboard.html', modules=modules)

@app.route('/management')
def management():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('management.html')

# ---------- Enquiry Modal ----------
@app.route('/get_enquiry_id')
def get_enquiry_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM enquiry_details")
    count = c.fetchone()[0] + 1
    conn.close()
    return jsonify({"enquiry_id": f"TEI/Enquiry/{count:03}"})

@app.route('/new_enquiry_form')
def new_enquiry_form():
    return render_template('new_enquiry.html')

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    form = request.form
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO enquiry_details (
        enquiry_id, enquiry_type, contractor_type, client_name, project_title, status
    ) VALUES (?, ?, ?, ?, ?, ?)''', (
        form['enquiry_id'], form['enquiry_type'], form['contractor_type'],
        form['client_name'], form['project_title'], 'In Progress'))

    c.execute('''INSERT INTO project_details (
        project_id, client_name, project_title, status
    ) VALUES (?, ?, ?, ?)''', (
        form['enquiry_id'], form['client_name'], form['project_title'], 'Pending'))

    conn.commit()
    conn.close()
    return jsonify({"message": "Enquiry submitted successfully!"})

@app.route('/progress-award')
def progress_award():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM enquiry_details")
    enquiries = c.fetchall()
    conn.close()
    return render_template("progress_award.html", enquiries=enquiries)

# ---------- Project Status ----------
@app.route('/project_status')
def project_status():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM project_details")
    projects = c.fetchall()
    conn.close()
    return render_template("project_status.html", projects=projects)

@app.route('/approve_project/<project_id>')
def approve_project(project_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE project_details SET status='Approved' WHERE project_id=?", (project_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('project_status'))

@app.route('/reject_project/<project_id>')
def reject_project(project_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE project_details SET status='Rejected' WHERE project_id=?", (project_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('project_status'))

# ---------- Vendor Registration ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        form = request.form
        vendor_data = (
            form['vendor_id'], form['company_name'], form['company_address'],
            form['office_mobile'], form['office_telephone'], form['email'],
            form['gstin'], form['pan'], form['tan'],
            form['ben_name'], form['ben_ac'], form['ac_type'],
            form['bank_name'], form['ifsc'], form['micr']
        )
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (
            vendor_id, company_name, company_address, office_mobile,
            office_telephone, email, gstin, pan, tan,
            ben_name, ben_ac, ac_type, bank_name, ifsc, micr
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', vendor_data)

        names = request.form.getlist('contact_name[]')
        depts = request.form.getlist('contact_dept[]')
        desigs = request.form.getlist('contact_desg[]')
        mobs = request.form.getlist('contact_mob[]')

        for name, dept, desg, mob in zip(names, depts, desigs, mobs):
            c.execute('''INSERT INTO vendor_contacts (vendor_id, name, dept, desg, mob)
                         VALUES (?, ?, ?, ?, ?)''', (form['vendor_id'], name, dept, desg, mob))

        conn.commit()
        conn.close()
        flash("Vendor Registered", "success")
        return redirect(url_for('register'))

    return render_template("register.html")

# ---------- Other Modules ----------
@app.route('/accounts')
def accounts():
    return render_template("accounts.html")

@app.route('/project')
def project():
    return render_template("project.html")

@app.route('/production')
def production():
    return render_template("production.html")

@app.route('/sales')
def sales():
    return render_template("sales.html")

@app.route('/customer')
def customer():
    return render_template("customer.html")

# ---------- Start App ----------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
