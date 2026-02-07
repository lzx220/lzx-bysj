# test_mysql.py - 最简单的测试
print("开始测试MySQL连接...")

try:
    import pymysql

    # 连接到你的MySQL
    conn = pymysql.connect(
        host='localhost',  # 地址
        user='root',  # 用户名
        password='092112',  # 你的密码
        database='oral_cdss'  # 数据库名
    )

    print("✅ 太好了！MySQL连接成功！")
    print("你的配置完全正确：")
    print("用户名: root")
    print("密码: 092112")
    print("数据库: oral_cdss")

    conn.close()

except Exception as e:
    print(f"❌ 连接失败: {e}")
    print("\n可能的原因：")
    print("1. MySQL服务没启动")
    print("2. 密码不对")
    print("3. 其他问题")

input("\n按回车键退出...")