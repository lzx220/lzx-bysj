from flask import jsonify

def success_response(data=None, message="操作成功", status_code=200):
    """成功响应"""
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code

def error_response(message="操作失败", status_code=400, errors=None):
    """错误响应"""
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors
    return jsonify(response), status_code

def paginated_response(data, total, page, per_page, message="查询成功"):
    """分页响应"""
    response = {
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }
    return jsonify(response), 200

def created_response(data=None, message="创建成功"):
    """创建成功响应"""
    return success_response(data, message, 201)

def not_found_response(message="资源不存在"):
    """未找到响应"""
    return error_response(message, 404)

def unauthorized_response(message="未授权访问"):
    """未授权响应"""
    return error_response(message, 401)

def forbidden_response(message="禁止访问"):
    """禁止访问响应"""
    return error_response(message, 403)

# utils/response.py - 极简版
from flask import jsonify

def success_response(data=None, message="成功"):
    return jsonify({'success': True, 'message': message, 'data': data}), 200

def error_response(message="错误", status_code=400):
    return jsonify({'success': False, 'message': message}), status_code

# 添加这个缺失的函数
def validation_error_response(errors):
    return error_response(f"验证失败: {errors}", 400)

# 其他函数（如果有需要）
def unauthorized_response(message="未授权"):
    return error_response(message, 401)

def forbidden_response(message="禁止访问"):
    return error_response(message, 403)