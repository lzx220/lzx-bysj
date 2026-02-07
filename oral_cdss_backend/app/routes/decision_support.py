from flask import Blueprint, request
from app import db
from app.models import MedicalRecord, AssessmentResult, TreatmentPlan, Rule, RuleCategory
from app.services.decision_algorithm import DecisionAlgorithm
from app.utils.response import success_response, error_response
from app.middlewares.auth_middleware import auth_required

decision_support_bp = Blueprint('decision_support', __name__)
decision_algorithm = DecisionAlgorithm()


@decision_support_bp.route('/assess/<int:record_id>', methods=['POST'])
@auth_required
def assess_medical_record(record_id):
    """评估病历并提供决策支持"""
    record = MedicalRecord.query.get_or_404(record_id)

    try:
        # 使用决策算法生成建议
        recommendation = decision_algorithm.generate_recommendation(record)

        # 保存评估结果到数据库
        assessment = AssessmentResult(
            medical_record_id=record.id,
            total_score=recommendation['evaluation']['total_score'],
            success_probability=recommendation['evaluation']['success_probability'],
            risk_level=recommendation['evaluation']['risk_level'],
            passed_mandatory=recommendation['evaluation']['passed_mandatory'],
            mandatory_failures=str(recommendation['evaluation']['mandatory_failures']),
            recommended_treatment=recommendation['recommended_treatment'],
            confidence_level=recommendation['confidence_level'],
            alternative_treatments=str(recommendation['alternative_treatments']),
            category_scores=str(recommendation['evaluation']['category_scores']),
            rule_evaluations=str(recommendation['evaluation']['rule_evaluations']),
            assessed_by=request.user_id,
            is_latest=True
        )

        # 将旧的评估结果标记为非最新
        AssessmentResult.query.filter_by(
            medical_record_id=record.id,
            is_latest=True
        ).update({'is_latest': False})

        db.session.add(assessment)
        db.session.flush()  # 获取ID

        # 保存治疗方案
        for plan_data in recommendation['treatment_plans']:
            plan = TreatmentPlan(
                assessment_id=assessment.id,
                treatment_type=plan_data['treatment_type'],
                priority=plan_data['priority'],
                description=plan_data['description'],
                estimated_success_rate=plan_data['estimated_success_rate'],
                estimated_cost=plan_data['estimated_cost'],
                estimated_duration=plan_data['estimated_duration'],
                complexity=plan_data['complexity'],
                contraindications=plan_data['contraindications'],
                post_treatment_care=plan_data['post_treatment_care']
            )
            db.session.add(plan)

        db.session.commit()

        return success_response({
            'assessment': assessment.to_dict(),
            'recommendation': recommendation
        }, '评估完成')

    except Exception as e:
        db.session.rollback()
        return error_response(f'评估失败: {str(e)}')


@decision_support_bp.route('/assessments/<int:record_id>', methods=['GET'])
@auth_required
def get_assessments(record_id):
    """获取病历的评估历史"""
    record = MedicalRecord.query.get_or_404(record_id)

    assessments = AssessmentResult.query.filter_by(
        medical_record_id=record.id
    ).order_by(
        AssessmentResult.assessed_at.desc()
    ).all()

    return success_response(
        data=[assessment.to_dict() for assessment in assessments],
        message='查询成功'
    )


@decision_support_bp.route('/rules', methods=['GET'])
@auth_required
def get_rules():
    """获取评分规则"""
    # 查询参数
    category_id = request.args.get('category_id')
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    # 构建查询
    query = Rule.query

    if category_id:
        query = query.filter_by(category_id=int(category_id))

    if active_only:
        query = query.filter_by(is_active=True)

    # 排序
    query = query.order_by(Rule.category_id, Rule.id)

    rules = [rule.to_dict() for rule in query.all()]

    return success_response(data=rules, message='查询成功')


@decision_support_bp.route('/rule-categories', methods=['GET'])
@auth_required
def get_rule_categories():
    """获取规则分类"""
    categories = RuleCategory.query.filter_by(is_active=True).order_by(RuleCategory.order).all()

    return success_response(
        data=[category.to_dict() for category in categories],
        message='查询成功'
    )


@decision_support_bp.route('/rules', methods=['POST'])
@auth_required
def create_rule():
    """创建评分规则（仅管理员）"""
    from flask import request

    if request.user_role != 'admin':
        return error_response('权限不足', 403)

    data = request.get_json()

    # 验证必填字段
    required_fields = ['category_id', 'name', 'condition_field', 'condition_operator']
    for field in required_fields:
        if field not in data:
            return error_response(f'{field}是必填字段')

    try:
        rule = Rule(
            category_id=data['category_id'],
            name=data['name'],
            description=data.get('description'),
            condition_field=data['condition_field'],
            condition_operator=data['condition_operator'],
            condition_value=data.get('condition_value'),
            score=data.get('score', 0),
            is_mandatory=data.get('is_mandatory', False),
            mandatory_failure_message=data.get('mandatory_failure_message'),
            treatment_suggestion=data.get('treatment_suggestion'),
            risk_level=data.get('risk_level'),
            created_by=request.user_id
        )

        db.session.add(rule)
        db.session.commit()

        return success_response(
            data=rule.to_dict(),
            message='规则创建成功'
        ), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建失败: {str(e)}')


@decision_support_bp.route('/simulate', methods=['POST'])
@auth_required
def simulate_assessment():
    """模拟评估（不保存结果）"""
    data = request.get_json()

    try:
        # 创建临时病历对象
        from app.models import MedicalRecord

        temp_record = MedicalRecord()
        for key, value in data.items():
            if hasattr(temp_record, key):
                setattr(temp_record, key, value)

        # 使用决策算法生成建议
        recommendation = decision_algorithm.generate_recommendation(temp_record)

        return success_response({
            'recommendation': recommendation
        }, '模拟评估完成')

    except Exception as e:
        return error_response(f'模拟评估失败: {str(e)}')