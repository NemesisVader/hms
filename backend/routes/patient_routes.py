from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.auth import role_required
from ..extensions import db
from ..models.user import User
from ..models.patient import Patient
from ..models.department import Department
from ..models.doctor import Doctor
from ..models.appointment import Appointment
from ..models.treatment import Treatment
from ..utils.cache import cache_get, cache_set, cache_delete
from ..tasks.tasks import export_treatments as export_task
from datetime import date, datetime
import re

patient_bp = Blueprint("patient", __name__)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{2}:\d{2}$")


def get_current_patient():
    user_id = int(get_jwt_identity())
    return Patient.query.filter_by(user_id=user_id).first()


def is_slot_in_availability(availability: dict, appt_date: str, appt_time: str) -> bool:
    try:
        dt = datetime.strptime(appt_date, "%Y-%m-%d").date()
    except Exception:
        return False

    short_day = dt.strftime("%a")          # e.g. "Mon"
    full_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    full_day = full_days[dt.weekday()]     # e.g. "Monday"

    slots = (
        availability.get(short_day)
        or availability.get(full_day)
        or []
    )
    return appt_time in slots


def doctor_has_conflict(doctor_id: int, appt_date: str, appt_time: str, exclude_appt_id: int = None) -> bool:
    q = Appointment.query.filter_by(doctor_id=doctor_id, date=appt_date, time=appt_time, status="Booked")
    if exclude_appt_id:
        q = q.filter(Appointment.id != exclude_appt_id)
    return db.session.query(q.exists()).scalar()


def patient_has_conflict(patient_id: int, appt_date: str, appt_time: str, exclude_appt_id: int = None) -> bool:
    q = Appointment.query.filter_by(patient_id=patient_id, date=appt_date, time=appt_time, status="Booked")
    if exclude_appt_id:
        q = q.filter(Appointment.id != exclude_appt_id)
    return db.session.query(q.exists()).scalar()


@patient_bp.route("/me", methods=["GET"])
@jwt_required()
@role_required("patient")
def patient_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()
    if not patient:
        return jsonify({"msg": "Patient profile not found"}), 404

    return jsonify({
        "id": patient.id,
        "username": user.username,
        "name": user.name or user.username,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "address": patient.address
    })


@patient_bp.route("/me", methods=["PUT"])
@jwt_required()
@role_required("patient")
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    patient = Patient.query.filter_by(user_id=user_id).first()
    if not patient:
        return jsonify({"msg": "Patient profile not found"}), 404

    data = request.get_json() or {}
    patient.age = data.get("age", patient.age)
    patient.gender = data.get("gender", patient.gender)
    patient.phone = data.get("phone", patient.phone)
    patient.address = data.get("address", patient.address)

    if data.get("username"):
        if User.query.filter(User.username == data.get("username"), User.id != user_id).first():
            return jsonify({"msg": "username already taken"}), 409
        user.username = data.get("username")

    if data.get("name"):
        user.name = data.get("name")

    db.session.commit()
    return jsonify({"msg": "Profile updated"})


@patient_bp.route("/next-visits", methods=["GET"])
@jwt_required()
@role_required("patient")
def next_visits():
    patient = get_current_patient()
    if not patient:
        return jsonify([])

    from ..models.treatment import Treatment
    today_str = str(date.today())

    results = (
        db.session.query(Treatment, Appointment, Doctor, User)
        .join(Appointment, Treatment.appointment_id == Appointment.id)
        .join(Doctor, Appointment.doctor_id == Doctor.id)
        .join(User, Doctor.user_id == User.id)
        .filter(
            Appointment.patient_id == patient.id,
            Treatment.next_visit != None,
            Treatment.next_visit >= today_str,
        )
        .order_by(Treatment.next_visit.asc())
        .all()
    )

    out = []
    for treat, appt, doc, doc_user in results:
        if not treat.next_visit or not treat.next_visit.strip():
            continue

        # Look for any future appointment with this doctor (on or after today),
        # not the original appointment that triggered the treatment record.
        followup_appt = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id == doc.id,
            Appointment.date >= today_str,
            Appointment.id != appt.id,
        ).order_by(Appointment.date.desc()).first()

        item = {
            "next_visit": treat.next_visit,
            "doctor_name": doc_user.name or doc_user.username,
            "doctor_id": doc.id,
            "specialization": doc.specialization,
            "diagnosis": treat.diagnosis,
            "original_date": appt.date,
        }

        # Only hide the reminder if a real Booked/Completed follow-up exists.
        # A Cancelled appointment means the patient still needs to rebook.
        if followup_appt and followup_appt.status in ("Booked", "Completed"):
            continue
        else:
            item["status"] = "pending"

        out.append(item)

    return jsonify(out)


def _attach_booked_slots(docs_list):
    if not docs_list:
        return docs_list
    doc_ids = [d["doctor_id"] for d in docs_list]
    today_str = str(date.today())
    appts = Appointment.query.filter(
        Appointment.doctor_id.in_(doc_ids),
        Appointment.date >= today_str,
        Appointment.status == "Booked"
    ).all()
    booked_map = {d_id: {} for d_id in doc_ids}
    for a in appts:
        if a.date not in booked_map[a.doctor_id]:
            booked_map[a.doctor_id][a.date] = []
        booked_map[a.doctor_id][a.date].append(a.time)
    for d in docs_list:
        d["booked_slots"] = booked_map.get(d["doctor_id"], {})
    return docs_list


@patient_bp.route("/departments", methods=["GET"])
@jwt_required(optional=True)
def patient_departments():
    cache_key = "patient_departments"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached)

    depts = Department.query.all()
    out = [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "doctor_count": len(d.doctors)
        }
        for d in depts
    ]

    cache_set(cache_key, out)
    return jsonify(out)


@patient_bp.route("/departments/<int:dept_id>/doctors", methods=["GET"])
@jwt_required(optional=True)
def doctors_by_department(dept_id):
    cache_key = f"dept_doctors:{dept_id}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(_attach_booked_slots(cached))

    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"msg": "Department not found"}), 404

    out = []
    for doc in dept.doctors:
        user = User.query.get(doc.user_id)
        out.append({
            "doctor_id": doc.id,
            "name": user.name or user.username if user else "Unknown (User record missing)",
            "username": user.username if user else None,
            "specialization": doc.specialization,
            "availability": doc.availability or {}
        })

    cache_set(cache_key, out)
    return jsonify(_attach_booked_slots(out))


@patient_bp.route("/doctors/<int:doctor_id>/availability", methods=["GET"])
@jwt_required(optional=True)
def get_doctor_availability(doctor_id):
    cache_key = f"availability:{doctor_id}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify(_attach_booked_slots([cached])[0])

    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    payload = {
        "doctor_id": doc.id,
        "availability": doc.availability or {}
    }

    cache_set(cache_key, payload)
    return jsonify(_attach_booked_slots([payload])[0])


@patient_bp.route("/doctors/search", methods=["GET"])
@jwt_required(optional=True)
def search_doctors():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    results = (
        db.session.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(
            db.or_(
                User.username.ilike(f"%{q}%"),
                Doctor.specialization.ilike(f"%{q}%"),
            ),
            User.is_active == True,
        )
        .all()
    )

    out = []
    for doc, user in results:
        dept = Department.query.get(doc.department_id) if doc.department_id else None
        out.append({
            "doctor_id": doc.id,
            "name": user.name or user.username,
            "username": user.username,
            "specialization": doc.specialization,
            "department": dept.name if dept else None,
            "availability": doc.availability or {},
        })

    return jsonify(out)


@patient_bp.route("/appointments", methods=["POST"])
@jwt_required()
@role_required("patient")
def book_appointment():
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient profile not found"}), 404

    data = request.get_json() or {}
    doctor_id = data.get("doctor_id")
    appt_date = data.get("date")
    appt_time = data.get("time")

    if not doctor_id or not appt_date or not appt_time:
        return jsonify({"msg": "doctor_id, date and time are required"}), 400

    if not DATE_RE.match(appt_date) or not TIME_RE.match(appt_time):
        return jsonify({"msg": "Invalid date/time format. Use YYYY-MM-DD and HH:MM"}), 400

    try:
        appt_dt = datetime.strptime(appt_date + " " + appt_time, "%Y-%m-%d %H:%M")
    except:
        return jsonify({"msg": "Invalid date/time"}), 400

    if appt_dt < datetime.now():
        return jsonify({"msg": "Cannot book an appointment in the past"}), 400

    doc = Doctor.query.get(doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    if doc.availability:
        if not is_slot_in_availability(doc.availability, appt_date, appt_time):
            return jsonify({"msg": "Selected slot not in doctor's availability"}), 400

    if doctor_has_conflict(doctor_id, appt_date, appt_time):
        return jsonify({"msg": "Doctor already has appointment at this date/time"}), 400

    if patient_has_conflict(patient.id, appt_date, appt_time):
        return jsonify({"msg": "You already have appointment at this date/time"}), 400

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor_id,
        date=appt_date,
        time=appt_time,
        status="Booked"
    )
    db.session.add(appt)
    db.session.commit()

    if appt_date == str(date.today()):
        from ..utils.notifications import send_google_chat_message
        patient_user = User.query.get(patient.user_id)
        doc_user = User.query.get(doc.user_id)
        doctor_display_name = doc_user.name or doc_user.username if doc_user else 'your doctor'
        send_google_chat_message(
            f"*Appointment Booked - Today!*\n"
            f"Hello *{patient_user.username if patient_user else 'Patient'}*,\n"
            f"Your appointment with *Dr. {doctor_display_name}* "
            f"is confirmed for today at *{appt_time}*.\n"
            f"Please reach the hospital on time."
        )

    return jsonify({"msg": "Appointment booked", "appointment_id": appt.id}), 201


@patient_bp.route("/appointments/<int:appt_id>/cancel", methods=["PUT"])
@jwt_required()
@role_required("patient")
def cancel_appointment(appt_id):
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    appt = Appointment.query.get(appt_id)
    if not appt or appt.patient_id != patient.id:
        return jsonify({"msg": "Appointment not found"}), 404

    appt.status = "Cancelled"
    db.session.commit()

    from ..utils.notifications import send_google_chat_message
    from ..models.user import User
    from ..models.doctor import Doctor

    u = User.query.get(patient.user_id)
    doc = Doctor.query.get(appt.doctor_id)
    doc_u = User.query.get(doc.user_id) if doc else None

    msg = f"*Appointment Cancelled*\n" \
          f"Patient: *{u.username if u else 'Unknown'}*\n" \
          f"Doctor: *{doc_u.name or doc_u.username if doc_u else 'Unknown'}*\n" \
          f"Date: {appt.date} at {appt.time}"
    send_google_chat_message(msg)

    return jsonify({"msg": "Appointment cancelled"})


@patient_bp.route("/appointments/<int:appt_id>/reschedule", methods=["PUT"])
@jwt_required()
@role_required("patient")
def reschedule_appointment(appt_id):
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    appt = Appointment.query.get(appt_id)
    if not appt or appt.patient_id != patient.id:
        return jsonify({"msg": "Appointment not found"}), 404

    data = request.get_json() or {}
    new_date = data.get("date")
    new_time = data.get("time")

    if not new_date or not new_time:
        return jsonify({"msg": "date and time required"}), 400

    if not DATE_RE.match(new_date) or not TIME_RE.match(new_time):
        return jsonify({"msg": "Invalid date/time format. Use YYYY-MM-DD and HH:MM"}), 400

    try:
        new_dt = datetime.strptime(new_date + " " + new_time, "%Y-%m-%d %H:%M")
    except:
        return jsonify({"msg": "Invalid date/time"}), 400

    if new_dt < datetime.now():
        return jsonify({"msg": "Cannot reschedule to a past time"}), 400

    doc = Doctor.query.get(appt.doctor_id)
    if not doc:
        return jsonify({"msg": "Doctor not found"}), 404

    if doc.availability and not is_slot_in_availability(doc.availability, new_date, new_time):
        return jsonify({"msg": "Selected slot not in doctor's availability"}), 400

    if doctor_has_conflict(doc.id, new_date, new_time, exclude_appt_id=appt.id):
        return jsonify({"msg": "Doctor already has appointment at this date/time"}), 400

    if patient_has_conflict(patient.id, new_date, new_time, exclude_appt_id=appt.id):
        return jsonify({"msg": "You already have appointment at this date/time"}), 400

    appt.date = new_date
    appt.time = new_time
    appt.status = "Booked"
    db.session.commit()

    try:
        from ..utils.notifications import send_google_chat_message
        u = User.query.get(patient.user_id)
        doc_u = User.query.get(doc.user_id) if doc else None
        doctor_display_name = doc_u.name or doc_u.username if doc_u else 'Unknown'
        msg = f"*Appointment Rescheduled*\n" \
              f"Patient: *{u.username if u else 'Unknown'}*\n" \
              f"Doctor: *{doctor_display_name}*\n" \
              f"New Date: {new_date} at {new_time}"
        send_google_chat_message(msg)
    except Exception as e:
        print(f"[WARN] Reschedule notification failed: {e}")

    return jsonify({"msg": "Appointment rescheduled", "appointment_id": appt.id})


@patient_bp.route("/appointments/upcoming", methods=["GET"])
@jwt_required()
@role_required("patient")
def upcoming_appointments():
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    today_str = str(date.today())
    appts = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.date >= today_str,
        Appointment.status == "Booked"
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()

    out = []
    for a in appts:
        doc = Doctor.query.get(a.doctor_id)
        user = User.query.get(doc.user_id) if doc else None
        out.append({
            "appointment_id": a.id,
            "doctor_id": doc.id if doc else None,
            "doctor_name": user.name or user.username if user else None,
            "date": a.date,
            "time": a.time,
            "status": a.status
        })
    return jsonify(out)


@patient_bp.route("/appointments/history", methods=["GET"])
@jwt_required()
@role_required("patient")
def appointment_history():
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    appts = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        db.or_(
            Appointment.date < str(date.today()),
            Appointment.status.in_(["Completed", "Cancelled"])
        )
    ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()

    out = []
    for a in appts:
        doc = Doctor.query.get(a.doctor_id)
        user = User.query.get(doc.user_id) if doc else None
        treatment = Treatment.query.filter_by(appointment_id=a.id).first()
        out.append({
            "appointment_id": a.id,
            "doctor": user.name or user.username if user else None,
            "date": a.date,
            "time": a.time,
            "status": a.status,
            "treatment": {
                "diagnosis": treatment.diagnosis if treatment else None,
                "prescription": treatment.prescription if treatment else None,
                "notes": treatment.notes if treatment else None,
                "next_visit": treatment.next_visit if treatment else None
            } if treatment else None
        })
    return jsonify(out)


import os as _os

_EXPORTS_DIR = _os.path.abspath(
    _os.path.join(_os.path.dirname(__file__), "..", "..", "exports")
)


@patient_bp.route("/export_treatments", methods=["POST"])
@jwt_required()
@role_required("patient")
def export_treatments():
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    task = export_task.delay(patient.id)
    return jsonify({"msg": "Export started", "task_id": task.id}), 202


@patient_bp.route("/export_treatments/status/<task_id>", methods=["GET"])
@jwt_required()
@role_required("patient")
def export_status(task_id):
    try:
        from backend.celery_app import get_celery_app
        celery = get_celery_app()
        task_result = celery.AsyncResult(task_id)

        if task_result.state == "PENDING":
            return jsonify({"status": "pending"})
        elif task_result.state == "SUCCESS":
            result = task_result.result or {}
            return jsonify({"status": "done", "file": result.get("file", "")})
        elif task_result.state == "FAILURE":
            return jsonify({"status": "failed", "msg": str(task_result.info)}), 500
        else:
            return jsonify({"status": task_result.state.lower()})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@patient_bp.route("/export_treatments/download", methods=["GET"])
@jwt_required()
@role_required("patient")
def download_export():
    from flask import send_file
    patient = get_current_patient()
    if not patient:
        return jsonify({"msg": "Patient not found"}), 404

    filepath = _os.path.join(_EXPORTS_DIR, f"treatment_export_{patient.id}.csv")
    if not _os.path.exists(filepath):
        return jsonify({"msg": "Export file not found. Please trigger an export first."}), 404

    return send_file(
        filepath,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"treatment_history_{patient.id}.csv"
    )
