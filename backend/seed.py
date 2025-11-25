import os
from .extensions import db
from .models.user import User
from .models.department import Department
from .models.doctor import Doctor
from .models.patient import Patient
from .models.appointment import Appointment
from werkzeug.security import generate_password_hash
from datetime import date, timedelta

def seed_admin():
    """Seed default admin from environment variables, with hashed password"""

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_username or not admin_password:
        print("Admin credentials missing in .env")
        return

    admin = User.query.filter_by(role="admin").first()

    if admin:
        print("Admin already exists")
        return

    # HASH PASSWORD
    hashed_pw = generate_password_hash(admin_password)

    admin = User(
        username=admin_username,
        password=hashed_pw,
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()

    print("Admin seeded successfully")


def seed_departments():
    """Seed initial departments"""
    
    departments_data = [
        {"name": "Cardiology", "description": "Heart and cardiovascular care"},
        {"name": "Neurology", "description": "Brain and nervous system disorders"},
        {"name": "Orthopedics", "description": "Bone, joint, and muscle treatment"},
        {"name": "Pediatrics", "description": "Medical care for children"},
        {"name": "General Medicine", "description": "General health and wellness"}
    ]
    
    for dept_data in departments_data:
        existing = Department.query.filter_by(name=dept_data["name"]).first()
        if not existing:
            dept = Department(**dept_data)
            db.session.add(dept)
    
    db.session.commit()
    print(f"✓ Seeded {len(departments_data)} departments")


def seed_all():
    seed_admin()
    seed_departments()
