from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
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

# ---------- Authentication ----------
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

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

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
        flash('Vendor registered successfully!', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')

# ---------- Run Server ----------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
