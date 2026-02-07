from datetime import datetime
from app import db


class MedicalRecord(db.Model):
    """病历模型"""
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.String(50), unique=True, nullable=False)  # 病历编号
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 就诊信息
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    chief_complaint = db.Column(db.Text)  # 主诉
    diagnosis = db.Column(db.Text)  # 诊断
    treatment_plan = db.Column(db.Text)  # 治疗方案

    # 临床特征 - 结构化存储
    tooth_number = db.Column(db.String(10))  # 牙位
    periodontal_status = db.Column(db.Enum('healthy', 'gingivitis', 'periodontitis'))
    bone_loss_percentage = db.Column(db.Integer)  # 骨吸收百分比
    mobility_degree = db.Column(db.Integer)  # 松动度 (0-3)
    caries_degree = db.Column(db.Enum('none', 'superficial', 'medium', 'deep'))
    pulp_condition = db.Column(db.Enum('vital', 'necrotic', 'pulpitis'))
    occlusion_type = db.Column(db.Enum('normal', 'deep', 'cross', 'open'))
    oral_hygiene = db.Column(db.Enum('good', 'fair', 'poor'))
    smoking_status = db.Column(db.Enum('non-smoker', 'former-smoker', 'smoker'))
    diabetic_status = db.Column(db.Boolean, default=False)

    # 影像资料
    xray_path = db.Column(db.String(255))
    ct_path = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))

    # 系统字段
    is_finalized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    clinical_features = db.relationship('ClinicalFeature', backref='medical_record', lazy=True,
                                        cascade='all, delete-orphan')
    assessment_results = db.relationship('AssessmentResult', backref='medical_record', lazy=True,
                                         cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'record_id': self.record_id,
            'patient_id': self.patient_id,
            'creator_id': self.creator_id,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'chief_complaint': self.chief_complaint,
            'diagnosis': self.diagnosis,
            'treatment_plan': self.treatment_plan,
            'tooth_number': self.tooth_number,
            'periodontal_status': self.periodontal_status,
            'bone_loss_percentage': self.bone_loss_percentage,
            'mobility_degree': self.mobility_degree,
            'caries_degree': self.caries_degree,
            'pulp_condition': self.pulp_condition,
            'occlusion_type': self.occlusion_type,
            'oral_hygiene': self.oral_hygiene,
            'smoking_status': self.smoking_status,
            'diabetic_status': self.diabetic_status,
            'xray_path': self.xray_path,
            'ct_path': self.ct_path,
            'photo_path': self.photo_path,
            'is_finalized': self.is_finalized,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'clinical_features': [cf.to_dict() for cf in self.clinical_features],
            'assessment_results': [ar.to_dict() for ar in self.assessment_results]
        }


class ClinicalFeature(db.Model):
    """临床特征模型（用于扩展特征存储）"""
    __tablename__ = 'clinical_features'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    feature_value = db.Column(db.String(255))
    feature_type = db.Column(db.Enum('numeric', 'categorical', 'text'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'feature_name': self.feature_name,
            'feature_value': self.feature_value,
            'feature_type': self.feature_type
        }