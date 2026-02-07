from datetime import datetime
from app import db


class RuleCategory(db.Model):
    """规则分类模型"""
    __tablename__ = 'rule_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Float, default=1.0)  # 类别权重
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    rules = db.relationship('Rule', backref='category', lazy=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'order': self.order,
            'is_active': self.is_active,
            'rule_count': len(self.rules) if self.rules else 0
        }


class Rule(db.Model):
    """评分规则模型"""
    __tablename__ = 'rules'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('rule_categories.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # 规则条件
    condition_field = db.Column(db.String(100), nullable=False)  # 条件字段
    condition_operator = db.Column(db.Enum('=', '!=', '>', '<', '>=', '<=', 'in', 'not_in', 'contains'))
    condition_value = db.Column(db.String(255))

    # 评分设置
    score = db.Column(db.Integer, default=0)
    is_mandatory = db.Column(db.Boolean, default=False)  # 是否为硬性条件
    mandatory_failure_message = db.Column(db.Text)  # 硬性条件失败消息

    # 决策建议
    treatment_suggestion = db.Column(
        db.Enum('full_crown', 'implant', 'bridge', 'filling', 'root_canal', 'extraction', 'observation'))
    risk_level = db.Column(db.Enum('low', 'medium', 'high'))

    # 系统字段
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'condition_field': self.condition_field,
            'condition_operator': self.condition_operator,
            'condition_value': self.condition_value,
            'score': self.score,
            'is_mandatory': self.is_mandatory,
            'mandatory_failure_message': self.mandatory_failure_message,
            'treatment_suggestion': self.treatment_suggestion,
            'risk_level': self.risk_level,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }