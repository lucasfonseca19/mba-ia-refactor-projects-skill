import hashlib
import hmac
from flask import current_app
from itsdangerous import URLSafeTimedSerializer


def password_binding(user):
    secret = current_app.config['SECRET_KEY'].encode('utf-8')
    return hmac.new(secret, user.password.encode('utf-8'), hashlib.sha256).hexdigest()


def issue_token(user):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='task-auth')
    return serializer.dumps({'user_id': user.id, 'binding': password_binding(user)})


def matches_user(payload, user):
    binding = payload.get('binding')
    return isinstance(binding, str) and hmac.compare_digest(binding, password_binding(user))
