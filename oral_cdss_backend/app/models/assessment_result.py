from datetime import datetime
from app import db


class AssessmentResult(db.Model):
    """评估结果模型"""
    __tablename__ = 'assessment_results'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)

    # 评分结果
    total_score = db.Column(db.Integer)
    success_probability = db.Column(db.Float)  # 预估成功率
    risk_level = db.Column(db.Enum('low', 'medium', 'high'))

    # 硬性条件检查
    passed_mandatory = db.Column(db.Boolean, default=True)
    mandatory_failures = db.Column(db.Text)  # JSON格式存储失败原因

    # 决策结果
    recommended_treatment = db.Column(
        db.Enum('full_crown', 'implant', 'bridge', 'filling', 'root_canal', 'extraction', 'observation'))
    confidence_level = db.Column(db.Float)  # 置信度
    alternative_treatments = db.Column(db.Text)  # JSON格式存储备选方案

    # 评估详情
    category_scores = db.Column(db.Text)  # JSON格式存储各类别得分
    rule_evaluations = db.Column(db.Text)  # JSON格式存储规则评估详情

    # 系统字段
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_latest = db.Column(db.Boolean, default=True)

    # 关系
    treatment_plans = db.relationship('TreatmentPlan', backref='assessment', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'medical_record_id': self.medical_record_id,
            'total_score': self.total_score,
            'success_probability': self.success_probability,
            'risk_level': self.risk_level,
            'passed_mandatory': self.passed_mandatory,
            'mandatory_failures': self.mandatory_failures,
            'recommended_treatment': self.recommended_treatment,
            'confidence_level': self.confidence_level,
            'alternative_treatments': self.alternative_treatments,
            'category_scores': self.category_scores,
            'rule_evaluations': self.rule_evaluations,
            'assessed_by': self.assessed_by,
            'assessed_at': self.assessed_at.isoformat() if self.assessed_at else None,
            'is_latest': self.is_latest,
            'treatment_plans': [tp.to_dict() for tp in self.treatment_plans]
        }


class TreatmentPlan(db.Model):
    """治疗方案模型"""
    __tablename__ = 'treatment_plans'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment_results.id'), nullable=False)

    # 治疗方案
    treatment_type = db.Column(
        db.Enum('full_crown', 'implant', 'bridge', 'filling', 'root_canal', 'extraction', 'observation'))
    priority = db.Column(db.Integer, default=1)  # 优先级
    description = db.Column(db.Text)

    # 预计效果
    estimated_success_rate = db.Column(db.Float)
    estimated_cost = db.Column(db.Float)
    estimated_duration = db.Column(db.String(50))  # 如：2-3周
    complexity = db.Column(db.Enum('low', 'medium', 'high'))

    # 注意事项
    contraindications = db.Column(db.Text)
    post_treatment_care = db.Column(db.Text)

    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'treatment_type': self.treatment_type,
            'priority': self.priority,
            'description': self.description,
            'estimated_success_rate': self.estimated_success_rate,
            'estimated_cost': self.estimated_cost,
            'estimated_duration': self.estimated_duration,
            'complexity': self.complexity,
            'contraindications': self.contraindications,
            'post_treatment_care': self.post_treatment_care
        }