from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, max-age=0"
    return response

def get_db():
    conn = sqlite3.connect('school_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- LOGIN & LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'): return redirect(url_for('index'))
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['logged_in'] = True; session['user'] = 'admin'
            return redirect(url_for('index'))
        else: flash("❌ Wrong Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

# --- DASHBOARD ---
@app.route('/')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db = get_db()
    s_count = db.execute("SELECT COUNT(*) as c FROM Students WHERE status='Active'").fetchone()['c']
    t_count = db.execute("SELECT COUNT(*) as c FROM Teachers WHERE status='Active'").fetchone()['c']
    due = db.execute("SELECT SUM(total_due) as t FROM Students WHERE status='Active'").fetchone()['t'] or 0
    coll = db.execute("SELECT SUM(amount) as t FROM Transactions").fetchone()['t'] or 0
    return render_template('index.html', s_count=s_count, t_count=t_count, expected_fee=due, collected_fee=coll)

# ================= REPORTS (FIXED ERROR HERE) =================
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db = get_db()
    
    transactions = []
    total_collected = 0  # <--- ERROR FIXED (Space removed)
    start_date = ""
    end_date = ""
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        query = '''
            SELECT t.*, s.name, s.class_name 
            FROM Transactions t 
            JOIN Students s ON t.student_id = s.id 
            WHERE date(t.date) BETWEEN ? AND ?
            ORDER BY t.date DESC
        '''
        transactions = db.execute(query, (start_date, end_date)).fetchall()
        
        for t in transactions:
            total_collected += t['amount']

    return render_template('reports.html', transactions=transactions, total=total_collected, s_date=start_date, e_date=end_date)

# ================= ACCOUNTING =================
@app.route('/accounting', methods=['GET', 'POST'])
def accounting():
    if not session.get('logged_in'): return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        sid = request.form['student_id']; amt = float(request.form['amount'])
        db.execute("INSERT INTO Transactions (student_id, amount, fee_type, mode, date, receipt_no) VALUES (?,?,?,?,?,?)",
                   (sid, amt, request.form['fee_type'], request.form['mode'], datetime.now().strftime("%Y-%m-%d %H:%M"), 'REC'+str(int(datetime.now().timestamp()))))
        db.execute("UPDATE Students SET total_due = total_due - ? WHERE id=?", (amt, sid))
        db.commit()
        return redirect(url_for('accounting'))
    
    st = db.execute("SELECT * FROM Students WHERE status='Active'").fetchall()
    tr = db.execute("SELECT t.*, s.name, s.class_name FROM Transactions t JOIN Students s ON t.student_id=s.id ORDER BY t.id DESC LIMIT 20").fetchall()
    return render_template('accounting.html', students=st, transactions=tr)

# --- OTHER ROUTES (Standard) ---
@app.route('/students')
def students():
    if not session.get('logged_in'): return redirect(url_for('login'))
    data = get_db().execute("SELECT * FROM Students WHERE status='Active'").fetchall()
    return render_template('students.html', students=data)

@app.route('/teachers')
def teachers():
    if not session.get('logged_in'): return redirect(url_for('login'))
    data = get_db().execute("SELECT * FROM Teachers WHERE status='Active'").fetchall()
    return render_template('teachers.html', teachers=data)

@app.route('/add_student', methods=['POST'])
def add_student():
    if not session.get('logged_in'): return redirect(url_for('login'))
    photo = request.files.get('photo'); fname = secure_filename(photo.filename) if photo else ""
    if photo: photo.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    sf = float(request.form['school_fee'] or 0); bf = float(request.form['bus_fee'] or 0); old = float(request.form['old_balance'] or 0)
    get_db().execute("INSERT INTO Students (name, class_name, dob, mobile, address, photo, school_fee, bus_fee, old_balance, total_due) VALUES (?,?,?,?,?,?,?,?,?,?)", (request.form['name'], request.form['class'], request.form['dob'], request.form['mobile'], request.form['address'], fname, sf, bf, old, sf+bf+old)).connection.commit()
    return redirect(url_for('students'))

@app.route('/add_teacher', methods=['POST'])
def add_teacher():
    if not session.get('logged_in'): return redirect(url_for('login'))
    photo = request.files.get('photo'); fname = secure_filename(photo.filename) if photo else ""
    if photo: photo.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    get_db().execute("INSERT INTO Teachers (name, post, dob, mobile, address, email, photo) VALUES (?,?,?,?,?,?,?)", (request.form['name'], request.form['post'], request.form['dob'], request.form['mobile'], request.form['address'], request.form['email'], fname)).connection.commit()
    return redirect(url_for('teachers'))

@app.route('/student/<int:id>')
def view_student(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    st = get_db().execute("SELECT * FROM Students WHERE id=?", (id,)).fetchone()
    tr = get_db().execute("SELECT * FROM Transactions WHERE student_id=? ORDER BY id DESC", (id,)).fetchall()
    paid = get_db().execute("SELECT SUM(amount) as t FROM Transactions WHERE student_id=?", (id,)).fetchone()['t'] or 0
    return render_template('view_student.html', s=st, trans=tr, paid=paid)

@app.route('/edit_student/<int:id>', methods=['GET','POST'])
def edit_student(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method=='POST':
        photo = request.files.get('photo'); fname = request.form['curr_photo']
        if photo and photo.filename: fname = secure_filename(photo.filename); photo.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        get_db().execute("UPDATE Students SET name=?, class_name=?, dob=?, mobile=?, address=?, photo=? WHERE id=?", (request.form['name'], request.form['class'], request.form['dob'], request.form['mobile'], request.form['address'], fname, id)).connection.commit()
        return redirect(url_for('view_student', id=id))
    st = get_db().execute("SELECT * FROM Students WHERE id=?", (id,)).fetchone()
    return render_template('edit_student.html', s=st)

@app.route('/teacher/<int:id>')
def view_teacher(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    t = get_db().execute("SELECT * FROM Teachers WHERE id=?", (id,)).fetchone()
    return render_template('view_teacher.html', t=t)

@app.route('/edit_teacher/<int:id>', methods=['GET','POST'])
def edit_teacher(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method=='POST':
        photo = request.files.get('photo'); fname = request.form['curr_photo']
        if photo and photo.filename: fname = secure_filename(photo.filename); photo.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        get_db().execute("UPDATE Teachers SET name=?, post=?, dob=?, mobile=?, address=?, email=?, photo=? WHERE id=?", (request.form['name'], request.form['post'], request.form['dob'], request.form['mobile'], request.form['address'], request.form['email'], fname, id)).connection.commit()
        return redirect(url_for('view_teacher', id=id))
    t = get_db().execute("SELECT * FROM Teachers WHERE id=?", (id,)).fetchone()
    return render_template('edit_teacher.html', t=t)

@app.route('/archive_it/<type>/<int:id>')
def archive_it(type, id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    db = get_db(); table = "Students" if type == "Student" else "Teachers"
    row = db.execute(f"SELECT * FROM {table} WHERE id=?", (id,)).fetchone()
    info = f"Due: {row['total_due']}" if type == "Student" else row['post']
    db.execute("INSERT INTO Archive (type, original_id, name, class_name, mobile, info, deleted_by, date) VALUES (?,?,?,?,?,?,?,?)", (type, id, row['name'], row['class_name'] if type=='Student' else 'Staff', row['mobile'], info, session.get('user'), datetime.now().strftime("%Y-%m-%d")))
    db.execute(f"UPDATE {table} SET status='Deleted' WHERE id=?", (id,)).connection.commit()
    return redirect(request.referrer)

@app.route('/history')
def history():
    if not session.get('logged_in'): return redirect(url_for('login'))
    data = get_db().execute("SELECT * FROM Archive ORDER BY id DESC").fetchall()
    return render_template('history.html', records=data)

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)