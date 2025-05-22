
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# ── App & Database Setup ──
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ── Models ──
class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(50), nullable=False, default='receptionist')

    def set_password(self, pw):  self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Patient(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(150), nullable=False)
    age      = db.Column(db.Integer, nullable=False)
    gender   = db.Column(db.String(20), nullable=False)

class Doctor(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(150), nullable=False)
    specialty = db.Column(db.String(150), nullable=False)

# ── Auth Helpers ──
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Routes ──
@app.route('/')
def home():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email, pw = request.form['email'].lower(), request.form['password']
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(pw):
            session['user_id'], session['user_role'] = u.id, u.role
            return redirect(url_for('dashboard'))
        flash("Invalid email or password", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        email, pw, role = request.form['email'].lower(), request.form['password'], request.form['role']
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            u=User(email=email, role=role); u.set_password(pw)
            db.session.add(u); db.session.commit()
            flash("Registered! Please log in.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear(); flash("Logged out.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ── Patient Management ──
@app.route('/patients')
@login_required
def patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

@app.route('/add_patient', methods=['GET','POST'])
@login_required
def add_patient():
    if request.method=='POST':
        n,a,g = request.form['name'], request.form['age'], request.form['gender']
        if not n or not a or not g:
            flash("Fill all fields", "danger"); return redirect(url_for('add_patient'))
        try: a=int(a)
        except: flash("Age must be a number", "danger"); return redirect(url_for('add_patient'))
        db.session.add(Patient(name=n, age=a, gender=g)); db.session.commit()
        flash("Patient added.", "success"); return redirect(url_for('patients'))
    return render_template('add_patient.html')

@app.route('/edit_patient/<int:pid>', methods=['GET','POST'])
@login_required
def edit_patient(pid):
    p=Patient.query.get_or_404(pid)
    if request.method=='POST':
        p.name,p.age,p.gender = request.form['name'], request.form['age'], request.form['gender']
        if not p.name or not p.age or not p.gender:
            flash("Fill all fields","danger"); return redirect(url_for('edit_patient',pid=pid))
        try: p.age=int(p.age)
        except: flash("Age must be a number","danger"); return redirect(url_for('edit_patient',pid=pid))
        db.session.commit(); flash("Patient updated.","success"); return redirect(url_for('patients'))
    return render_template('edit_patient.html', patient=p)

@app.route('/delete_patient/<int:pid>', methods=['POST'])
@login_required
def delete_patient(pid):
    db.session.delete(Patient.query.get_or_404(pid)); db.session.commit()
    flash("Patient deleted.","success"); return redirect(url_for('patients'))

# ── Doctor Management ──
@app.route('/doctors')
@login_required
def doctors():
    doctors = Doctor.query.all()
    return render_template('doctors.html', doctors=doctors)

@app.route('/add_doctor', methods=['GET','POST'])
@login_required
def add_doctor():
    if request.method=='POST':
        n,s=request.form['name'],request.form['specialty']
        if not n or not s:
            flash("Fill all fields","danger"); return redirect(url_for('add_doctor'))
        db.session.add(Doctor(name=n, specialty=s)); db.session.commit()
        flash("Doctor added.","success"); return redirect(url_for('doctors'))
    return render_template('add_doctor.html')

@app.route('/edit_doctor/<int:did>', methods=['GET','POST'])
@login_required
def edit_doctor(did):
    d=Doctor.query.get_or_404(did)
    if request.method=='POST':
        d.name,d.specialty=request.form['name'],request.form['specialty']
        if not d.name or not d.specialty:
            flash("Fill all fields","danger"); return redirect(url_for('edit_doctor',did=did))
        db.session.commit(); flash("Doctor updated.","success"); return redirect(url_for('doctors'))
    return render_template('edit_doctor.html', doctor=d)

@app.route('/delete_doctor/<int:did>', methods=['POST'])
@login_required
def delete_doctor(did):
    db.session.delete(Doctor.query.get_or_404(did)); db.session.commit()
    flash("Doctor deleted.","success"); return redirect(url_for('doctors'))

# ── Create DB & Run ──
if __name__=='__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)




