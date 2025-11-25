from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..models.user import User

def hash_password(plain):
    return generate_password_hash(plain)

def verify_password(hash, plain):
    return check_password_hash(hash, plain)

def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        allowed = [allowed_roles]
    else:
        allowed = list(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # ensure JWT exists & valid
            verify_jwt_in_request()
            identity = get_jwt_identity()
            if not identity:
                return jsonify({"msg": "Missing identity"}), 401

            # identity is user id or dict depending on your login. We store user id and role
            user_id = identity.get("id") if isinstance(identity, dict) else identity
            user = User.query.get(user_id)
            if not user or user.role not in allowed:
                return jsonify({"msg": "Forbidden - insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
