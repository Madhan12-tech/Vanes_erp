from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "vanes_secret_key"
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- DB Initialization ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS enquiry_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enquiry_id TEXT,
            enquiry_type TEXT,
            contractor_type TEXT,
            client_name TEXT,
            project_title TEXT,
            status TEXT DEFAULT 'In Progress',
            file_name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            client_name TEXT,
            project_title TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))
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

# ---------- New Enquiry Form (AJAX Load) ----------
@app.route('/new_enquiry_form')
def new_enquiry_form():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('new_enquiry.html')

@app.route('/get_enquiry_id')
def get_enquiry_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM enquiry_details")
    count = c.fetchone()[0] + 1
    conn.close()
    return jsonify({"enquiry_id": f"TEI/Enquiry/{count:03}"})

# ---------- Submit New Enquiry ----------
@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    enquiry_id = request.form.get('enquiry_id')
    enquiry_type = request.form.get('enquiry_type')
    contractor_type = request.form.get('contractor_type')
    client_name = request.form.get('client_name')
    project_title = request.form.get('project_title')

    file = request.files.get('file')
    file_name = None
    if file and file.filename:
        filename = secure_filename(f"{enquiry_id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_name = filename

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO enquiry_details (
        enquiry_id, enquiry_type, contractor_type, client_name, project_title, status, file_name
    ) VALUES (?, ?, ?, ?, ?, ?, ?)''', (
        enquiry_id, enquiry_type, contractor_type, client_name, project_title, 'In Progress', file_name))

    c.execute('''INSERT INTO project_details (
        project_id, client_name, project_title, status
    ) VALUES (?, ?, ?, ?)''', (
        enquiry_id, client_name, project_title, 'Pending'))

    conn.commit()
    conn.close()

    return jsonify({"message": "Enquiry submitted successfully!"})

# ---------- View Progress / Award Status ----------
@app.route('/progress-award')
def progress_award():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM enquiry_details")
    enquiries = c.fetchall()
    conn.close()
    return render_template('progress_award.html', enquiries=enquiries)

# ---------- Edit Enquiry ----------
@app.route('/edit_enquiry/<int:id>', methods=['GET', 'POST'])
def edit_enquiry(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        form = request.form
        c.execute('''UPDATE enquiry_details SET 
                        enquiry_type=?, contractor_type=?, client_name=?, project_title=? 
                    WHERE id=?''',
                  (form['enquiry_type'], form['contractor_type'], form['client_name'],
                   form['project_title'], id))
        conn.commit()
        conn.close()
        flash('Enquiry updated successfully!', 'success')
        return redirect(url_for('progress_award'))
    c.execute("SELECT * FROM enquiry_details WHERE id=?", (id,))
    enquiry = c.fetchone()
    conn.close()
    return render_template("edit_enquiry.html", enquiry=enquiry)

# ---------- Project Status ----------
@app.route('/project_status')
def project_status():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM project_details")
    projects = c.fetchall()
    conn.close()
    return render_template('project_status.html', projects=projects)

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
        flash('Vendor registration logic here.', 'success')
        return redirect(url_for('register'))
    return render_template('register.html')

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

# ---------- Server ----------
if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    
