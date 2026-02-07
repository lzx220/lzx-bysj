# app/routes/__init__.py
from flask import Blueprint, jsonify, request
from app import db
from app.models.user import User
from datetime import datetime
import traceback
from sqlalchemy import text

# ==================== 创建蓝图 ====================
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)


# ==================== 主路由 ====================
@main_bp.route('/')
def index():
    return jsonify({
        'message': '口腔CDSS系统运行正常！',
        'version': '1.0.0',
        'status': 'healthy',
        'endpoints': {
            '健康检查': '/api/health',
            '登录': '/api/auth/login',
            '注册': '/api/auth/register',
            '获取用户信息': '/api/auth/me',
            '测试连接': '/api/test'
        }
    })


@main_bp.route('/api/health', methods=['GET'])
def health_check():
    try:
        # 修复：使用text()包装SQL表达式
        db.session.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'message': '口腔CDSS系统运行正常',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'service': 'oral-cdss-backend'
    })


@main_bp.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'success',
        'message': 'API测试成功',
        'timestamp': datetime.now().isoformat()
    })


# ==================== 认证路由 ====================
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # 处理预检请求
        return '', 200

    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400

        # 查找用户
        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 401

        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': '密码错误'
            }), 401

        # 检查用户是否激活
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': '用户已被禁用，请联系管理员'
            }), 403

        # 登录成功
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': f'token-{user.id}-{datetime.now().timestamp()}',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        print(f"登录错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500


@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        # 处理预检请求
        return '', 200

    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        username = data.get('username')
        password = data.get('password')
        user_type = data.get('userType')  # doctor, admin

        # 验证必填字段
        if not username:
            return jsonify({
                'success': False,
                'message': '用户名不能为空'
            }), 400

        if not password:
            return jsonify({
                'success': False,
                'message': '密码不能为空'
            }), 400

        if not user_type:
            return jsonify({
                'success': False,
                'message': '用户类型不能为空'
            }), 400

        if user_type not in ['doctor', 'admin']:
            return jsonify({
                'success': False,
                'message': '用户类型必须是doctor或admin'
            }), 400

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 409

        # 创建新用户
        email = data.get('email', f'{username}@oralcdss.com')
        full_name = data.get('full_name', username)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=user_type,
            department=data.get('department', ''),
            specialty=data.get('specialty', '')
        )

        # 设置密码
        new_user.set_password(password)

        # 保存到数据库
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'role': new_user.role
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"注册错误: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500


@auth_bp.route('/me', methods=['GET'])
def get_user_info():
    # 这是一个示例，实际中需要验证token
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({
            'success': False,
            'message': '未提供认证信息'
        }), 401

    # 这里应该验证token，但为了简单演示，我们返回一个示例用户
    return jsonify({
        'success': True,
        'user': {
            'id': 1,
            'username': 'demo_user',
            'role': 'doctor',
            'full_name': '演示用户'
        }
    })


# 添加一个GET方法来测试接口（仅用于测试）
@auth_bp.route('/test', methods=['GET'])
def test_auth():
    return jsonify({
        'success': True,
        'message': '认证模块工作正常',
        'available_endpoints': {
            'POST /api/auth/login': '用户登录',
            'POST /api/auth/register': '用户注册',
            'GET /api/auth/me': '获取用户信息'
        }
    })


# ==================== 导出蓝图 ====================
__all__ = ['main_bp', 'auth_bp']