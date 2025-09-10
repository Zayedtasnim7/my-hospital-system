from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key_here")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instance/hospital.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ── Models ──
class User(db.Model):
    __tablename__ = "users"  # ✅ avoid Postgres reserved word "user"
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(50), nullable=False, default="receptionist")

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Profile(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)  # ✅ updated FK
    first_name = db.Column(db.String(100))
    middle_name= db.Column(db.String(100))
    last_name  = db.Column(db.String(100))
    address    = db.Column(db.String(255))
    gender     = db.Column(db.String(100))   # free-text, inclusive
    referral_source = db.Column(db.String(120))
    username   = db.Column(db.String(120), unique=True)
    user     = db.relationship("User", backref=db.backref("profile", uselist=False))

class Patient(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.String(150), nullable=False)
    age    = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)

class Doctor(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(150), nullable=False)
    specialty = db.Column(db.String(150), nullable=False)



# ✅ Health check for Render so it knows your service is alive
@app.route("/healthz")
def healthz():
    return "ok", 200

# ── Auth helper ──
def login_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return inner

# ── Landing flow ──
@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("welcome"))

@app.route("/welcome")
def welcome():
    return render_template("landing.html")

@app.route("/get-started")
def get_started():
    role = request.args.get("role", "Patient")
    session["selected_role"] = role
    return render_template("get_started.html", role=role)

# ── Auth ──
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower().strip()
        pw    = request.form["password"]
        u = User.query.filter_by(email=email).first()
        if u and u.check_password(pw):
            session["user_id"], session["user_role"] = u.id, u.role
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    role = request.args.get("role") or session.get("selected_role") or "Patient"
    if request.method == "POST":
        # account bits
        email = request.form["email"].lower().strip()
        pw    = request.form["password"]
        pw2   = request.form["password2"]
        role  = request.form.get("role") or role

        # profile bits
        first = request.form.get("first_name","").strip()
        middle= request.form.get("middle_name","").strip()
        last  = request.form.get("last_name","").strip()
        addr  = request.form.get("address","").strip()
        gender= request.form.get("gender","").strip()
        if gender == "Self-describe":
            gender = request.form.get("gender_self","").strip()
        heard = request.form.get("referral_source","").strip()
        username = request.form.get("username","").strip()

        if pw != pw2:
            flash("Passwords do not match.", "danger"); return redirect(url_for("register", role=role))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning"); return redirect(url_for("register", role=role))
        if username and Profile.query.filter_by(username=username).first():
            flash("Username is taken.", "warning"); return redirect(url_for("register", role=role))

        u = User(email=email, role=role); u.set_password(pw)
        db.session.add(u); db.session.flush()  # get u.id
        prof = Profile(user_id=u.id, first_name=first, middle_name=middle, last_name=last,
                       address=addr, gender=gender, referral_source=heard, username=username)
        db.session.add(prof); db.session.commit()
        flash("Yay! Account created — please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", role=role)

@app.route("/logout")
@login_required
def logout():
    session.clear(); flash("Logged out.", "info")
    return redirect(url_for("login"))

# ── Dashboard ──
@app.route("/dashboard")
@login_required
def dashboard():
    u = User.query.get(session["user_id"])
    display_name = (u.profile.first_name if u and u.profile and u.profile.first_name else u.email.split("@")[0])
    return render_template("dashboard.html",
                           name=display_name,
                           role=u.role if u else "User",
                           patient_count=Patient.query.count(),
                           doctor_count=Doctor.query.count())

# ── Patients ──
@app.route("/patients")
@login_required
def patients():
    pts = Patient.query.order_by(Patient.id.desc()).all()
    return render_template("patients.html", patients=pts)

@app.route("/add_patient", methods=["GET","POST"])
@login_required
def add_patient():
    if request.method == "POST":
        n = request.form["name"].strip()
        a = request.form["age"].strip()
        g = request.form["gender"].strip()
        if not n or not a or not g:
            flash("Fill all fields.", "danger"); return redirect(url_for("add_patient"))
        try: a = int(a)
        except: flash("Age must be a number.", "danger"); return redirect(url_for("add_patient"))
        db.session.add(Patient(name=n, age=a, gender=g)); db.session.commit()
        flash("Patient added.", "success"); return redirect(url_for("patients"))
    return render_template("add_patient.html")

@app.route("/edit_patient/<int:pid>", methods=["GET","POST"])
@login_required
def edit_patient(pid):
    p = Patient.query.get_or_404(pid)
    if request.method == "POST":
        p.name = request.form["name"].strip()
        p.gender = request.form["gender"].strip()
        try: p.age = int(request.form["age"].strip())
        except: flash("Age must be a number.", "danger"); return redirect(url_for("edit_patient", pid=pid))
        db.session.commit(); flash("Patient updated.", "success"); return redirect(url_for("patients"))
    return render_template("edit_patient.html", patient=p)

@app.route("/delete_patient/<int:pid>", methods=["POST"])
@login_required
def delete_patient(pid):
    db.session.delete(Patient.query.get_or_404(pid)); db.session.commit()
    flash("Patient deleted.", "success"); return redirect(url_for("patients"))

# ── Doctors ──
@app.route("/doctors")
@login_required
def doctors():
    docs = Doctor.query.order_by(Doctor.id.desc()).all()
    return render_template("doctors.html", doctors=docs)

@app.route("/add_doctor", methods=["GET","POST"])
@login_required
def add_doctor():
    if request.method == "POST":
        n = request.form["name"].strip()
        s = request.form["specialty"].strip()
        if not n or not s:
            flash("Fill all fields.", "danger"); return redirect(url_for("add_doctor"))
        db.session.add(Doctor(name=n, specialty=s)); db.session.commit()
        flash("Doctor added.", "success"); return redirect(url_for("doctors"))
    return render_template("add_doctor.html")

@app.route("/edit_doctor/<int:did>", methods=["GET","POST"])
@login_required
def edit_doctor(did):
    d = Doctor.query.get_or_404(did)
    if request.method == "POST":
        d.name = request.form["name"].strip()
        d.specialty = request.form["specialty"].strip()
        if not d.name or not d.specialty:
            flash("Fill all fields.", "danger"); return redirect(url_for("edit_doctor", did=did))
        db.session.commit(); flash("Doctor updated.", "success"); return redirect(url_for("doctors"))
    return render_template("edit_doctor.html", doctor=d)

@app.route("/delete_doctor/<int:did>", methods=["POST"])
@login_required
def delete_doctor(did):
    db.session.delete(Doctor.query.get_or_404(did)); db.session.commit()
    flash("Doctor deleted.", "success"); return redirect(url_for("doctors"))

if __name__ == "__main__":
    app.run(debug=True)
