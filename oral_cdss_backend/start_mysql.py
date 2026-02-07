# start_mysql.py
import sys
import os

print("=" * 60)
print("口腔CDSS系统 - MySQL版本")
print("=" * 60)

# 1. 检查并安装pymysql
print("\n1. 检查MySQL驱动...")
try:
    import pymysql
    print("✅ pymysql 已安装")
except ImportError:
    print("正在安装 pymysql...")
    os.system(f"{sys.executable} -m pip install pymysql")

# 2. 设置MySQL连接
print("\n2. 配置MySQL连接...")

# 在这里设置你的MySQL信息
MYSQL_CONFIG = {
    'user': 'root',      # 改成你的用户名
    'password': '092112', # 改成你的密码
    'host': 'localhost',
    'port': 3306,
    'database': 'oral_cdss'  # 改成你的数据库名
}

# 3. 测试MySQL连接
try:
    import pymysql
    conn = pymysql.connect(**MYSQL_CONFIG)
    print("✅ MySQL连接成功！")
    conn.close()
except Exception as e:
    print(f"❌ MySQL连接失败: {e}")
    print("\n请检查：")
    print("1. MySQL服务是否启动？")
    print("2. 用户名密码是否正确？")
    print("3. 数据库是否存在？（CREATE DATABASE oral_cdss;）")
    input("\n按回车退出...")
    sys.exit(1)

# 4. 更新app配置
print("\n3. 更新应用配置...")
config_path = os.path.join('app', '__init__.py')

with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换数据库配置
mysql_uri = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@localhost:3306/{MYSQL_CONFIG['database']}"
content = content.replace(
    "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oral_cdss.db'",
    f"app.config['SQLALCHEMY_DATABASE_URI'] = '{mysql_uri}'"
)

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 配置更新完成")

# 5. 启动系统
print("\n4. 启动系统...")
os.system(f"{sys.executable} run.py")