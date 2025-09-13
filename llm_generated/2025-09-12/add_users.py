import asyncio
import pymysql
from datetime import datetime
import bcrypt

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root', 
    'password': 'root',
    'database': 'teachaid',
    'charset': 'utf8mb4'
}

def hash_password(password: str) -> str:
    """对密码进行bcrypt哈希"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def add_users():
    """添加三个正式用户到数据库"""
    connection = None
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 准备正式用户数据
        users = [
            {
                'username': 'admin001',
                'password': 'admin123',
                'email': 'admin001@teachaid.com',
                'role': 'admin',
                'full_name': '系统管理员'
            },
            {
                'username': 'teacher001', 
                'password': 'teacher123',
                'email': 'teacher001@teachaid.com',
                'role': 'teacher',
                'full_name': '教师用户'
            },
            {
                'username': 'student001',
                'password': 'student123', 
                'email': 'student001@teachaid.com',
                'role': 'student',
                'full_name': '学生用户'
            }
        ]
        
        current_time = datetime.now()
        
        for user in users:
            # 检查用户是否已存在
            cursor.execute("SELECT user_id FROM config_users WHERE user_name = %s", (user['username'],))
            if cursor.fetchone():
                print(f"用户 {user['username']} 已存在，跳过")
                continue
                
            # 哈希密码
            hashed_password = hash_password(user['password'])
            
            # 插入用户
            insert_sql = """
                INSERT INTO config_users (user_name, user_email, user_password_hash, user_role, user_full_name, 
                                        user_status, user_is_verified, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_sql, (
                user['username'],
                user['email'], 
                hashed_password,
                user['role'],
                user['full_name'],
                'active',  # user_status
                True,      # user_is_verified
                current_time,
                current_time
            ))
            
            print(f"成功添加用户: {user['username']} ({user['role']})")
        
        # 提交事务
        connection.commit()
        print("所有用户添加完成！")
        
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"添加用户时发生错误: {e}")
        
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    add_users()