# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # 基本配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:092112@localhost:3306/oral_cdss'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-123'

    # 初始化
    db.init_app(app)

    # 更好的CORS配置
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 添加CORS中间件
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    try:
        # 导入蓝图
        from app.routes import main_bp, auth_bp

        # 注册蓝图
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/api/auth')

        print("✅ 蓝图注册成功")

    except ImportError as e:
        print(f"⚠️ 警告: 无法导入路由模块: {e}")

        # 创建简单的默认路由
        @app.route('/')
        def index():
            return '口腔CDSS系统运行正常！请检查路由配置。'

        @app.route('/api/health', methods=['GET'])
        def health_check():
            return {'status': 'healthy', 'message': '系统运行中'}

    return app