# security.py - 简化版
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g
from app.utils.response import unauthorized_response, forbidden_response


class SimpleSecurity:
    """简单的安全模块 - 适合学生项目"""

    def __init__(self, secret_key='your-secret-key-change-this'):
        self.secret_key = secret_key.encode('utf-8')
        # 模拟数据库中的用户（实际项目中从数据库读取）
        self.users = {
            'admin': {
                'id': 1,
                'username': 'admin',
                'password_hash': self._hash_password('admin123'),  # 简单哈希
                'role': 'admin',
                'full_name': '管理员'
            },
            'doctor1': {
                'id': 2,
                'username': 'doctor1',
                'password_hash': self._hash_password('doctor123'),
                'role': 'doctor',
                'full_name': '张医生'
            },
            'patient1': {
                'id': 3,
                'username': 'patient1',
                'password_hash': self._hash_password('patient123'),
                'role': 'patient',
                'full_name': '李患者'
            }
        }

    def _hash_password(self, password):
        """简单密码哈希"""
        # 使用SHA256 + 盐
        salt = self.secret_key[:16]  # 使用部分secret作为盐
        return hashlib.sha256((password + salt.decode('utf-8')).encode('utf-8')).hexdigest()

    def verify_user(self, username, password):
        """验证用户"""
        user = self.users.get(username)
        if not user:
            return None

        password_hash = self._hash_password(password)
        if user['password_hash'] == password_hash:
            return user

        return None

    def generate_simple_token(self, user_id, username, role):
        """生成简单令牌（JSON格式）"""
        # 有效期为7天
        expire_time = (datetime.now() + timedelta(days=7)).timestamp()

        token_data = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'expire': expire_time
        }

        # 将数据转换为JSON字符串
        token_json = json.dumps(token_data)

        # 生成签名（防篡改）
        signature = hmac.new(
            self.secret_key,
            token_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 组合：数据 + 签名
        return f"{token_json}.{signature}"

    def verify_simple_token(self, token):
        """验证简单令牌"""
        if not token:
            return None

        try:
            # 分割数据和签名
            parts = token.split('.')
            if len(parts) != 2:
                return None

            token_json, signature = parts

            # 验证签名
            expected_signature = hmac.new(
                self.secret_key,
                token_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if signature != expected_signature:
                return None

            # 解析数据
            token_data = json.loads(token_json)

            # 检查是否过期
            if datetime.now().timestamp() > token_data.get('expire', 0):
                return None

            return token_data

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def requires_auth(self, f):
        """需要认证的装饰器"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 从请求头获取令牌
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return unauthorized_response('请先登录')

            # 支持两种格式：Bearer token 或直接token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # 去掉 'Bearer '
            else:
                token = auth_header

            # 验证令牌
            token_data = self.verify_simple_token(token)
            if not token_data:
                return unauthorized_response('登录已过期，请重新登录')

            # 将用户信息存储在全局变量g中
            g.user_id = token_data['user_id']
            g.username = token_data['username']
            g.user_role = token_data['role']

            return f(*args, **kwargs)

        return decorated_function

    def requires_role(self, *allowed_roles):
        """需要特定角色的装饰器"""

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 先进行认证
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    return unauthorized_response('请先登录')

                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
                else:
                    token = auth_header

                token_data = self.verify_simple_token(token)
                if not token_data:
                    return unauthorized_response('登录已过期')

                # 检查角色
                user_role = token_data.get('role')
                if user_role not in allowed_roles:
                    return forbidden_response('权限不足')

                # 存储用户信息
                g.user_id = token_data['user_id']
                g.username = token_data['username']
                g.user_role = user_role

                return f(*args, **kwargs)

            return decorated_function

        return decorator


# 创建全局实例
security = SimpleSecurity()


# ===== 以下是兼容原有代码的包装函数 =====

def hash_password(password):
    """哈希密码（兼容函数）"""
    return security._hash_password(password)


def verify_password(plain_password, hashed_password):
    """验证密码（兼容函数）"""
    # 因为我们是简单哈希，直接比较
    test_hash = security._hash_password(plain_password)
    return test_hash == hashed_password


def generate_token(user_id, role, username):
    """生成令牌（兼容函数）"""
    return security.generate_simple_token(user_id, username, role)


def verify_token(token):
    """验证令牌（兼容函数）"""
    return security.verify_simple_token(token)


def requires_roles(*roles):
    """角色验证装饰器（兼容函数）"""
    return security.requires_role(*roles)


# ===== 使用示例 =====
if __name__ == "__main__":
    # 测试代码
    print("=== 安全模块测试 ===")

    # 1. 验证用户
    user = security.verify_user('admin', 'admin123')
    print(f"1. 验证admin用户: {'成功' if user else '失败'}")

    # 2. 生成令牌
    if user:
        token = security.generate_simple_token(
            user['id'],
            user['username'],
            user['role']
        )
        print(f"2. 生成令牌: {token[:30]}...")

        # 3. 验证令牌
        token_data = security.verify_simple_token(token)
        print(f"3. 验证令牌: {'成功' if token_data else '失败'}")
        if token_data:
            print(f"   用户ID: {token_data['user_id']}")
            print(f"   用户名: {token_data['username']}")
            print(f"   角色: {token_data['role']}")