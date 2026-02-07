# sync_database.py
print("=== 一键同步数据库 ===")
print("将删除所有数据并重新创建表结构")
print("=" * 40)

confirm = input("确定要同步吗？所有数据将被删除！(y/n): ")
if confirm.lower() != 'y':
    print("取消操作")
    exit()

import pymysql
from app import create_app, db

# 1. 删除并重建数据库
print("\n1. 重建数据库...")
try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='092112'
    )
    cursor = conn.cursor()

    cursor.execute("DROP DATABASE IF EXISTS oral_cdss")
    cursor.execute("CREATE DATABASE oral_cdss CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print("✅ 数据库重建完成")

    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ 错误: {e}")

# 2. 使用SQLAlchemy根据模型创建表
print("\n2. 根据模型创建表...")
app = create_app()

with app.app_context():
    # 删除所有表
    db.drop_all()
    print("✅ 清除旧表")

    # 重新创建所有表（根据模型定义）
    db.create_all()
    print("✅ 新表创建完成")

    # 创建默认数据
    print("\n3. 创建默认数据...")

    # 创建管理员用户
    from app.models import User

    admin = User(
        username='admin',
        email='admin@hospital.com',
        password_hash='admin123',
        real_name='系统管理员',
        role='管理员',
        department='系统管理部'
    )
    db.session.add(admin)

    # 如果有其他默认数据，在这里添加

    db.session.commit()
    print("✅ 默认数据创建完成")

print("\n" + "=" * 40)
print("🎉 同步完成！")
print("现在数据库结构和代码完全一致")
print("运行: python run.py")