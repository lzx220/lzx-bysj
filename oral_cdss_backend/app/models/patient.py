from datetime import datetime, date
from app import db


class Patient(db.Model):
    """患者模型"""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), unique=True, nullable=False)  # 病历号
    full_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('male', 'female', 'other'))
    date_of_birth = db.Column(db.Date)
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))

    # 医疗信息
    blood_type = db.Column(db.Enum('A', 'B', 'AB', 'O', 'unknown'))
    allergies = db.Column(db.Text)
    medical_history = db.Column(db.Text)  # 既往病史
    dental_history = db.Column(db.Text)  # 牙科病史

    # 系统字段
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')

    def calculate_age(self):
        """计算年龄"""
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year
            if today.month < self.date_of_birth.month or \
                    (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
                age -= 1
            return age
        return None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'full_name': self.full_name,
            'gender': self.gender,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age or self.calculate_age(),
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'medical_history': self.medical_history,
            'dental_history': self.dental_history,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }