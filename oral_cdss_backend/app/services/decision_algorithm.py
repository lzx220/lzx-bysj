import json
from app.services.rule_engine import RuleEngine
from app.models import TreatmentPlan


class DecisionAlgorithm:
    """决策算法服务"""

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.treatment_options = {
            'full_crown': {
                'name': '全冠修复',
                'description': '适用于牙体缺损较大但牙根完好的牙齿',
                'min_score': 60,
                'success_rate': 85,
                'cost': 2000,
                'duration': '2周'
            },
            'implant': {
                'name': '种植修复',
                'description': '适用于牙齿缺失或无法保留的情况',
                'min_score': 70,
                'success_rate': 95,
                'cost': 8000,
                'duration': '3-6个月'
            },
            'bridge': {
                'name': '固定桥修复',
                'description': '适用于缺失1-2颗牙且邻牙健康的情况',
                'min_score': 50,
                'success_rate': 80,
                'cost': 5000,
                'duration': '3周'
            },
            'filling': {
                'name': '充填修复',
                'description': '适用于龋齿或小范围牙体缺损',
                'min_score': 40,
                'success_rate': 90,
                'cost': 500,
                'duration': '1次就诊'
            },
            'root_canal': {
                'name': '根管治疗',
                'description': '适用于牙髓病变或感染的情况',
                'min_score': 30,
                'success_rate': 85,
                'cost': 1500,
                'duration': '2-3次就诊'
            },
            'extraction': {
                'name': '拔牙',
                'description': '适用于无法保留的牙齿',
                'min_score': 0,
                'success_rate': 100,
                'cost': 300,
                'duration': '1次就诊'
            },
            'observation': {
                'name': '观察随访',
                'description': '适用于轻微问题或需要进一步检查的情况',
                'min_score': 0,
                'success_rate': 100,
                'cost': 0,
                'duration': '定期复查'
            }
        }

    def generate_recommendation(self, medical_record):
        """生成治疗建议"""
        # 第一步：规则引擎评估
        evaluation = self.rule_engine.evaluate_record(medical_record)

        if not evaluation['passed_mandatory']:
            # 硬性条件未通过，建议拔牙或根管治疗
            return self.handle_mandatory_failure(evaluation, medical_record)

        # 第二步：基于评分选择治疗方案
        total_score = evaluation['total_score']
        risk_level = evaluation['risk_level']

        # 收集规则建议
        rule_suggestions = {}
        for eval_item in evaluation['rule_evaluations']:
            if eval_item['treatment_suggestion']:
                treatment = eval_item['treatment_suggestion']
                if treatment not in rule_suggestions:
                    rule_suggestions[treatment] = 0
                rule_suggestions[treatment] += 1

        # 第三步：综合决策
        recommended_treatment = self.select_treatment(
            total_score, risk_level, rule_suggestions, medical_record
        )

        # 第四步：生成备选方案
        alternative_treatments = self.generate_alternatives(
            recommended_treatment, total_score, risk_level
        )

        # 第五步：生成治疗方案详情
        treatment_plans = self.generate_treatment_plans(
            recommended_treatment, alternative_treatments, evaluation, medical_record
        )

        return {
            'evaluation': evaluation,
            'recommended_treatment': recommended_treatment,
            'confidence_level': self.calculate_confidence(evaluation, medical_record),
            'alternative_treatments': alternative_treatments,
            'treatment_plans': treatment_plans
        }

    def handle_mandatory_failure(self, evaluation, medical_record):
        """处理硬性条件失败情况"""
        failures = evaluation['mandatory_failures']

        # 检查是否有牙髓坏死的硬性条件
        for failure in failures:
            if '牙髓坏死' in failure.get('message', ''):
                return {
                    'evaluation': evaluation,
                    'recommended_treatment': 'root_canal',
                    'confidence_level': 0.9,
                    'alternative_treatments': ['extraction', 'observation'],
                    'treatment_plans': [
                        {
                            'treatment_type': 'root_canal',
                            'priority': 1,
                            'description': '必须先进行根管治疗解决牙髓坏死问题',
                            'estimated_success_rate': 85,
                            'estimated_cost': 1500,
                            'estimated_duration': '2-3次就诊',
                            'complexity': 'medium',
                            'contraindications': '全身健康状况不佳者慎用',
                            'post_treatment_care': '避免用患牙咀嚼硬物，定期复查'
                        }
                    ]
                }

        # 默认建议拔牙
        return {
            'evaluation': evaluation,
            'recommended_treatment': 'extraction',
            'confidence_level': 0.8,
            'alternative_treatments': ['observation'],
            'treatment_plans': [
                {
                    'treatment_type': 'extraction',
                    'priority': 1,
                    'description': '牙齿因硬性条件不满足而无法保留，建议拔除',
                    'estimated_success_rate': 100,
                    'estimated_cost': 300,
                    'estimated_duration': '1次就诊',
                    'complexity': 'low',
                    'contraindications': '急性炎症期、血液病患者慎用',
                    'post_treatment_care': '咬紧棉球30分钟，24小时内不刷牙漱口'
                }
            ]
        }

    def select_treatment(self, total_score, risk_level, rule_suggestions, medical_record):
        """选择治疗方案"""
        # 如果有明确的规则建议，优先考虑
        if rule_suggestions:
            # 选择出现次数最多的建议
            most_common = max(rule_suggestions.items(), key=lambda x: x[1])[0]
            return most_common

        # 基于分数选择
        if total_score >= 70:
            return 'full_crown' if medical_record.bone_loss_percentage < 30 else 'implant'
        elif total_score >= 50:
            return 'bridge' if self.check_adjacent_teeth(medical_record) else 'full_crown'
        elif total_score >= 30:
            return 'filling' if medical_record.caries_degree in ['superficial', 'medium'] else 'root_canal'
        else:
            return 'extraction'

    def check_adjacent_teeth(self, medical_record):
        """检查邻牙状况（简化版本）"""
        # 在实际应用中，这里应该检查邻牙的详细状况
        return True  # 假设邻牙健康

    def generate_alternatives(self, primary_treatment, total_score, risk_level):
        """生成备选方案"""
        alternatives = []

        if primary_treatment == 'implant':
            alternatives = ['bridge', 'full_crown', 'observation']
        elif primary_treatment == 'full_crown':
            alternatives = ['bridge', 'filling', 'observation']
        elif primary_treatment == 'bridge':
            alternatives = ['implant', 'full_crown', 'observation']
        elif primary_treatment == 'filling':
            alternatives = ['root_canal', 'observation']
        elif primary_treatment == 'root_canal':
            alternatives = ['extraction', 'observation']
        elif primary_treatment == 'extraction':
            alternatives = ['observation']
        else:
            alternatives = ['filling', 'root_canal']

        # 根据分数过滤
        filtered = []
        for alt in alternatives:
            if alt in self.treatment_options:
                min_score = self.treatment_options[alt]['min_score']
                if total_score >= min_score or alt == 'observation':
                    filtered.append(alt)

        return filtered[:3]  # 返回最多3个备选方案

    def generate_treatment_plans(self, primary_treatment, alternatives, evaluation, medical_record):
        """生成治疗方案详情"""
        plans = []

        # 主要治疗方案
        primary_plan = self.create_treatment_plan(
            primary_treatment, 1, evaluation, medical_record
        )
        plans.append(primary_plan)

        # 备选治疗方案
        for i, alt_treatment in enumerate(alternatives[:2], start=2):
            alt_plan = self.create_treatment_plan(
                alt_treatment, i, evaluation, medical_record
            )
            plans.append(alt_plan)

        return plans

    def create_treatment_plan(self, treatment_type, priority, evaluation, medical_record):
        """创建单个治疗方案"""
        treatment_info = self.treatment_options.get(treatment_type, {})

        # 调整成功率
        base_success_rate = treatment_info.get('success_rate', 80)
        adjusted_rate = self.adjust_success_rate(
            base_success_rate, evaluation, medical_record
        )

        return {
            'treatment_type': treatment_type,
            'priority': priority,
            'description': treatment_info.get('description', ''),
            'estimated_success_rate': adjusted_rate,
            'estimated_cost': treatment_info.get('cost', 0),
            'estimated_duration': treatment_info.get('duration', ''),
            'complexity': self.determine_complexity(treatment_type, medical_record),
            'contraindications': self.get_contraindications(treatment_type, medical_record),
            'post_treatment_care': self.get_post_treatment_care(treatment_type)
        }

    def adjust_success_rate(self, base_rate, evaluation, medical_record):
        """根据具体情况调整成功率"""
        adjusted = base_rate

        # 根据风险等级调整
        risk_level = evaluation['risk_level']
        if risk_level == 'high':
            adjusted -= 15
        elif risk_level == 'medium':
            adjusted -= 5

        # 根据患者因素调整
        if medical_record.diabetic_status:
            adjusted -= 10

        if medical_record.smoking_status == 'smoker':
            adjusted -= 15

        if medical_record.oral_hygiene == 'good':
            adjusted += 5
        elif medical_record.oral_hygiene == 'poor':
            adjusted -= 10

        # 确保在合理范围内
        return max(0, min(100, adjusted))

    def determine_complexity(self, treatment_type, medical_record):
        """确定治疗复杂性"""
        if treatment_type in ['implant', 'bridge']:
            return 'high'
        elif treatment_type in ['full_crown', 'root_canal']:
            return 'medium'
        else:
            return 'low'

    def get_contraindications(self, treatment_type, medical_record):
        """获取禁忌症"""
        contraindications = []

        if medical_record.diabetic_status and treatment_type in ['implant', 'extraction']:
            contraindications.append('糖尿病患者需控制血糖稳定后方可进行')

        if medical_record.smoking_status == 'smoker' and treatment_type == 'implant':
            contraindications.append('吸烟者种植体失败风险增加，建议戒烟')

        if medical_record.periodontal_status == 'periodontitis' and treatment_type == 'full_crown':
            contraindications.append('需先控制牙周炎症')

        return '；'.join(contraindications) if contraindications else '无明显禁忌症'

    def get_post_treatment_care(self, treatment_type):
        """获取术后护理建议"""
        care_instructions = {
            'implant': '术后24小时内冰敷，避免剧烈运动，保持口腔卫生，定期复查',
            'full_crown': '避免用修复牙咀嚼硬物，注意口腔卫生，定期检查',
            'bridge': '注意桥体清洁，使用牙线清洁器，避免咀嚼过硬食物',
            'filling': '避免过硬食物，如有不适及时复诊',
            'root_canal': '避免用患牙咀嚼，按时复诊完成冠部修复',
            'extraction': '咬紧棉球30分钟，24小时内不刷牙漱口，避免辛辣食物',
            'observation': '保持良好的口腔卫生，定期复查'
        }
        return care_instructions.get(treatment_type, '请遵循医生指导')

    def calculate_confidence(self, evaluation, medical_record):
        """计算置信度"""
        confidence = 0.7  # 基础置信度

        # 基于评分分布的置信度
        category_scores = evaluation.get('category_scores', {})
        if len(category_scores) >= 3:
            confidence += 0.1

        # 基于数据完整性的置信度
        completeness = self.calculate_data_completeness(medical_record)
        confidence += completeness * 0.2

        # 确保在0-1范围内
        return max(0, min(1, confidence))

    def calculate_data_completeness(self, medical_record):
        """计算数据完整性"""
        required_fields = [
            'chief_complaint', 'diagnosis', 'periodontal_status',
            'bone_loss_percentage', 'mobility_degree', 'caries_degree'
        ]

        filled_count = 0
        for field in required_fields:
            if getattr(medical_record, field, None) not in [None, '']:
                filled_count += 1

        return filled_count / len(required_fields)