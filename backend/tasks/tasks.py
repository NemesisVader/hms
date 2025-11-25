from backend.celery_app import get_celery_app
from ..extensions import db
from ..models.appointment import Appointment
from ..models.doctor import Doctor
from ..models.patient import Patient
from ..models.user import User
from ..models.treatment import Treatment
from ..utils.notifications import send_google_chat_message
from ..utils.email_utils import send_email_with_html
from datetime import date, timedelta
import csv
import os

celery = get_celery_app()

# DAILY REMINDER TASK
@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    today_str = str(date.today())

    appts = Appointment.query.filter(Appointment.date == today_str).all()

    for appt in appts:
        patient = Patient.query.get(appt.patient_id)
        if not patient:
            continue

        user = User.query.get(patient.user_id)
        if not user:
            continue

        message = (
            f"*Hospital Appointment Reminder*\n"
            f"Hello *{user.username}*,\n"
            f"You have an appointment today at *{appt.time}*.\n"
            f"Please reach the hospital on time."
        )

        send_google_chat_message(message)

    return {"count": len(appts)}



# MONTHLY DOCTOR REPORT
@celery.task(name="tasks.send_monthly_reports")
def send_monthly_reports():
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
            continue  # Skip if no appointments

        # Generate detailed HTML report
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

        # Save HTML report to file
        os.makedirs("reports", exist_ok=True)
        report_filename = f"reports/monthly_report_{doc.id}_{last_month_end.strftime('%Y_%m')}.html"
        
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(html_report)

        # Send via email (as per requirements)
        # Assuming doctor email is username@hospital.com or stored somewhere
        # For now, we'll use a placeholder - you can add email field to User model later
        doctor_email = os.getenv(f"DOCTOR_{doc.id}_EMAIL", f"{doc_user.username}@hospital.com")
        
        email_sent = send_email_with_html(
            to_email=doctor_email,
            subject=f"Monthly Activity Report - {month_name}",
            html_content=html_report,
            attachment_path=report_filename
        )
        
        # Also send notification via Google Chat (as backup/confirmation)
        if email_sent:
            send_google_chat_message(
                f"📊 Monthly Report Sent\n"
                f"Doctor: Dr. {doc_user.username}\n"
                f"Period: {month_name}\n"
                f"Appointments: {len(appts)}\n"
                f"Email sent to: {doctor_email}"
            )
        else:
            send_google_chat_message(
                f"⚠️ Monthly Report Generated (Email Failed)\n"
                f"Doctor: Dr. {doc_user.username}\n"
                f"Period: {month_name}\n"
                f"Appointments: {len(appts)}\n"
                f"Report saved: {report_filename}\n"
                f"Note: Email not configured - check SMTP settings"
            )

        
    return "Monthly reports completed"




# CSV EXPORT
@celery.task(name="tasks.export_treatments")
def export_treatments(patient_id):
    patient = Patient.query.get(patient_id)
    user = User.query.get(patient.user_id)

    appts = Appointment.query.filter_by(patient_id=patient.id).all()

    os.makedirs("exports", exist_ok=True)
    filename = f"exports/treatment_export_{patient.id}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Doctor", "Date", "Time", "Diagnosis", "Prescription", "Notes", "Next Visit"])

        for a in appts:
            doctor = Doctor.query.get(a.doctor_id)
            duser = User.query.get(doctor.user_id)
            treat = Treatment.query.filter_by(appointment_id=a.id).first()

            writer.writerow([
                duser.username if duser else "Unknown",
                a.date,
                a.time,
                treat.diagnosis if treat else "",
                treat.prescription if treat else "",
                treat.notes if treat else "",
                treat.next_visit if treat else ""
            ])

    send_google_chat_message(
        f"CSV Export Ready for {user.username}\nFile saved at: {filename}"
    )

    return {"file": filename, "status": "done"}
