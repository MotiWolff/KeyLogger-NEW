from datetime import datetime
import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    devices = db.relationship('Device', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Device(db.Model):
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    is_logging = db.Column(db.Boolean, default=False)
    is_encrypted = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    os_info = db.Column(db.String(100))
    hostname = db.Column(db.String(100))
    battery_level = db.Column(db.Float)
    ip_address = db.Column(db.String(45))
    
    key_logs = db.relationship('KeyLog', 
                             backref='device', 
                             lazy=True,
                             cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.device_id,
            'name': self.name,
            'is_active': self.is_active,
            'is_logging': self.is_logging,
            'is_encrypted': self.is_encrypted,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'os_info': self.os_info,
            'hostname': self.hostname,
            'battery_level': self.battery_level,
            'ip_address': self.ip_address
        }

class Keystrokes(db.Model):
    __tablename__ = 'keystrokes'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), db.ForeignKey('device.device_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref=db.backref('keystrokes', lazy=True))

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), db.ForeignKey('device.device_id', name='fk_log_device'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    device = db.relationship('Device', backref=db.backref('logs', lazy=True))

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    
class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class KeyLog(db.Model):
    __tablename__ = 'key_log'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(36), db.ForeignKey('device.device_id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    keystrokes = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'keystrokes': self.keystrokes
        }