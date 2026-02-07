import json
from datetime import datetime
from app import db
from app.models import Rule, RuleCategory, MedicalRecord


class RuleEngine:
    """规则引擎服务"""

    def __init__(self):
        self.rules = self.load_active_rules()

    def load_active_rules(self):
        """加载活动规则"""
        return Rule.query.filter_by(is_active=True).all()

    def evaluate_record(self, medical_record):
        """评估病历"""
        # 初始化评估结果
        total_score = 0
        category_scores = {}
        rule_evaluations = []
        mandatory_failures = []
        passed_mandatory = True

        # 按类别分组规则
        rules_by_category = {}
        for rule in self.rules:
            if rule.category_id not in rules_by_category:
                rules_by_category[rule.category_id] = []
            rules_by_category[rule.category_id].append(rule)

        # 评估每个类别的规则
        for category_id, rules in rules_by_category.items():
            category_score = 0
            category = RuleCategory.query.get(category_id)

            for rule in rules:
                # 检查规则条件
                condition_met = self.check_condition(rule, medical_record)

                if condition_met:
                    # 硬性条件检查
                    if rule.is_mandatory:
                        passed_mandatory = False
                        mandatory_failures.append({
                            'rule_id': rule.id,
                            'rule_name': rule.name,
                            'message': rule.mandatory_failure_message
                        })

                    # 计算分数
                    category_score += rule.score

                    # 记录规则评估
                    rule_evaluations.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'category': category.name,
                        'score': rule.score,
                        'condition_met': condition_met,
                        'is_mandatory': rule.is_mandatory,
                        'treatment_suggestion': rule.treatment_suggestion,
                        'risk_level': rule.risk_level
                    })

            # 应用类别权重
            weighted_score = category_score * (category.weight if category else 1.0)
            total_score += weighted_score

            category_scores[category.name if category else '未知'] = {
                'raw_score': category_score,
                'weighted_score': weighted_score,
                'weight': category.weight if category else 1.0
            }

        # 计算预估成功率
        success_probability = self.calculate_success_probability(total_score, medical_record)

        # 确定风险等级
        risk_level = self.determine_risk_level(total_score, mandatory_failures)

        return {
            'total_score': total_score,
            'success_probability': success_probability,
            'risk_level': risk_level,
            'passed_mandatory': passed_mandatory,
            'mandatory_failures': mandatory_failures,
            'category_scores': category_scores,
            'rule_evaluations': rule_evaluations
        }

    def check_condition(self, rule, medical_record):
        """检查规则条件是否满足"""
        # 获取字段值
        field_value = getattr(medical_record, rule.condition_field, None)

        if field_value is None:
            return False

        # 根据操作符检查条件
        operator = rule.condition_operator
        condition_value = rule.condition_value

        try:
            if operator == '=':
                return str(field_value) == condition_value
            elif operator == '!=':
                return str(field_value) != condition_value
            elif operator == '>':
                return float(field_value) > float(condition_value)
            elif operator == '<':
                return float(field_value) < float(condition_value)
            elif operator == '>=':
                return float(field_value) >= float(condition_value)
            elif operator == '<=':
                return float(field_value) <= float(condition_value)
            elif operator == 'in':
                values = [v.strip() for v in condition_value.split(',')]
                return str(field_value) in values
            elif operator == 'not_in':
                values = [v.strip() for v in condition_value.split(',')]
                return str(field_value) not in values
            elif operator == 'contains':
                return condition_value in str(field_value)
            else:
                return False
        except (ValueError, TypeError):
            return False

    def calculate_success_probability(self, total_score, medical_record):
        """计算预估成功率"""
        # 基础成功率基于分数
        base_probability = 50 + (total_score * 0.5)  # 每分增加0.5%

        # 根据患者因素调整
        adjustments = 0

        if medical_record.diabetic_status:
            adjustments -= 10  # 糖尿病患者成功率降低10%

        if medical_record.smoking_status == 'smoker':
            adjustments -= 15  # 吸烟者成功率降低15%

        if medical_record.oral_hygiene == 'good':
            adjustments += 5  # 口腔卫生良好提高5%

        # 确保在0-100%范围内
        probability = max(0, min(100, base_probability + adjustments))

        return round(probability, 1)

    def determine_risk_level(self, total_score, mandatory_failures):
        """确定风险等级"""
        if mandatory_failures:
            return 'high'
        elif total_score < 30:
            return 'high'
        elif total_score < 60:
            return 'medium'
        else:
            return 'low'