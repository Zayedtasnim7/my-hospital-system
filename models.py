from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(50), nullable=False, default='receptionist')
    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Patient(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.String(150), nullable=False)
    age    = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)

class Doctor(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(150), nullable=False)
    specialty = db.Column(db.String(150), nullable=False)



