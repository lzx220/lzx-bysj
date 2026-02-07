import os
from datetime import timedelta


class Config:
    """基础配置类"""
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'mysql+pymysql://root:password@localhost:3306/dental_cds_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT配置
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # 文件上传
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # 评分规则配置
    MIN_SCORE = 0
    MAX_SCORE = 100
    SUCCESS_THRESHOLD = 70
    HIGH_RISK_THRESHOLD = 30


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}