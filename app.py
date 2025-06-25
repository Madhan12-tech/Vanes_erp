from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import openpyxl
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'vanes_secret_key'

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Vendor main table
    c.execute('''CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT, company_name TEXT, company_address TEXT,
        office_mobile TEXT, office_telephone TEXT, email TEXT,
        gstin TEXT, pan TEXT, tan TEXT,
        ben_name TEXT, ben_ac TEXT, ac_type TEXT,
        bank_name TEXT, ifsc TEXT, micr TEXT
    )''')

    # Communication table
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id TEXT,
        name TEXT, dept TEXT, desg TEXT, mob TEXT
    )''')

    # Login table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, password TEXT
    )''')

    # Default user
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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

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
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', vendor_data)
        
        vendor_id = form['vendor_id']
        names = request.form.getlist('contact_name[]')
        depts = request.form.getlist('contact_dept[]')
        desigs = request.form.getlist('contact_desg[]')
        mobs = request.form.getlist('contact_mob[]')

        for name, dept, desg, mob in zip(names, depts, desigs, mobs):
            c.execute('''INSERT INTO vendor_contacts (vendor_id, name, dept, desg, mob)
                         VALUES (?, ?, ?, ?, ?)''', (vendor_id, name, dept, desg, mob))
        
        conn.commit()
        conn.close()
        flash('Vendor registered successfully!', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/vendors')
def vendors():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    vendors = c.fetchall()
    conn.close()
    return render_template("vendors.html", vendors=vendors)

@app.route('/export')
def export():
    if 'username' not in session:
        return redirect(url_for('login'))

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

# ---------- Run ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
