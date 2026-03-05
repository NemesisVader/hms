from ..extensions import db

class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)

    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    next_visit = db.Column(db.String(20))

    appointment = db.relationship("Appointment", backref="treatment")