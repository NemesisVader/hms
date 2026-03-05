from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.auth import role_required
from ..extensions import db
from ..models.doctor import Doctor
from ..models.appointment import Appointment
from ..models.patient import Patient
from ..models.user import User
from datetime import date, timedelta

doctor_bp = Blueprint("doctor", __name__)


def get_current_doctor():
    user_id = int(get_jwt_identity())
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    return doctor


@doctor_bp.route("/availability", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_availability():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    return jsonify({
        "availability": doctor.availability or {}
    })


@doctor_bp.route("/availability", methods=["PUT"])
@jwt_required()
@role_required("doctor")
def set_availability():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    data = request.get_json() or {}
    availability = data.get("availability")

    if availability is None:
        return {"msg": "availability field is required"}, 400

    if not isinstance(availability, dict):
        return {"msg": "availability must be a JSON object (dict)"}, 400

    doctor.availability = availability
    db.session.commit()

    from ..utils.cache import cache_delete
    cache_delete(f"availability:{doctor.id}")
    cache_delete("doctors_list")
    cache_delete(f"dept_doctors:{doctor.department_id}")

    return jsonify({
        "msg": "Availability updated successfully",
        "availability": doctor.availability
    })


@doctor_bp.route("/appointments/today", methods=["GET"])
@jwt_required()
@role_required("doctor")
def doctor_today():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    today = str(date.today())

    appts = Appointment.query.filter_by(
        doctor_id=doctor.id,
        date=today
    ).all()

    data = []
    for a in appts:
        patient = Patient.query.get(a.patient_id)
        if not patient:
            data.append({
                "appointment_id": a.id,
                "patient_id": a.patient_id,
                "patient": "Unknown (Patient profile missing)",
                "date": a.date,
                "time": a.time,
                "status": a.status
            })
            continue

        user = User.query.get(patient.user_id)
        data.append({
            "appointment_id": a.id,
            "patient_id": patient.id,
            "patient": user.username if user else "Unknown (User record missing)",
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    return jsonify(data)


@doctor_bp.route("/appointments/week", methods=["GET"])
@jwt_required()
@role_required("doctor")
def doctor_week():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    start = date.today()
    end = start + timedelta(days=7)

    appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.date >= str(start),
        Appointment.date <= str(end)
    ).all()

    data = []
    for a in appts:
        patient = Patient.query.get(a.patient_id)
        if not patient:
            data.append({
                "appointment_id": a.id,
                "patient_id": a.patient_id,
                "patient": "Unknown (Patient profile missing)",
                "date": a.date,
                "time": a.time,
                "status": a.status
            })
            continue

        user = User.query.get(patient.user_id)
        data.append({
            "appointment_id": a.id,
            "patient_id": patient.id,
            "patient": user.username if user else "Unknown (User record missing)",
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    return jsonify(data)


@doctor_bp.route("/appointments", methods=["GET"])
@jwt_required()
@role_required("doctor")
def doctor_all():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    appts = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).all()

    data = []
    for a in appts:
        patient = Patient.query.get(a.patient_id)
        if not patient:
            data.append({
                "appointment_id": a.id,
                "patient_id": a.patient_id,
                "patient": "Unknown (Patient profile missing)",
                "date": a.date,
                "time": a.time,
                "status": a.status
            })
            continue

        user = User.query.get(patient.user_id)
        data.append({
            "appointment_id": a.id,
            "patient_id": patient.id,
            "patient": user.username if user else "Unknown (User record missing)",
            "date": a.date,
            "time": a.time,
            "status": a.status
        })

    return jsonify(data)


@doctor_bp.route("/appointments/<int:appt_id>/status", methods=["PUT"])
@jwt_required()
@role_required("doctor")
def doctor_update_status(appt_id):
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    appt = Appointment.query.get(appt_id)
    if not appt or appt.doctor_id != doctor.id:
        return {"msg": "Appointment not found"}, 404

    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ["Completed", "Cancelled"]:
        return {"msg": "Invalid status"}, 400

    appt.status = new_status
    db.session.commit()

    from ..utils.notifications import send_google_chat_message
    from ..models.patient import Patient
    from ..models.user import User

    patient = Patient.query.get(appt.patient_id)
    if patient:
        p_user = User.query.get(patient.user_id)
        msg = f"*Appointment Update*\n" \
              f"Hello *{p_user.username if p_user else 'Patient'}*,\n" \
              f"Your appointment with Dr. *{doctor.user.username}* has been marked as *{new_status}*."
        send_google_chat_message(msg)

    return {"msg": "Status updated successfully"}


@doctor_bp.route("/patient/<int:patient_id>/history", methods=["GET"])
@jwt_required()
@role_required("doctor")
def patient_history(patient_id):
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    patient = Patient.query.get(patient_id)
    if not patient:
        return {"msg": "Patient not found"}, 404

    patient_appts = Appointment.query.filter_by(
        patient_id=patient_id,
        doctor_id=doctor.id
    ).all()

    if not patient_appts:
        return {"msg": "Doctor not authorized to view this patient's history"}, 403

    history_data = []
    from ..models.treatment import Treatment

    for appt in patient_appts:
        treatment = Treatment.query.filter_by(appointment_id=appt.id).first()

        history_data.append({
            "appointment_id": appt.id,
            "date": appt.date,
            "time": appt.time,
            "status": appt.status,
            "treatment": {
                "id": treatment.id if treatment else None,
                "diagnosis": treatment.diagnosis if treatment else None,
                "prescription": treatment.prescription if treatment else None,
                "notes": treatment.notes if treatment else None,
                "next_visit": treatment.next_visit if treatment else None
            } if treatment else None
        })

    user = User.query.get(patient.user_id) if patient else None
    patient_name = user.username if user else "Unknown"

    return jsonify({
        "patient": {
            "id": patient.id if patient else patient_id,
            "name": patient_name,
            "age": patient.age if patient else None,
            "gender": patient.gender if patient else None,
            "phone": patient.phone if patient else None,
            "address": patient.address if patient else None
        },
        "history": history_data
    })


@doctor_bp.route("/appointments/<int:appt_id>/treatment", methods=["POST"])
@jwt_required()
@role_required("doctor")
def add_treatment(appt_id):
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    appt = Appointment.query.get(appt_id)
    if not appt or appt.doctor_id != doctor.id:
        return {"msg": "Appointment not found"}, 404

    from ..models.treatment import Treatment
    existing = Treatment.query.filter_by(appointment_id=appt_id).first()
    if existing:
        return {"msg": "Treatment record already exists for this appointment. Use PUT to update."}, 409

    data = request.get_json() or {}
    diagnosis = data.get("diagnosis", "").strip()
    prescription = data.get("prescription", "").strip()
    notes = data.get("notes", "").strip()
    next_visit = data.get("next_visit", "").strip()

    if not diagnosis or not prescription:
        return {"msg": "diagnosis and prescription are required"}, 400

    treatment = Treatment(
        appointment_id=appt_id,
        diagnosis=diagnosis,
        prescription=prescription,
        notes=notes,
        next_visit=next_visit if next_visit else None
    )

    db.session.add(treatment)

    if appt.status == "Booked":
        appt.status = "Completed"

    db.session.commit()

    from ..utils.notifications import send_google_chat_message
    from ..models.patient import Patient
    from ..models.user import User

    patient = Patient.query.get(appt.patient_id)
    if patient:
        p_user = User.query.get(patient.user_id)
        msg = f"*New Treatment Record Added*\n" \
              f"Hello *{p_user.username if p_user else 'Patient'}*,\n" \
              f"Dr. *{doctor.user.username}* has added a treatment record for your appointment on {appt.date}.\n" \
              f"Diagnosis: *{diagnosis}*.\n" \
              f"Please check your portal for full details."
        if next_visit:
            msg += f"\nFollow-up Recommendation: *{next_visit}*"

        send_google_chat_message(msg)

    return jsonify({
        "msg": "Treatment record added successfully",
        "treatment_id": treatment.id
    }), 201


@doctor_bp.route("/treatments/<int:treatment_id>", methods=["PUT"])
@jwt_required()
@role_required("doctor")
def update_treatment(treatment_id):
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    from ..models.treatment import Treatment
    treatment = Treatment.query.get(treatment_id)
    if not treatment:
        return {"msg": "Treatment record not found"}, 404

    appt = Appointment.query.get(treatment.appointment_id)
    if not appt or appt.doctor_id != doctor.id:
        return {"msg": "Unauthorized to update this treatment record"}, 403

    data = request.get_json() or {}

    if "diagnosis" in data:
        treatment.diagnosis = data["diagnosis"].strip()
    if "prescription" in data:
        treatment.prescription = data["prescription"].strip()
    if "notes" in data:
        treatment.notes = data["notes"].strip()
    if "next_visit" in data:
        treatment.next_visit = data["next_visit"].strip() if data["next_visit"] else None

    db.session.commit()

    return jsonify({
        "msg": "Treatment record updated successfully",
        "treatment": {
            "id": treatment.id,
            "diagnosis": treatment.diagnosis,
            "prescription": treatment.prescription,
            "notes": treatment.notes,
            "next_visit": treatment.next_visit
        }
    })


@doctor_bp.route("/patients", methods=["GET"])
@jwt_required()
@role_required("doctor")
def get_doctor_patients():
    doctor = get_current_doctor()
    if not doctor:
        return {"msg": "Doctor profile not found"}, 404

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patient_ids = list(set([appt.patient_id for appt in appointments]))

    patients_data = []
    for patient_id in patient_ids:
        patient = Patient.query.get(patient_id)
        if patient:
            user = User.query.get(patient.user_id)
            patients_data.append({
                "patient_id": patient.id,
                "name": user.username if user else "Unknown",
                "age": patient.age,
                "gender": patient.gender,
                "phone": patient.phone
            })

    return jsonify(patients_data)
