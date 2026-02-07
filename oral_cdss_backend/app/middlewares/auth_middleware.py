from functools import wraps
from flask import request
from app.utils.response import unauthorized_response, forbidden_response
from app.utils.security import verify_token


def auth_required(f):
    """认证中间件"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return unauthorized_response('缺少认证令牌')

        if token.startswith('Bearer '):
            token = token[7:]

        payload = verify_token(token)
        if not payload:
            return unauthorized_response('无效或过期的令牌')

        # 将用户信息添加到请求上下文
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')
        request.username = payload.get('username')

        return f(*args, **kwargs)

    return decorated_function


def role_required(*allowed_roles):
    """角色权限中间件"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 先进行认证
            auth_result = auth_required(lambda: None)()
            if auth_result:
                return auth_result

            # 检查角色权限
            if request.user_role not in allowed_roles:
                return forbidden_response('权限不足')

            return f(*args, **kwargs)

        return decorated_function

    return decorator