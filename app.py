from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from flask import send_file
import openpyxl
from io import BytesIO

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
        name2 TEXT, dept2 TEXT, desg2 TEXT, mob2 TEXT,
        ben_name TEXT, ben_ac TEXT, ac_type TEXT,
        bank_name TEXT, ifsc TEXT, micr TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT, password TEXT
    )''')

    # Insert default admin if not exists
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
            flash('Login successful!', 'success')
            return redirect(url_for('register'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = tuple(request.form.values())
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''INSERT INTO vendors (
            vendor_id, company_name, company_address, office_mobile,
            office_telephone, email, gstin, pan, tan,
            name1, dept1, desg1, mob1,
            name2, dept2, desg2, mob2,
            ben_name, ben_ac, ac_type, bank_name, ifsc, micr
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', data)
        conn.commit()
        conn.close()
        flash('Vendor registered successfully!', 'success')
    return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        flash("OTP sent to your email (simulation).", "info")
    return render_template('forgot.html')

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

    # GET request
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

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vendors"

    # Column titles
    headers = [
        "ID", "Vendor ID", "Company Name", "Company Address", "Office Mobile",
        "Office Telephone", "Email", "GSTIN", "PAN", "TAN",
        "Contact 1 Name", "Contact 1 Dept", "Contact 1 Designation", "Contact 1 Mobile",
        "Contact 2 Name", "Contact 2 Dept", "Contact 2 Designation", "Contact 2 Mobile",
        "Bank Name", "Account Number", "Account Type", "Bank", "IFSC", "MICR"
    ]
    ws.append(headers)

    for row in data:
        ws.append(row)

    # Save to memory
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="vendors.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------- Run ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=10000)
