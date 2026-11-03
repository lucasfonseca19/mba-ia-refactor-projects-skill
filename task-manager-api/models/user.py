from utils.time_utils import utc_now
from database import db
import hashlib
import hmac
import re
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):

        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if re.fullmatch(r'[0-9a-f]{32}', self.password or ''):
            valid = hmac.compare_digest(self.password, hashlib.md5(pwd.encode()).hexdigest())
            if valid:
                self.set_password(pwd)
            return valid
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        if self.role == 'admin':
            return True
        else:
            return False
