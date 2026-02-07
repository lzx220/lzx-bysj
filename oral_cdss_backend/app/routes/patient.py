from flask import Blueprint, request
from app import db
from app.models import Patient
from app.utils.validation import validate_patient_data
from app.utils.response import success_response, error_response, paginated_response
from app.middlewares.auth_middleware import auth_required

patient_bp = Blueprint('patient', __name__)


@patient_bp.route('', methods=['POST'])
@auth_required
def create_patient():
    """创建患者"""
    data = request.get_json()

    # 验证数据
    errors = validate_patient_data(data)
    if errors:
        return error_response('数据验证失败', 400, errors)

    # 检查病历号是否已存在
    if Patient.query.filter_by(patient_id=data['patient_id']).first():
        return error_response('病历号已存在')

    try:
        # 创建患者
        patient = Patient(**data)
        patient.created_by = request.user_id

        # 计算年龄
        if patient.date_of_birth:
            patient.age = patient.calculate_age()

        db.session.add(patient)
        db.session.commit()

        return success_response(
            data=patient.to_dict(),
            message='患者创建成功'
        ), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建失败: {str(e)}')


@patient_bp.route('', methods=['GET'])
@auth_required
def get_patients():
    """获取患者列表"""
    # 查询参数
    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    # 构建查询
    query = Patient.query

    if active_only:
        query = query.filter_by(is_active=True)

    if search:
        query = query.filter(
            (Patient.patient_id.like(f'%{search}%')) |
            (Patient.full_name.like(f'%{search}%')) |
            (Patient.phone.like(f'%{search}%'))
        )

    # 排序
    query = query.order_by(Patient.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    patients = [patient.to_dict() for patient in pagination.items]

    return paginated_response(
        data=patients,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message='查询成功'
    )


@patient_bp.route('/<int:patient_id>', methods=['GET'])
@auth_required
def get_patient(patient_id):
    """获取单个患者"""
    patient = Patient.query.get_or_404(patient_id)
    return success_response(data=patient.to_dict())


@patient_bp.route('/<int:patient_id>', methods=['PUT'])
@auth_required
def update_patient(patient_id):
    """更新患者信息"""
    patient = Patient.query.get_or_404(patient_id)

    data = request.get_json()

    # 验证数据
    errors = validate_patient_data(data)
    if errors:
        return error_response('数据验证失败', 400, errors)

    try:
        # 更新字段
        for key, value in data.items():
            if hasattr(patient, key):
                setattr(patient, key, value)

        # 重新计算年龄
        if 'date_of_birth' in data:
            patient.age = patient.calculate_age()

        db.session.commit()
        return success_response(data=patient.to_dict(), message='更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


@patient_bp.route('/<int:patient_id>', methods=['DELETE'])
@auth_required
def delete_patient(patient_id):
    """删除患者（软删除）"""
    from flask import request

    if request.user_role != 'admin':
        return error_response('权限不足', 403)

    patient = Patient.query.get_or_404(patient_id)

    try:
        patient.is_active = False
        db.session.commit()
        return success_response(message='患者已停用')

    except Exception as e:
        db.session.rollback()
        return error_response(f'操作失败: {str(e)}')


@patient_bp.route('/<int:patient_id>/reactivate', methods=['PUT'])
@auth_required
def reactivate_patient(patient_id):
    """重新激活患者"""
    from flask import request

    if request.user_role != 'admin':
        return error_response('权限不足', 403)

    patient = Patient.query.get_or_404(patient_id)

    try:
        patient.is_active = True
        db.session.commit()
        return success_response(message='患者已重新激活')

    except Exception as e:
        db.session.rollback()
        return error_response(f'操作失败: {str(e)}')