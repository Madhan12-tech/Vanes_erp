from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
import sqlite3
import openpyxl
from io import BytesIO
import random

app = Flask(__name__)
app.secret_key = 'vanes_secret_key'

# ---------- DB INIT ----------
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

    c.execute('''CREATE TABLE IF NOT EXISTS enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enquiry_id TEXT, enquiry_type TEXT, contractor_type TEXT, client_name TEXT, project_title TEXT
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
        vendor_id TEXT, name TEXT, dept TEXT, desg TEXT, mob TEXT
    )''')

    conn.commit()
    conn.close()

# ---------- AUTH ----------
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
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        session['otp'] = str(random.randint(100000, 999999))
        session['username_reset'] = request.form['username']
        flash(f"OTP sent: {session['otp']} (for demo)", "info")
        return redirect(url_for('verify_otp'))
    return render_template('forgot.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        if request.form['otp'] == session.get('otp'):
            flash("OTP Verified!", "success")
            return redirect(url_for('reset_password'))
        flash("Invalid OTP", "danger")
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
        flash("Session expired. Try again.", "danger")
        return redirect(url_for('forgot'))
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully", "info")
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
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

# ---------- ENQUIRY ----------
@app.route('/get_enquiry_id')
def get_enquiry_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM enquiries")
    count = c.fetchone()[0] + 1
    enquiry_id = f"TEI/Enquiry/{count:03}"
    conn.close()
    return jsonify({'enquiry_id': enquiry_id})

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    data = request.form
    enquiry_id = data.get('enquiry_id')
    enquiry_type = data.get('enquiry_type')
    contractor_type = data.get('contractor_type')
    client_name = data.get('client_name')
    project_title = data.get('project_title')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO enquiries (enquiry_id, enquiry_type, contractor_type, client_name, project_title) VALUES (?, ?, ?, ?, ?)",
              (enquiry_id, enquiry_type, contractor_type, client_name, project_title))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Enquiry submitted successfully'})

# ---------- PROGRESS/AWARD ----------
@app.route('/progress-award')
def progress_award():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT enquiry_id, client_name, project_title FROM enquiries")
    enquiries = c.fetchall()
    conn.close()
    return render_template('progress_award.html', enquiries=enquiries)

# ---------- DUMMY ROUTES ----------
@app.route('/accounts')
def accounts():
    return render_template('accounts.html')

@app.route('/project')
def project():
    return render_template('project.html')

@app.route('/production')
def production():
    return render_template('production.html')

@app.route('/sales')
def sales():
    return render_template('sales.html')

@app.route('/customer')
def customer():
    return render_template('customer.html')

# ---------- EXPORT ----------
@app.route('/export')
def export():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    vendors = c.fetchall()
    c.execute("SELECT * FROM vendor_contacts")
    contacts = c.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Vendors"
    ws1.append([
        "ID", "Vendor ID", "Company Name", "Company Address", "Office Mobile",
        "Office Telephone", "Email", "GSTIN", "PAN", "TAN",
        "Beneficiary Name", "Account Number", "Account Type", "Bank Name", "IFSC", "MICR"
    ])
    for row in vendors:
        ws1.append(row)

    ws2 = wb.create_sheet("Contacts")
    ws2.append(["ID", "Vendor ID", "Name", "Department", "Designation", "Mobile"])
    for row in contacts:
        ws2.append(row)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="vendors.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------- MAIN ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=10000)
