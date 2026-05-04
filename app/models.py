from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    """User Management for Consultants and Admins[cite: 1, 2]."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='consultant') # consultant/admin
    records = db.relationship('VerificationRecord', backref='uploader', lazy=True)

class ValidationLog(db.Model):
    """
    The 'Gatekeeper' log. 
    Tracks every upload attempt to prevent duplicate successful validations for the same State/Phase.
    """
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(100), nullable=False)
    phase = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20)) # 'Success' or 'Failure'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class VerificationRecord(db.Model):
    """
    The 'VerifiedRecords' table[cite: 2].
    Stores the final, audited figures for global export.
    """
    id = db.Column(db.Integer, primary_key=True)
    project_id_key = db.Column(db.String(255), index=True) # The 5-part key from mpr_loader[cite: 4]
    
    # Context Fields
    state_canonical = db.Column(db.String(100))
    rusa_phase = db.Column(db.String(50))
    component = db.Column(db.String(100))
    inst_name = db.Column(db.String(255))
    
    # Financial Data from UC (Audited)[cite: 1, 3]
    uc_central_appr = db.Column(db.Float)
    uc_state_appr = db.Column(db.Float)
    uc_total_appr = db.Column(db.Float)
    
    uc_central_rel = db.Column(db.Float)
    uc_state_rel = db.Column(db.Float)
    uc_total_rel = db.Column(db.Float)
    
    uc_central_util = db.Column(db.Float)
    uc_state_util = db.Column(db.Float)
    uc_total_util = db.Column(db.Float)
    
    # Metadata for Audit Trail[cite: 1]
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))