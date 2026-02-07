# run.py
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表
        db.create_all()

        # 创建默认管理员（如果不存在）
        from app.models.user import User

        # 检查并创建管理员
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@hospital.com',
                full_name='系统管理员',
                role='admin',
                department='系统管理部'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ 创建管理员账号：admin / admin123")

        # 检查并创建医生账号
        if not User.query.filter_by(username='doctor').first():
            doctor = User(
                username='doctor',
                email='doctor@hospital.com',
                full_name='演示医生',
                role='doctor',
                department='口腔科'
            )
            doctor.set_password('doctor123')
            db.session.add(doctor)
            print("✅ 创建医生账号：doctor / doctor123")

        db.session.commit()
        print("✅ 数据库初始化完成！")

    print("\n🚀 启动服务器...")
    print("📌 访问地址：http://localhost:5000")
    print("📌 健康检查：http://localhost:5000/api/health")
    print("📌 登录接口：http://localhost:5000/api/auth/login")
    print("📌 注册接口：http://localhost:5000/api/auth/register")
    print("\n📋 测试账号：")
    print("  管理员：admin / admin123")
    print("  医生：doctor / doctor123")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)