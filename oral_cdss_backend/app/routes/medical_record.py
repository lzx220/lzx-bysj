from flask import Blueprint, request
from datetime import datetime
from app import db
from app.models import MedicalRecord, ClinicalFeature, Patient
from app.utils.validation import validate_medical_record_data
from app.utils.response import success_response, error_response, paginated_response
from app.middlewares.auth_middleware import auth_required
import random

medical_record_bp = Blueprint('medical_record', __name__)


def generate_record_id():
    """生成病历号 - 独立函数版本"""
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = str(random.randint(1000, 9999))
    return f'MR{date_str}{random_str}'


@medical_record_bp.route('', methods=['POST'])
@auth_required
def create_medical_record():
    """创建病历"""
    data = request.get_json()

    # 验证数据
    errors = validate_medical_record_data(data)
    if errors:
        return error_response('数据验证失败', 400, errors)

    # 检查患者是否存在
    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return error_response('患者不存在')

    # 生成病历号 - 使用独立函数
    record_id = generate_record_id()

    try:
        # 创建病历
        record = MedicalRecord(
            record_id=record_id,
            patient_id=data['patient_id'],
            creator_id=request.user_id,
            chief_complaint=data['chief_complaint'],
            diagnosis=data.get('diagnosis'),
            treatment_plan=data.get('treatment_plan'),
            tooth_number=data.get('tooth_number'),
            periodontal_status=data.get('periodontal_status'),
            bone_loss_percentage=data.get('bone_loss_percentage'),
            mobility_degree=data.get('mobility_degree'),
            caries_degree=data.get('caries_degree'),
            pulp_condition=data.get('pulp_condition'),
            occlusion_type=data.get('occlusion_type'),
            oral_hygiene=data.get('oral_hygiene'),
            smoking_status=data.get('smoking_status'),
            diabetic_status=data.get('diabetic_status', False)
        )

        # 处理就诊日期
        if 'visit_date' in data:
            try:
                # 兼容不同的日期格式
                visit_date = data['visit_date']
                if 'Z' in visit_date:
                    visit_date = visit_date.replace('Z', '+00:00')
                record.visit_date = datetime.fromisoformat(visit_date)
            except ValueError as e:
                return error_response(f'就诊日期格式错误: {str(e)}', 400)

        db.session.add(record)
        db.session.flush()  # 获取ID

        # 添加临床特征
        if 'clinical_features' in data:
            for feature_data in data['clinical_features']:
                feature = ClinicalFeature(
                    medical_record_id=record.id,
                    feature_name=feature_data['name'],
                    feature_value=feature_data['value'],
                    feature_type=feature_data.get('type', 'text')
                )
                db.session.add(feature)

        db.session.commit()

        return success_response(
            data=record.to_dict(),
            message='病历创建成功'
        ), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建失败: {str(e)}')


@medical_record_bp.route('', methods=['GET'])
@auth_required
def get_medical_records():
    """获取病历列表"""
    # 查询参数
    patient_id = request.args.get('patient_id')
    creator_id = request.args.get('creator_id')
    finalized = request.args.get('finalized')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    # 构建查询
    query = MedicalRecord.query

    if patient_id:
        try:
            query = query.filter_by(patient_id=int(patient_id))
        except ValueError:
            return error_response('患者ID格式错误', 400)

    if creator_id:
        try:
            query = query.filter_by(creator_id=int(creator_id))
        except ValueError:
            return error_response('创建者ID格式错误', 400)

    if finalized is not None:
        query = query.filter_by(is_finalized=finalized.lower() == 'true')

    if start_date:
        try:
            start_date_str = start_date.replace('Z', '+00:00') if 'Z' in start_date else start_date
            start_dt = datetime.fromisoformat(start_date_str)
            query = query.filter(MedicalRecord.visit_date >= start_dt)
        except ValueError:
            return error_response('开始日期格式错误', 400)

    if end_date:
        try:
            end_date_str = end_date.replace('Z', '+00:00') if 'Z' in end_date else end_date
            end_dt = datetime.fromisoformat(end_date_str)
            query = query.filter(MedicalRecord.visit_date <= end_dt)
        except ValueError:
            return error_response('结束日期格式错误', 400)

    # 排序
    query = query.order_by(MedicalRecord.visit_date.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    records = [record.to_dict() for record in pagination.items]

    return paginated_response(
        data=records,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message='查询成功'
    )


@medical_record_bp.route('/<int:record_id>', methods=['GET'])
@auth_required
def get_medical_record(record_id):
    """获取单个病历"""
    record = MedicalRecord.query.get(record_id)
    if not record:
        return error_response('病历不存在', 404)
    return success_response(data=record.to_dict())


@medical_record_bp.route('/<int:record_id>', methods=['PUT'])
@auth_required
def update_medical_record(record_id):
    """更新病历"""
    record = MedicalRecord.query.get(record_id)
    if not record:
        return error_response('病历不存在', 404)

    # 检查是否已最终化
    if record.is_finalized and request.user_role != 'admin':
        return error_response('病历已最终化，无法修改', 403)

    data = request.get_json()

    # 验证数据
    errors = validate_medical_record_data(data)
    if errors:
        return error_response('数据验证失败', 400, errors)

    try:
        # 更新字段
        update_fields = [
            'chief_complaint', 'diagnosis', 'treatment_plan',
            'tooth_number', 'periodontal_status', 'bone_loss_percentage',
            'mobility_degree', 'caries_degree', 'pulp_condition',
            'occlusion_type', 'oral_hygiene', 'smoking_status',
            'diabetic_status'
        ]

        for field in update_fields:
            if field in data:
                setattr(record, field, data[field])

        # 更新就诊日期
        if 'visit_date' in data:
            try:
                visit_date = data['visit_date']
                if 'Z' in visit_date:
                    visit_date = visit_date.replace('Z', '+00:00')
                record.visit_date = datetime.fromisoformat(visit_date)
            except ValueError as e:
                return error_response(f'就诊日期格式错误: {str(e)}', 400)

        # 更新临床特征
        if 'clinical_features' in data:
            # 删除原有特征
            ClinicalFeature.query.filter_by(medical_record_id=record.id).delete()

            # 添加新特征
            for feature_data in data['clinical_features']:
                feature = ClinicalFeature(
                    medical_record_id=record.id,
                    feature_name=feature_data['name'],
                    feature_value=feature_data['value'],
                    feature_type=feature_data.get('type', 'text')
                )
                db.session.add(feature)

        db.session.commit()
        return success_response(data=record.to_dict(), message='更新成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


@medical_record_bp.route('/<int:record_id>/finalize', methods=['PUT'])
@auth_required
def finalize_medical_record(record_id):
    """最终化病历"""
    # 从request获取用户角色 - 假设auth_required中间件已经设置
    user_role = getattr(request, 'user_role', None)

    if user_role not in ['doctor', 'admin']:
        return error_response('权限不足', 403)

    record = MedicalRecord.query.get(record_id)
    if not record:
        return error_response('病历不存在', 404)

    if record.is_finalized:
        return error_response('病历已最终化')

    try:
        record.is_finalized = True
        record.finalized_at = datetime.utcnow()
        record.finalized_by = getattr(request, 'user_id', None)
        db.session.commit()
        return success_response(data=record.to_dict(), message='病历已最终化')

    except Exception as e:
        db.session.rollback()
        return error_response(f'操作失败: {str(e)}')


@medical_record_bp.route('/<int:record_id>/features', methods=['POST'])
@auth_required
def add_clinical_feature(record_id):
    """添加临床特征"""
    record = MedicalRecord.query.get(record_id)
    if not record:
        return error_response('病历不存在', 404)

    if record.is_finalized:
        return error_response('病历已最终化，无法添加特征', 403)

    data = request.get_json()

    if not data.get('feature_name') or not data.get('feature_value'):
        return error_response('特征名称和值是必填项', 400)

    try:
        feature = ClinicalFeature(
            medical_record_id=record.id,
            feature_name=data['feature_name'],
            feature_value=data['feature_value'],
            feature_type=data.get('feature_type', 'text')
        )

        db.session.add(feature)
        db.session.commit()

        return success_response(
            data=feature.to_dict(),
            message='临床特征添加成功'
        ), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'添加失败: {str(e)}')


@medical_record_bp.route('/<int:record_id>/features/<int:feature_id>', methods=['DELETE'])
@auth_required
def delete_clinical_feature(record_id, feature_id):
    """删除临床特征"""
    record = MedicalRecord.query.get(record_id)
    if not record:
        return error_response('病历不存在', 404)

    if record.is_finalized:
        return error_response('病历已最终化，无法删除特征', 403)

    feature = ClinicalFeature.query.filter_by(
        id=feature_id,
        medical_record_id=record_id
    ).first()

    if not feature:
        return error_response('临床特征不存在', 404)

    try:
        db.session.delete(feature)
        db.session.commit()
        return success_response(message='临床特征删除成功')

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除失败: {str(e)}')


@medical_record_bp.route('/patient/<int:patient_id>', methods=['GET'])
@auth_required
def get_patient_medical_records(patient_id):
    """获取指定患者的所有病历"""
    # 检查患者是否存在
    patient = Patient.query.get(patient_id)
    if not patient:
        return error_response('患者不存在', 404)

    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    # 查询该患者的所有病历
    query = MedicalRecord.query.filter_by(patient_id=patient_id)
    query = query.order_by(MedicalRecord.visit_date.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = [record.to_dict() for record in pagination.items]

    return paginated_response(
        data=records,
        total=pagination.total,
        page=page,
        per_page=per_page,
        message='查询成功'
    )