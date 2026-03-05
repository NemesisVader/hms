from backend.celery_app import get_celery_app
from ..utils.notifications import send_google_chat_message
from ..utils.email_utils import send_email_with_html
from datetime import date, timedelta
import csv
import os

celery = get_celery_app()


def _get_app():
    from backend.app import create_app
    return create_app()


@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    app = _get_app()
    with app.app_context():
        from ..extensions import db
        from ..models.appointment import Appointment
        from ..models.patient import Patient
        from ..models.doctor import Doctor
        from ..models.user import User
        from ..models.treatment import Treatment

        today_str = str(date.today())

        appts = Appointment.query.filter(
            Appointment.date == today_str,
            Appointment.status == "Booked"
        ).all()

        for appt in appts:
            patient = Patient.query.get(appt.patient_id)
            if not patient:
                continue
            user = User.query.get(patient.user_id)
            if not user:
                continue
            doctor = Doctor.query.get(appt.doctor_id)
            doc_user = User.query.get(doctor.user_id) if doctor else None
            doctor_name = f"Dr. {doc_user.username}" if doc_user else "your doctor"

            send_google_chat_message(
                f"*Hospital Appointment Reminder*\n"
                f"Hello *{user.username}*,\n"
                f"You have an appointment today at *{appt.time}* with *{doctor_name}*.\n"
                f"Please reach the hospital on time."
            )

        cancelled_followups = (
            db.session.query(Treatment, Appointment, Doctor, User)
            .join(Appointment, Treatment.appointment_id == Appointment.id)
            .join(Doctor, Appointment.doctor_id == Doctor.id)
            .join(User, Doctor.user_id == User.id)
            .filter(
                Treatment.next_visit != None,
                Treatment.next_visit >= today_str,
            )
            .all()
        )

        for treat, orig_appt, doc, doc_user in cancelled_followups:
            cancelled = Appointment.query.filter(
                Appointment.patient_id == orig_appt.patient_id,
                Appointment.doctor_id == doc.id,
                Appointment.date >= treat.next_visit,
                Appointment.id != orig_appt.id,
                Appointment.status == "Cancelled"
            ).first()

            if not cancelled:
                continue

            patient = Patient.query.get(orig_appt.patient_id)
            if not patient:
                continue
            patient_user = User.query.get(patient.user_id)
            if not patient_user:
                continue

            send_google_chat_message(
                f"*Cancelled Follow-up Reminder*\n"
                f"Hello *{patient_user.username}*,\n"
                f"You had a follow-up scheduled with *Dr. {doc_user.username}* "
                f"on *{treat.next_visit}* (for: _{treat.diagnosis}_) that was cancelled.\n"
                f"Please rebook your appointment at your earliest convenience."
            )

        return {"reminders": len(appts)}


@celery.task(name="tasks.send_monthly_reports")
def send_monthly_reports():
    app = _get_app()
    with app.app_context():
        from ..extensions import db
        from ..models.appointment import Appointment
        from ..models.doctor import Doctor
        from ..models.patient import Patient
        from ..models.user import User
        from ..models.treatment import Treatment

        today = date.today()
        first_day = today.replace(day=1)
        last_month_end = first_day - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        start_str = str(last_month_start)
        end_str = str(last_month_end)
        month_name = last_month_end.strftime("%B %Y")

        doctors = Doctor.query.all()

        for doc in doctors:
            doc_user = User.query.get(doc.user_id)
            if not doc_user:
                continue

            appts = Appointment.query.filter(
                Appointment.doctor_id == doc.id,
                Appointment.date >= start_str,
                Appointment.date <= end_str,
                Appointment.status == "Completed"
            ).all()

            if not appts:
                continue

            html_report = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #3498db; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
                    .stat-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
                    .stat-label {{ color: #7f8c8d; }}
                </style>
            </head>
            <body>
                <h1>Monthly Activity Report - {month_name}</h1>
                <p><strong>Doctor:</strong> Dr. {doc_user.username}</p>

                <div class="summary">
                    <h2>Summary Statistics</h2>
                    <div class="stat">
                        <div class="stat-value">{len(appts)}</div>
                        <div class="stat-label">Total Appointments</div>
                    </div>
                </div>

                <h2>Appointment Details</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Patient</th>
                            <th>Diagnosis</th>
                            <th>Treatment</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for appt in appts:
                patient = Patient.query.get(appt.patient_id)
                patient_user = User.query.get(patient.user_id) if patient else None
                treatment = Treatment.query.filter_by(appointment_id=appt.id).first()

                html_report += f"""
                        <tr>
                            <td>{appt.date}</td>
                            <td>{appt.time}</td>
                            <td>{patient_user.username if patient_user else 'Unknown'}</td>
                            <td>{treatment.diagnosis if treatment else 'N/A'}</td>
                            <td>{treatment.prescription if treatment else 'N/A'}</td>
                        </tr>
                """

            html_report += """
                    </tbody>
                </table>
            </body>
            </html>
            """

            os.makedirs("reports", exist_ok=True)
            report_filename = f"reports/monthly_report_{doc.id}_{last_month_end.strftime('%Y_%m')}.html"

            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(html_report)

            doctor_email = os.getenv(f"DOCTOR_{doc.id}_EMAIL", f"{doc_user.username}@hospital.com")

            email_sent = send_email_with_html(
                to_email=doctor_email,
                subject=f"Monthly Activity Report - {month_name}",
                html_content=html_report,
                attachment_path=report_filename
            )

            if email_sent:
                send_google_chat_message(
                    f"Monthly Report Sent\n"
                    f"Doctor: Dr. {doc_user.username}\n"
                    f"Period: {month_name}\n"
                    f"Appointments: {len(appts)}\n"
                    f"Email sent to: {doctor_email}"
                )
            else:
                send_google_chat_message(
                    f"Monthly Report Generated (Email Failed)\n"
                    f"Doctor: Dr. {doc_user.username}\n"
                    f"Period: {month_name}\n"
                    f"Appointments: {len(appts)}\n"
                    f"Report saved: {report_filename}\n"
                    f"Note: Email not configured - check SMTP settings"
                )

        return "Monthly reports completed"


@celery.task(name="tasks.export_treatments")
def export_treatments(patient_id):
    app = _get_app()
    with app.app_context():
        from ..extensions import db
        from ..models.appointment import Appointment
        from ..models.doctor import Doctor
        from ..models.patient import Patient
        from ..models.user import User
        from ..models.treatment import Treatment

        patient = Patient.query.get(patient_id)
        if not patient:
            return {"error": "Patient not found"}

        user = User.query.get(patient.user_id)
        if not user:
            return {"error": "User not found"}

        appts = Appointment.query.filter_by(patient_id=patient.id).order_by(
            Appointment.date.desc()
        ).all()

        exports_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "exports")
        )
        os.makedirs(exports_dir, exist_ok=True)
        filename = os.path.join(exports_dir, f"treatment_export_{patient.id}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "User ID", "Username", "Consulting Doctor",
                "Appointment Date", "Appointment Time", "Status",
                "Diagnosis", "Treatment/Prescription", "Doctor Notes", "Next Visit"
            ])

            for a in appts:
                doctor = Doctor.query.get(a.doctor_id)
                duser = User.query.get(doctor.user_id) if doctor else None
                treat = Treatment.query.filter_by(appointment_id=a.id).first()

                writer.writerow([
                    user.id,
                    user.username,
                    duser.username if duser else "Unknown",
                    a.date,
                    a.time,
                    a.status,
                    treat.diagnosis if treat else "",
                    treat.prescription if treat else "",
                    treat.notes if treat else "",
                    treat.next_visit if treat else ""
                ])

        send_google_chat_message(
            f"CSV Export Ready for {user.username}\nFile: {filename}"
        )

        return {"file": filename, "status": "done"}
