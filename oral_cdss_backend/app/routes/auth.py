from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from app.utils.validation import validate_user_data
from app.utils.response import success_response, error_response, validation_error_response
from app.utils.security import generate_token
from app.middlewares.auth_middleware import auth_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()

    # 验证数据
    errors = validate_user_data(data)
    if errors:
        return validation_error_response(errors)

    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return error_response('用户名已存在')

    if User.query.filter_by(email=data['email']).first():
        return error_response('邮箱已注册')

    try:
        # 创建用户
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data['role'],
            department=data.get('department'),
            license_number=data.get('license_number')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return success_response(
            data=user.to_dict(),
            message='注册成功'
        ), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'注册失败: {str(e)}')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('username') or not data.get('password'):
        return error_response('用户名和密码是必填项')

    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return error_response('用户名或密码错误')

    if not user.is_active:
        return error_response('用户已被禁用')

    # 生成令牌
    token = generate_token(user.id, user.role, user.username)

    return success_response({
        'token': token,
        'user': user.to_dict()
    }, '登录成功')


@auth_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """获取用户资料"""
    from flask import request

    user = User.query.get(request.user_id)
    if not user:
        return error_response('用户不存在')

    return success_response(data=user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@auth_required
def update_profile():
    """更新用户资料"""
    from flask import request

    user = User.query.get(request.user_id)
    if not user:
        return error_response('用户不存在')

    data = request.get_json()

    # 更新允许修改的字段
    allowed_fields = ['full_name', 'email', 'department']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])

    # 更新密码
    if 'password' in data and data['password']:
        user.set_password(data['password'])

    try:
        db.session.commit()
        return success_response(data=user.to_dict(), message='资料更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


@auth_bp.route('/users', methods=['GET'])
@auth_required
def get_users():
    """获取用户列表（仅管理员）"""
    from flask import request

    if request.user_role != 'admin':
        return error_response('权限不足', 403)

    # 查询参数
    role = request.args.get('role')
    search = request.args.get('search')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    # 构建查询
    query = User.query

    if role:
        query = query.filter_by(role=role)

    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.full_name.like(f'%{search}%')) |
            (User.email.like(f'%{search}%'))
        )

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    users = [user.to_dict() for user in pagination.items]

    return success_response({
        'users': users,
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page,
        'per_page': per_page
    })