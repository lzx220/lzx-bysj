from flask import Blueprint, request
from datetime import datetime, timedelta
from sqlalchemy import func, case, extract
from app import db
from app.models import AssessmentResult, MedicalRecord, User, Patient
from app.utils.response import success_response, error_response
from app.middlewares.auth_middleware import auth_required
import json

visualization_bp = Blueprint('visualization', __name__)


@visualization_bp.route('/dashboard-stats', methods=['GET'])
@auth_required
def get_dashboard_statistics():
    """获取仪表盘统计数据"""

    # 总体统计
    total_patients = db.session.query(func.count(Patient.id)).filter_by(is_active=True).scalar()
    total_records = db.session.query(func.count(MedicalRecord.id)).scalar()
    total_assessments = db.session.query(func.count(AssessmentResult.id)).filter_by(is_latest=True).scalar()

    # 今日统计
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    today_patients = db.session.query(func.count(Patient.id)).filter(
        Patient.created_at >= today_start,
        Patient.created_at <= today_end
    ).scalar() or 0

    today_records = db.session.query(func.count(MedicalRecord.id)).filter(
        MedicalRecord.created_at >= today_start,
        MedicalRecord.created_at <= today_end
    ).scalar() or 0

    today_assessments = db.session.query(func.count(AssessmentResult.id)).filter(
        AssessmentResult.assessed_at >= today_start,
        AssessmentResult.assessed_at <= today_end
    ).scalar() or 0

    # 成功率统计
    success_stats = db.session.query(
        func.avg(AssessmentResult.success_probability).label('avg_success_rate'),
        func.min(AssessmentResult.success_probability).label('min_success_rate'),
        func.max(AssessmentResult.success_probability).label('max_success_rate')
    ).filter(
        AssessmentResult.is_latest == True
    ).first()

    # 风险等级分布
    risk_distribution = db.session.query(
        AssessmentResult.risk_level,
        func.count(AssessmentResult.id).label('count')
    ).filter(
        AssessmentResult.is_latest == True
    ).group_by(
        AssessmentResult.risk_level
    ).all()

    # 治疗类型分布
    treatment_distribution = db.session.query(
        AssessmentResult.recommended_treatment,
        func.count(AssessmentResult.id).label('count')
    ).filter(
        AssessmentResult.is_latest == True,
        AssessmentResult.recommended_treatment.isnot(None)
    ).group_by(
        AssessmentResult.recommended_treatment
    ).all()

    return success_response({
        'overall': {
            'total_patients': total_patients,
            'total_records': total_records,
            'total_assessments': total_assessments
        },
        'today': {
            'new_patients': today_patients,
            'new_records': today_records,
            'new_assessments': today_assessments
        },
        'success_rates': {
            'average': float(success_stats.avg_success_rate or 0),
            'minimum': float(success_stats.min_success_rate or 0),
            'maximum': float(success_stats.max_success_rate or 0)
        },
        'risk_distribution': {
            item.risk_level: item.count for item in risk_distribution
        },
        'treatment_distribution': {
            item.recommended_treatment: item.count for item in treatment_distribution
        }
    }, '查询成功')


@visualization_bp.route('/success-chart', methods=['GET'])
@auth_required
def get_success_chart_data():
    """获取成功率图表数据"""
    # 时间范围参数
    days = int(request.args.get('days', 30))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 按日期分组统计
    daily_stats = db.session.query(
        func.date(AssessmentResult.assessed_at).label('date'),
        func.count(AssessmentResult.id).label('count'),
        func.avg(AssessmentResult.success_probability).label('avg_success'),
        func.avg(AssessmentResult.total_score).label('avg_score')
    ).filter(
        AssessmentResult.is_latest == True,
        AssessmentResult.assessed_at >= start_date,
        AssessmentResult.assessed_at <= end_date
    ).group_by(
        func.date(AssessmentResult.assessed_at)
    ).order_by(
        func.date(AssessmentResult.assessed_at)
    ).all()

    dates = []
    counts = []
    success_rates = []
    scores = []

    for stat in daily_stats:
        dates.append(stat.date.isoformat())
        counts.append(stat.count)
        success_rates.append(float(stat.avg_success or 0))
        scores.append(float(stat.avg_score or 0))

    return success_response({
        'dates': dates,
        'counts': counts,
        'success_rates': success_rates,
        'scores': scores
    }, '查询成功')


@visualization_bp.route('/radar-chart/<int:record_id>', methods=['GET'])
@auth_required
def get_radar_chart_data(record_id):
    """获取雷达图数据"""
    assessment = AssessmentResult.query.filter_by(
        medical_record_id=record_id,
        is_latest=True
    ).first()

    if not assessment:
        return error_response('未找到评估结果', 404)

    try:
        # 检查是否有category_scores字段
        if not hasattr(assessment, 'category_scores'):
            return error_response('评估结果格式错误', 400)

        # 解析JSON数据
        if isinstance(assessment.category_scores, str):
            category_scores = json.loads(assessment.category_scores)
        else:
            category_scores = assessment.category_scores or {}

        categories = []
        scores = []
        max_scores = []

        for category, data in category_scores.items():
            categories.append(category)
            # 确保数据格式正确
            if isinstance(data, dict) and 'weighted_score' in data:
                scores.append(abs(float(data['weighted_score'])))
            elif isinstance(data, (int, float)):
                scores.append(abs(float(data)))
            else:
                scores.append(0)
            max_scores.append(30)  # 假设每类别最大分30

        # 计算总体得分
        total_max = sum(max_scores) if max_scores else 100
        total_score = float(assessment.total_score) if assessment.total_score else 0

        return success_response({
            'categories': categories,
            'scores': scores,
            'max_scores': max_scores,
            'total_score': total_score,
            'total_max': total_max,
            'success_probability': float(assessment.success_probability) if assessment.success_probability else 0,
            'risk_level': assessment.risk_level or 'unknown'
        }, '查询成功')

    except (json.JSONDecodeError, ValueError) as e:
        return error_response(f'数据处理失败: {str(e)}', 400)


@visualization_bp.route('/doctor-stats', methods=['GET'])
@auth_required
def get_doctor_statistics():
    """获取医生工作统计"""
    # 按医生统计
    doctor_stats = db.session.query(
        User.id,
        User.full_name,
        func.count(MedicalRecord.id).label('record_count'),
        func.avg(AssessmentResult.success_probability).label('avg_success_rate'),
        func.count(func.distinct(Patient.id)).label('patient_count')
    ).join(
        MedicalRecord, MedicalRecord.creator_id == User.id
    ).join(
        AssessmentResult, AssessmentResult.medical_record_id == MedicalRecord.id
    ).join(
        Patient, Patient.id == MedicalRecord.patient_id
    ).filter(
        User.role.in_(['doctor', 'intern']),
        AssessmentResult.is_latest == True
    ).group_by(
        User.id
    ).order_by(
        func.count(MedicalRecord.id).desc()
    ).all()

    statistics = []
    for stat in doctor_stats:
        statistics.append({
            'doctor_id': stat.id,
            'doctor_name': stat.full_name,
            'record_count': stat.record_count or 0,
            'average_success_rate': float(stat.avg_success_rate or 0),
            'patient_count': stat.patient_count or 0
        })

    return success_response({
        'doctor_statistics': statistics
    }, '查询成功')


@visualization_bp.route('/treatment-comparison', methods=['GET'])
@auth_required
def get_treatment_comparison():
    """获取治疗方案对比数据"""
    treatments = ['full_crown', 'implant', 'bridge', 'filling', 'root_canal', 'extraction']

    comparison_data = []

    for treatment in treatments:
        stats = db.session.query(
            func.count(AssessmentResult.id).label('count'),
            func.avg(AssessmentResult.success_probability).label('avg_success'),
            func.avg(AssessmentResult.total_score).label('avg_score'),
            func.avg(
                case(
                    [(AssessmentResult.risk_level == 'high', 1)],
                    else_=0
                )
            ).label('high_risk_rate')
        ).filter(
            AssessmentResult.recommended_treatment == treatment,
            AssessmentResult.is_latest == True
        ).first()

        comparison_data.append({
            'treatment': treatment,
            'count': stats.count or 0,
            'average_success_rate': float(stats.avg_success or 0),
            'average_score': float(stats.avg_score or 0),
            'high_risk_rate': float(stats.high_risk_rate or 0) * 100
        })

    return success_response({
        'comparison': comparison_data
    }, '查询成功')


@visualization_bp.route('/risk-trend', methods=['GET'])
@auth_required
def get_risk_trend():
    """获取风险趋势数据"""
    # 时间范围参数
    days = int(request.args.get('days', 90))
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 按周统计风险趋势
    weekly_stats = db.session.query(
        func.year(AssessmentResult.assessed_at).label('year'),
        func.week(AssessmentResult.assessed_at).label('week'),
        func.count(AssessmentResult.id).label('total_count'),
        func.sum(case([(AssessmentResult.risk_level == 'high', 1)], else_=0)).label('high_risk_count'),
        func.sum(case([(AssessmentResult.risk_level == 'medium', 1)], else_=0)).label('medium_risk_count'),
        func.sum(case([(AssessmentResult.risk_level == 'low', 1)], else_=0)).label('low_risk_count'),
        func.avg(AssessmentResult.success_probability).label('avg_success')
    ).filter(
        AssessmentResult.is_latest == True,
        AssessmentResult.assessed_at >= start_date,
        AssessmentResult.assessed_at <= end_date
    ).group_by(
        func.year(AssessmentResult.assessed_at),
        func.week(AssessmentResult.assessed_at)
    ).order_by(
        func.year(AssessmentResult.assessed_at),
        func.week(AssessmentResult.assessed_at)
    ).all()

    weeks = []
    high_risk_percentages = []
    medium_risk_percentages = []
    low_risk_percentages = []
    avg_success_rates = []

    for stat in weekly_stats:
        week_label = f"{stat.year}-W{str(stat.week).zfill(2)}"
        weeks.append(week_label)

        total = stat.total_count or 1
        high_risk_percentages.append((stat.high_risk_count or 0) / total * 100)
        medium_risk_percentages.append((stat.medium_risk_count or 0) / total * 100)
        low_risk_percentages.append((stat.low_risk_count or 0) / total * 100)
        avg_success_rates.append(float(stat.avg_success or 0))

    return success_response({
        'weeks': weeks,
        'high_risk_percentages': high_risk_percentages,
        'medium_risk_percentages': medium_risk_percentages,
        'low_risk_percentages': low_risk_percentages,
        'avg_success_rates': avg_success_rates
    }, '查询成功')


@visualization_bp.route('/patient-age-distribution', methods=['GET'])
@auth_required
def get_patient_age_distribution():
    """获取患者年龄分布"""
    # 获取所有活跃患者的年龄信息
    patients = Patient.query.filter_by(is_active=True).all()

    age_distribution = {
        'under_20': 0,
        '20_29': 0,
        '30_39': 0,
        '40_49': 0,
        '50_59': 0,
        '60_plus': 0
    }

    for patient in patients:
        if patient.date_of_birth:
            age = calculate_age(patient.date_of_birth)
            if age < 20:
                age_distribution['under_20'] += 1
            elif 20 <= age < 30:
                age_distribution['20_29'] += 1
            elif 30 <= age < 40:
                age_distribution['30_39'] += 1
            elif 40 <= age < 50:
                age_distribution['40_49'] += 1
            elif 50 <= age < 60:
                age_distribution['50_59'] += 1
            else:
                age_distribution['60_plus'] += 1

    return success_response({
        'age_distribution': age_distribution
    }, '查询成功')


@visualization_bp.route('/top-treatments/<int:patient_id>', methods=['GET'])
@auth_required
def get_patient_top_treatments(patient_id):
    """获取患者最常见治疗方案"""
    # 检查患者是否存在
    patient = Patient.query.get(patient_id)
    if not patient:
        return error_response('患者不存在', 404)

    # 获取患者的所有评估结果
    patient_treatments = db.session.query(
        AssessmentResult.recommended_treatment,
        func.count(AssessmentResult.id).label('count'),
        func.avg(AssessmentResult.success_probability).label('avg_success')
    ).join(
        MedicalRecord, MedicalRecord.id == AssessmentResult.medical_record_id
    ).filter(
        MedicalRecord.patient_id == patient_id,
        AssessmentResult.is_latest == True,
        AssessmentResult.recommended_treatment.isnot(None)
    ).group_by(
        AssessmentResult.recommended_treatment
    ).order_by(
        func.count(AssessmentResult.id).desc()
    ).limit(5).all()

    treatments = []
    for treatment in patient_treatments:
        treatments.append({
            'treatment': treatment.recommended_treatment,
            'count': treatment.count,
            'average_success_rate': float(treatment.avg_success or 0)
        })

    return success_response({
        'patient_id': patient_id,
        'top_treatments': treatments
    }, '查询成功')


def calculate_age(birth_date):
    """计算年龄"""
    today = datetime.now().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))