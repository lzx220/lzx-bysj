from datetime import datetime, date
import re
from flask import jsonify


def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """验证电话号码格式"""
    pattern = r'^[0-9]{10,11}$'
    return re.match(pattern, phone) is not None


def validate_patient_data(data):
    """验证患者数据"""
    errors = []

    # 必填字段检查
    required_fields = ['patient_id', 'full_name']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field}是必填字段")

    # 邮箱格式检查
    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            errors.append("邮箱格式不正确")

    # 电话格式检查
    if 'phone' in data and data['phone']:
        if not validate_phone(data['phone']):
            errors.append("电话号码格式不正确")

    # 出生日期检查
    if 'date_of_birth' in data and data['date_of_birth']:
        try:
            birth_date = datetime.fromisoformat(data['date_of_birth'].replace('Z', '+00:00')).date()
            if birth_date > date.today():
                errors.append("出生日期不能晚于今天")
        except ValueError:
            errors.append("出生日期格式不正确")

    # 年龄检查
    if 'age' in data and data['age']:
        try:
            age = int(data['age'])
            if age < 0 or age > 150:
                errors.append("年龄必须在0-150岁之间")
        except ValueError:
            errors.append("年龄必须是数字")

    return errors


def validate_medical_record_data(data):
    """验证病历数据"""
    errors = []

    # 必填字段检查
    required_fields = ['patient_id', 'chief_complaint']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field}是必填字段")

    # 数值范围检查
    if 'bone_loss_percentage' in data and data['bone_loss_percentage']:
        try:
            percentage = int(data['bone_loss_percentage'])
            if percentage < 0 or percentage > 100:
                errors.append("骨吸收百分比必须在0-100之间")
        except ValueError:
            errors.append("骨吸收百分比必须是数字")

    if 'mobility_degree' in data and data['mobility_degree']:
        try:
            degree = int(data['mobility_degree'])
            if degree < 0 or degree > 3:
                errors.append("松动度必须在0-3之间")
        except ValueError:
            errors.append("松动度必须是数字")

    return errors


def validate_user_data(data):
    """验证用户数据"""
    errors = []

    required_fields = ['username', 'email', 'full_name', 'role', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field}是必填字段")

    if 'email' in data and data['email']:
        if not validate_email(data['email']):
            errors.append("邮箱格式不正确")

    valid_roles = ['doctor', 'intern', 'admin']
    if 'role' in data and data['role'] not in valid_roles:
        errors.append(f"角色必须是以下之一: {', '.join(valid_roles)}")

    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            errors.append("密码长度至少6位")

    return errors


def validation_error_response(errors):
    """返回验证错误响应"""
    return jsonify({
        'success': False,
        'message': '数据验证失败',
        'errors': errors
    }), 400