# Zayed's Hospital (Flask)
Full-stack app with roles, onboarding flow (welcome → role → yes/no → register), and CRUD for Patients/Doctors.

## Run
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
app.py="app.py"; 1="1"
python -m flask run

## Features
- Landing + role selection with hover cards
- Inclusive registration (name, address, gender/self-describe, referral, username)
- Auth (login/logout)
- Dashboard with quick actions + counts
- Patients/Doctors: add, edit, delete, list
