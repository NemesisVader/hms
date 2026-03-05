from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.sql import func
from sqlalchemy import or_
from ..utils.auth import role_required
from ..extensions import db
from ..models.doctor import Doctor
from ..models.department import Department
from ..models.patient import Patient
from ..models.user import User
from ..models.appointment import Appointment
from ..models.treatment import Treatment
from ..utils.cache import cache_get, cache_set, cache_delete
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/doctors", methods=["POST"])
@jwt_required()
@role_required("admin")
def add_doctor():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")
    specialization = data.get("specialization")
    department_id = data.get("department_id")
    availability = data.get("availability", {})

    if not username or not password or not specialization or not department_id:
        return jsonify({"msg": "username, password, specialization and department_id are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 409

    dept = Department.query.get(department_id)
    if not dept:
        return jsonify({"msg": "department_id is invalid"}), 400

    hashed_pw = generate_password_hash(password)
    user = User(username=username, password=hashed_pw, role="doctor")
    db.session.add(user)
    db.session.flush()

    if availability and not isinstance(availability, dict):
        return jsonify({"msg": "availability must be a JSON object (dict)"}), 400

    doctor = Doctor(
        user_id=user.id,
        specialization=specialization,
        department_id=department_id,
        availability=availability or {}
    )

    db.session.add(doctor)
    db.session.commit()

    cache_delete("doctors_list")
    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{department_id}")

    return jsonify({"msg": "Doctor added successfully", "doctor_id": doctor.id}), 201


@admin_bp.route("/doctors", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_doctors():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    cache_key = "doctors_list"
    cached = cache_get(cache_key)
    if cached is not None:
        total = len(cached)
        start = (page - 1) * per_page
        end = start + per_page
        items = cached[start:end]
        return jsonify({
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total
        })

    q = Doctor.query.order_by(Doctor.id)
    docs = q.all()

    data = []
    for d in docs:
        user = User.query.get(d.user_id)
        dept = Department.query.get(d.department_id)
        data.append({
            "doctor_id": d.id,
            "name": user.username if user else None,
            "specialization": d.specialization,
            "department": dept.name if dept else None,
            "availability": d.availability or {},
            "is_active": user.is_active if user else False
        })

    cache_set(cache_key, data)
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    items = data[start:end]

    return jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total
    })


@admin_bp.route("/doctors/<int:doctor_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_doctor(doctor_id):
    cache_key = f"doctor:{doctor_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return jsonify(cached)

    d = Doctor.query.get(doctor_id)
    if not d:
        return jsonify({"msg": "Doctor not found"}), 404
    user = User.query.get(d.user_id)
    dept = Department.query.get(d.department_id)
    payload = {
        "doctor_id": d.id,
        "name": user.username if user else None,
        "specialization": d.specialization,
        "department": dept.name if dept else None,
        "availability": d.availability or {}
    }

    cache_set(cache_key, payload)
    return jsonify(payload)


@admin_bp.route("/doctors/<int:doctor_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    old_dept_id = doc.department_id

    data = request.get_json() or {}
    if "department_id" in data and data.get("department_id") and not Department.query.get(data.get("department_id")):
        return jsonify({"msg": "department_id is invalid"}), 400

    if "availability" in data and data.get("availability") is not None and not isinstance(data.get("availability"), dict):
        return jsonify({"msg": "availability must be a JSON object (dict)"}), 400

    if "username" in data and data.get("username"):
        user = User.query.get(doc.user_id)
        if user:
            existing = User.query.filter(User.username == data["username"], User.id != user.id).first()
            if existing:
                return jsonify({"msg": "Username already taken"}), 409
            user.username = data["username"]

    doc.specialization = data.get("specialization", doc.specialization)
    doc.department_id = data.get("department_id", doc.department_id)
    doc.availability = data.get("availability", doc.availability)

    db.session.commit()

    cache_delete("doctors_list")
    cache_delete(f"doctor:{doctor_id}")
    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{old_dept_id}")
    cache_delete(f"dept_doctors:{doc.department_id}")
    cache_delete(f"availability:{doctor_id}")

    return jsonify({"msg": "Doctor updated"})


@admin_bp.route("/doctors/<int:doctor_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    user = User.query.get(doc.user_id)
    if user:
        user.is_active = False
    db.session.commit()

    cache_delete("doctors_list")
    cache_delete(f"doctor:{doctor_id}")
    cache_delete("admin:dashboard")

    return jsonify({"msg": "Doctor blacklisted successfully"})


@admin_bp.route("/doctors/<int:doctor_id>/restore", methods=["PUT"])
@jwt_required()
@role_required("admin")
def restore_doctor(doctor_id):
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    user = User.query.get(doc.user_id)
    if user:
        user.is_active = True
    db.session.commit()

    cache_delete("doctors_list")
    cache_delete(f"doctor:{doctor_id}")
    cache_delete("admin:dashboard")

    return jsonify({"msg": "Doctor restored successfully"})


@admin_bp.route("/doctors/search", methods=["GET"])
@jwt_required()
@role_required("admin")
def search_doctors():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"msg": "Search query missing"}), 400

    q_like = f"%{query}%"

    results = (
        Doctor.query
        .join(User)
        .outerjoin(Department)
        .filter(
            or_(
                User.username.ilike(q_like),
                Doctor.specialization.ilike(q_like),
                func.coalesce(Department.name, "").ilike(q_like)
            )
        )
        .all()
    )

    return jsonify([
        {
            "doctor_id": d.id,
            "name": d.user.username,
            "specialization": d.specialization,
            "department": d.department.name if d.department else None,
            "availability": d.availability or {}
        }
        for d in results
    ])


@admin_bp.route("/doctors/<int:doctor_id>/availability", methods=["PUT"])
@jwt_required()
@role_required("admin")
def set_doctor_availability(doctor_id):
    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    data = request.get_json() or {}
    availability = data.get("availability")

    if availability is None or not isinstance(availability, dict):
        return jsonify({"msg": "Invalid availability format. Must be JSON object (dict)."}), 400

    for day, slots in availability.items():
        if not isinstance(slots, list):
            return jsonify({"msg": f"Invalid format for {day}. Must be a list of slots"}), 400

    doc.availability = availability or {}
    db.session.commit()

    cache_delete("doctors_list")
    cache_delete(f"doctor:{doctor_id}")
    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{doc.department_id}")
    cache_delete(f"availability:{doctor_id}")

    return jsonify({"msg": "Availability updated successfully"})


@admin_bp.route("/patients", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_patients():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    cache_key = f"admin:patients:p{page}:pp{per_page}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    q = Patient.query.order_by(Patient.id)
    paged = q.paginate(page=page, per_page=per_page, error_out=False)

    data = []
    for p in paged.items:
        user = User.query.get(p.user_id)
        data.append({
            "patient_id": p.id,
            "name": user.username if user else "Unknown (User record missing)",
            "age": p.age,
            "gender": p.gender,
            "phone": p.phone,
            "address": p.address,
            "is_active": user.is_active if user else False
        })

    result = {
        "items": data,
        "page": page,
        "per_page": per_page,
        "total": paged.total
    }
    cache_set(cache_key, result, expire=300)
    return jsonify(result)


@admin_bp.route("/patients/<int:patient_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"msg": "Patient not found"}), 404
    user = User.query.get(p.user_id)
    return jsonify({
        "patient_id": p.id,
        "name": user.username if user else "Unknown (User record missing)",
        "age": p.age,
        "gender": p.gender,
        "phone": p.phone,
        "address": p.address
    })


@admin_bp.route("/patients/<int:patient_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"msg": "Patient not found"}), 404

    data = request.get_json() or {}
    p.age = data.get("age", p.age)
    p.gender = data.get("gender", p.gender)
    p.phone = data.get("phone", p.phone)
    p.address = data.get("address", p.address)

    if data.get("username"):
        u = User.query.get(p.user_id)
        if u:
            if User.query.filter(User.username == data.get("username"), User.id != u.id).first():
                return jsonify({"msg": "username already taken"}), 409
            u.username = data.get("username")

    db.session.commit()
    return jsonify({"msg": "Patient updated"})


@admin_bp.route("/patients/<int:patient_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"msg": "Patient not found"}), 404

    user = User.query.get(p.user_id)
    if user:
        user.is_active = False
    db.session.commit()

    cache_delete("admin:dashboard")
    cache_delete("admin:patients:p1:pp50")

    return jsonify({"msg": "Patient blacklisted successfully"})


@admin_bp.route("/patients/<int:patient_id>/restore", methods=["PUT"])
@jwt_required()
@role_required("admin")
def restore_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return jsonify({"msg": "Patient not found"}), 404

    user = User.query.get(p.user_id)
    if user:
        user.is_active = True
    db.session.commit()

    cache_delete("admin:dashboard")
    cache_delete("admin:patients:p1:pp50")

    return jsonify({"msg": "Patient restored successfully"})


@admin_bp.route("/patients/search", methods=["GET"])
@jwt_required()
@role_required("admin")
def search_patients():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"msg": "Search query missing"}), 400

    results = (
        Patient.query
        .join(User, Patient.user_id == User.id)
        .filter(
            or_(
                User.username.ilike(f"%{q}%"),
                Patient.phone.ilike(f"%{q}%"),
                Patient.id == (q.isdigit() and int(q) or -1)
            )
        ).all()
    )

    output = []
    for p in results:
        output.append({
            "patient_id": p.id,
            "name": p.user.username if p.user else None,
            "age": p.age,
            "gender": p.gender,
            "phone": p.phone,
            "address": p.address
        })

    return jsonify(output)


@admin_bp.route("/appointments", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_all_appointments():
    doctor_id = request.args.get("doctor_id")
    patient_id = request.args.get("patient_id")
    date_q = request.args.get("date")
    status_q = request.args.get("status")

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 100))

    cache_key = f"admin:appointments:p{page}:pp{per_page}:d{doctor_id}:pa{patient_id}:dt{date_q}:s{status_q}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    q = Appointment.query

    if doctor_id:
        q = q.filter(Appointment.doctor_id == int(doctor_id))
    if patient_id:
        q = q.filter(Appointment.patient_id == int(patient_id))
    if date_q:
        q = q.filter(Appointment.date == date_q)
    if status_q:
        q = q.filter(Appointment.status.ilike(f"%{status_q}%"))

    q = q.order_by(Appointment.date.desc(), Appointment.time.desc())
    paged = q.paginate(page=page, per_page=per_page, error_out=False)

    data = []
    for a in paged.items:
        doctor = Doctor.query.get(a.doctor_id)
        patient = Patient.query.get(a.patient_id)
        doctor_user = User.query.get(doctor.user_id) if doctor else None
        patient_user = User.query.get(patient.user_id) if patient else None

        data.append({
            "appointment_id": a.id,
            "doctor_id": doctor.id if doctor else None,
            "doctor": doctor_user.username if doctor_user else None,
            "patient_id": patient.id if patient else None,
            "patient": patient_user.username if patient_user else None,
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    result = {
        "items": data,
        "page": page,
        "per_page": per_page,
        "total": paged.total
    }
    cache_set(cache_key, result, expire=120)
    return jsonify(result)


@admin_bp.route("/appointments/<int:appt_id>/status", methods=["PUT"])
@jwt_required()
@role_required("admin")
def admin_update_appointment_status(appt_id):
    appt = Appointment.query.get(appt_id)
    if not appt:
        return jsonify({"msg": "Appointment not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ["Booked", "Completed", "Cancelled"]:
        return jsonify({"msg": "Invalid status. Must be Booked, Completed, or Cancelled"}), 400

    old_status = appt.status
    appt.status = new_status
    db.session.commit()

    cache_delete("admin:dashboard")

    return jsonify({
        "msg": f"Status updated from {old_status} to {new_status}",
        "appointment_id": appt.id,
        "status": new_status
    })


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("admin")
def dashboard():
    cache_key = "admin:dashboard"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    today = date.today()
    upcoming_cutoff = today + timedelta(days=7)

    today_count = Appointment.query.filter(Appointment.date == str(today)).count()
    upcoming_count = Appointment.query.filter(
        Appointment.date > str(today),
        Appointment.date <= str(upcoming_cutoff)
    ).count()

    result = {
        "doctors": Doctor.query.count(),
        "patients": Patient.query.count(),
        "appointments": Appointment.query.count(),
        "departments": Department.query.count(),
        "today_appointments": today_count,
        "upcoming_7days_appointments": upcoming_count
    }
    cache_set(cache_key, result, expire=60)
    return jsonify(result)


@admin_bp.route("/departments", methods=["POST"])
@jwt_required()
@role_required("admin")
def create_department():
    data = request.get_json() or {}

    name = data.get("name")
    description = data.get("description", "")

    if not name:
        return {"msg": "Department name required"}, 400

    if Department.query.filter_by(name=name).first():
        return {"msg": "Department already exists"}, 409

    dept = Department(name=name, description=description)
    db.session.add(dept)
    db.session.commit()

    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{dept.id}")
    cache_delete(f"department:{dept.id}")

    return {"msg": "Department created", "id": dept.id}, 201


@admin_bp.route("/departments", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_departments():
    cache_key = "departments_list"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    departments = Department.query.all()
    data = []

    for dept in departments:
        doctors_data = []
        for doc in dept.doctors:
            user = User.query.get(doc.user_id)
            doctors_data.append({
                "doctor_id": doc.id,
                "name": user.username if user else None,
                "specialization": doc.specialization,
                "availability": doc.availability or {}
            })

        data.append({
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "doctor_count": len(doctors_data),
            "doctors": doctors_data
        })

    cache_set(cache_key, data)
    return jsonify(data)


@admin_bp.route("/departments/search", methods=["GET"])
@jwt_required()
@role_required("admin")
def search_departments():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"msg": "Search query missing"}), 400

    results = Department.query.filter(Department.name.ilike(f"%{q}%")).all()

    return jsonify([{
        "id": d.id,
        "name": d.name,
        "description": d.description,
        "doctor_count": len(d.doctors)
    } for d in results])


@admin_bp.route("/departments/<int:dept_id>", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_department(dept_id):
    cache_key = f"department:{dept_id}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"msg": "Department not found"}), 404

    doctors_data = []
    for doc in dept.doctors:
        user = User.query.get(doc.user_id)
        doctors_data.append({
            "doctor_id": doc.id,
            "name": user.username if user else None,
            "specialization": doc.specialization,
            "availability": doc.availability or {}
        })

    payload = {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "doctors": doctors_data
    }

    cache_set(cache_key, payload)
    return jsonify(payload)


@admin_bp.route("/departments/<int:dept_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def update_department(dept_id):
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"msg": "Department not found"}), 404

    data = request.get_json() or {}

    dept.name = data.get("name", dept.name)
    dept.description = data.get("description", dept.description)

    db.session.commit()

    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{dept_id}")
    cache_delete(f"department:{dept_id}")

    return jsonify({"msg": "Department updated successfully"})


@admin_bp.route("/departments/<int:dept_id>", methods=["DELETE"])
@jwt_required()
@role_required("admin")
def delete_department(dept_id):
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"msg": "Department not found"}), 404

    if len(dept.doctors) > 0:
        return jsonify({"msg": "Cannot delete department with registered doctors"}), 400

    db.session.delete(dept)
    db.session.commit()

    cache_delete("departments_list")
    cache_delete("patient_departments")
    cache_delete(f"dept_doctors:{dept_id}")
    cache_delete(f"department:{dept_id}")

    return jsonify({"msg": "Department deleted"})
