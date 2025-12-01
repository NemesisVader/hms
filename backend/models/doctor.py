from ..extensions import db
from sqlalchemy.orm import relationship

class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    availability = db.Column(db.JSON, nullable=True)

    # Relationship to User
    user = relationship("User", backref="doctor", uselist=False)

