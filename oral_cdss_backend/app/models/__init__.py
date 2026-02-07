# app/models/__init__.py - 简化版本

# 只导入确认存在的基础类
from .user import User
from .patient import Patient
from .medical_record import MedicalRecord
from .rule import Rule
from .assessment_result import AssessmentResult

# 注释掉可能不存在的类
# from .medical_record import ClinicalFeature  # 如果这个类不存在，注释掉
# from .rule import RuleCategory              # 如果这个类不存在，注释掉
# from .assessment_result import TreatmentPlan # 如果这个类不存在，注释掉

__all__ = [
    'User',
    'Patient',
    'MedicalRecord',
    'Rule',
    'AssessmentResult',
    # 'ClinicalFeature',    # 暂时注释掉
    # 'RuleCategory',      # 暂时注释掉
    # 'TreatmentPlan'      # 暂时注释掉
]