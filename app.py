from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
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
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT, company_name TEXT, company_address TEXT,
        office_mobile TEXT, office_telephone TEXT, email TEXT,
        gstin TEXT, pan TEXT, tan TEXT,
        name1 TEXT, dept1 TEXT, desg1 TEXT, mob1 TEXT,
        ben_name TEXT, ben_ac TEXT, ac_type TEXT,
        bank_name TEXT, ifsc TEXT, micr TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, password TEXT
    )''')

    # Add admin if not exists
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
            flash('Login successful!', 'success')
            return redirect(url_for('register'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

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

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = (
            request.form['vendor_id'],
            request.form['company_name'],
            request.form['company_address'],
            request.form['office_mobile'],
            request.form['office_telephone'],
            request.form['email'],
            request.form['gstin'],
            request.form['pan'],
            request.form['tan'],
            request.form['name1'],
            request.form['dept1'],
            request.form['desg1'],
            request.form['mob1'],
            request.form['ben_name'],
            request.form['ben_ac'],
            request.form['ac_type'],
            request.form['bank_name'],
            request.form['ifsc'],
            request.form['micr']
        )
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (
            vendor_id, company_name, company_address, office_mobile,
            office_telephone, email, gstin, pan, tan,
            name1, dept1, desg1, mob1,
            ben_name, ben_ac, ac_type, bank_name, ifsc, micr
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', data)
        conn.commit()
        conn.close()
        flash('Vendor registered successfully!', 'success')
    return render_template('register.html')

@app.route('/vendors')
def vendors():
    if 'username' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    data = c.fetchall()
    conn.close()
    return render_template("vendors.html", vendors=data)

@app.route('/edit/<int:vendor_id>', methods=['GET', 'POST'])
def edit(vendor_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        fields = (
            request.form['company_name'],
            request.form['email'],
            request.form['office_mobile'],
            vendor_id
        )
        c.execute('''
            UPDATE vendors SET company_name=?, email=?, office_mobile=? WHERE id=?
        ''', fields)
        conn.commit()
        conn.close()
        flash("Vendor updated!", "success")
        return redirect(url_for('vendors'))

    c.execute("SELECT * FROM vendors WHERE id=?", (vendor_id,))
    vendor = c.fetchone()
    conn.close()
    return render_template('edit_vendor.html', vendor=vendor)

@app.route('/delete/<int:vendor_id>')
def delete(vendor_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM vendors WHERE id=?", (vendor_id,))
    conn.commit()
    conn.close()
    flash("Vendor deleted!", "info")
    return redirect(url_for('vendors'))

@app.route('/export')
def export():
    if 'username' not in session:
        flash("Login required", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    data = c.fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vendors"
    headers = [
        "ID", "Vendor ID", "Company Name", "Company Address", "Office Mobile",
        "Office Telephone", "Email", "GSTIN", "PAN", "TAN",
        "Contact 1 Name", "Dept", "Designation", "Mobile",
        "Beneficiary Name", "Account Number", "Account Type",
        "Bank Name", "IFSC", "MICR"
    ]
    ws.append(headers)
    for row in data:
        ws.append(row)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="vendors.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------- Run ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
