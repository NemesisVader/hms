from ..extensions import db
from sqlalchemy.orm import relationship

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)

    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))

    user = relationship("User", backref="patient", uselist=False)
