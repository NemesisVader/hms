from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models.user import User
from ..models.patient import Patient
from ..utils.auth import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"msg": "Invalid credentials"}), 401

    if not verify_password(user.password, password):
        return jsonify({"msg": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
    })


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    age = data.get("age")
    gender = data.get("gender")
    phone = data.get("phone")
    address = data.get("address")

    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "username already exists"}), 409

    hashed = hash_password(password)
    user = User(username=username, password=hashed, role="patient")
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    # create patient profile row
    patient = Patient(user_id=user.id, age=age or 0, gender=gender or "", phone=phone, address=address)
    db.session.add(patient)
    db.session.commit()

    return jsonify({"msg": "registered", "user": {"id": user.id, "username": user.username}}), 201


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    claims = get_jwt()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"msg": "Not found"}), 404
    return jsonify({"id": user.id, "username": user.username, "role": claims.get("role")})
