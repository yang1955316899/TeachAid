"""
测试配置管理功能
包括API测试和界面功能验证
"""
import asyncio
import json
import aiohttp
from datetime import datetime, timedelta


class ConfigManagementTester:
    """配置管理功能测试器"""

    def __init__(self, base_url="http://localhost:50001"):
        self.base_url = base_url
        self.session = None
        self.admin_token = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def login_as_admin(self, username="admin", password="admin123"):
        """以管理员身份登录"""
        try:
            login_data = {
                "username": username,
                "password": password
            }

            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    print(f"✅ 管理员登录成功: {username}")
                    return True
                else:
                    error = await response.text()
                    print(f"❌ 管理员登录失败 ({response.status}): {error}")
                    return False
        except Exception as e:
            print(f"❌ 登录请求失败: {e}")
            return False

    def get_auth_headers(self):
        """获取认证头"""
        if not self.admin_token:
            raise ValueError("未登录，请先调用 login_as_admin")
        return {"Authorization": f"Bearer {self.admin_token}"}

    async def test_system_settings(self):
        """测试系统设置管理"""
        print("\n🔧 测试系统设置管理...")

        # 1. 获取系统设置列表
        try:
            async with self.session.get(
                f"{self.base_url}/api/admin/settings",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    settings = await response.json()
                    print(f"✅ 获取系统设置成功，共 {len(settings.get('settings', {}))} 个分类")

                    # 显示部分设置
                    for category, category_settings in settings.get('settings', {}).items():
                        print(f"   📁 {category}: {len(category_settings)} 个设置")
                        if category_settings:
                            print(f"      例如: {category_settings[0]['setting_key']} = {category_settings[0]['setting_value']}")
                else:
                    error = await response.text()
                    print(f"❌ 获取系统设置失败 ({response.status}): {error}")
                    return False
        except Exception as e:
            print(f"❌ 获取系统设置请求失败: {e}")
            return False

        # 2. 创建新的系统设置
        try:
            new_setting = {
                "category": "test",
                "setting_key": "test_setting_" + str(int(datetime.now().timestamp())),
                "setting_value": "test_value",
                "display_name": "测试设置",
                "description": "这是一个测试设置",
                "value_type": "string",
                "input_type": "text"
            }

            async with self.session.post(
                f"{self.base_url}/api/admin/settings",
                json=new_setting,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    setting_id = result.get("setting_id")
                    print(f"✅ 创建系统设置成功: {new_setting['setting_key']}")

                    # 3. 更新设置
                    update_data = {
                        "setting_value": "updated_test_value",
                        "description": "更新后的测试设置"
                    }

                    async with self.session.put(
                        f"{self.base_url}/api/admin/settings/{setting_id}",
                        json=update_data,
                        headers=self.get_auth_headers()
                    ) as response:
                        if response.status == 200:
                            print(f"✅ 更新系统设置成功")
                        else:
                            error = await response.text()
                            print(f"❌ 更新系统设置失败 ({response.status}): {error}")

                else:
                    error = await response.text()
                    print(f"❌ 创建系统设置失败 ({response.status}): {error}")
        except Exception as e:
            print(f"❌ 创建系统设置请求失败: {e}")

        return True

    async def test_security_policies(self):
        """测试安全策略管理"""
        print("\n🔒 测试安全策略管理...")

        # 1. 获取安全策略列表
        try:
            async with self.session.get(
                f"{self.base_url}/api/admin/security-policies",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    policies = await response.json()
                    print(f"✅ 获取安全策略成功，共 {len(policies.get('policies', []))} 个策略")

                    # 显示策略信息
                    for policy in policies.get('policies', [])[:3]:  # 显示前3个
                        print(f"   🛡️ {policy['policy_name']} ({policy['policy_type']})")
                        print(f"      优先级: {policy['priority']}, 状态: {'启用' if policy.get('is_active') else '禁用'}")
                else:
                    error = await response.text()
                    print(f"❌ 获取安全策略失败 ({response.status}): {error}")
                    return False
        except Exception as e:
            print(f"❌ 获取安全策略请求失败: {e}")
            return False

        # 2. 创建新的安全策略
        try:
            new_policy = {
                "policy_name": f"测试策略_{int(datetime.now().timestamp())}",
                "policy_type": "access_control",
                "config": {
                    "max_daily_requests": 1000,
                    "allowed_ips": ["127.0.0.1", "192.168.1.0/24"],
                    "rate_limit": {
                        "requests_per_minute": 60,
                        "burst_size": 10
                    }
                },
                "description": "用于测试的访问控制策略",
                "applies_to_roles": ["student", "teacher"],
                "priority": 5
            }

            async with self.session.post(
                f"{self.base_url}/api/admin/security-policies",
                json=new_policy,
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    policy_id = result.get("policy_id")
                    print(f"✅ 创建安全策略成功: {new_policy['policy_name']}")

                    # 3. 更新策略
                    update_data = {
                        "priority": 8,
                        "description": "更新后的测试策略",
                        "config": {
                            **new_policy["config"],
                            "max_daily_requests": 2000
                        }
                    }

                    async with self.session.put(
                        f"{self.base_url}/api/admin/security-policies/{policy_id}",
                        json=update_data,
                        headers=self.get_auth_headers()
                    ) as response:
                        if response.status == 200:
                            print(f"✅ 更新安全策略成功")
                        else:
                            error = await response.text()
                            print(f"❌ 更新安全策略失败 ({response.status}): {error}")

                else:
                    error = await response.text()
                    print(f"❌ 创建安全策略失败 ({response.status}): {error}")
        except Exception as e:
            print(f"❌ 创建安全策略请求失败: {e}")

        return True

    async def test_login_logs(self):
        """测试登录日志查询"""
        print("\n📊 测试登录日志查询...")

        try:
            # 1. 获取登录统计
            async with self.session.get(
                f"{self.base_url}/api/admin/login-stats?days=7",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ 获取登录统计成功")
                    print(f"   📈 7天内总登录次数: {stats['total_logins']}")
                    print(f"   ✅ 成功登录: {stats['successful_logins']}")
                    print(f"   ❌ 失败登录: {stats['failed_logins']}")
                    print(f"   👥 唯一用户数: {stats['unique_users']}")
                else:
                    error = await response.text()
                    print(f"❌ 获取登录统计失败 ({response.status}): {error}")

            # 2. 获取安全统计
            async with self.session.get(
                f"{self.base_url}/api/admin/security-stats",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ 获取安全统计成功")
                    print(f"   🔒 锁定用户数: {stats['locked_users']}")
                    print(f"   ⚠️ 今日失败尝试: {stats['failed_attempts_today']}")
                    print(f"   🚨 可疑IP数量: {len(stats['suspicious_ips'])}")
                else:
                    error = await response.text()
                    print(f"❌ 获取安全统计失败 ({response.status}): {error}")

            # 3. 获取登录日志
            async with self.session.get(
                f"{self.base_url}/api/admin/login-logs?page=1&page_size=10",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    logs = await response.json()
                    print(f"✅ 获取登录日志成功，共 {logs['total']} 条记录")

                    # 显示最近几条日志
                    for log in logs.get('logs', [])[:3]:
                        status = "成功" if log['is_success'] else "失败"
                        print(f"   📝 {log['username']} - {status} - {log['ip_address']} - {log['logged_in_at']}")
                        if not log['is_success'] and log.get('failure_reason'):
                            print(f"      失败原因: {log['failure_reason']}")
                else:
                    error = await response.text()
                    print(f"❌ 获取登录日志失败 ({response.status}): {error}")

        except Exception as e:
            print(f"❌ 登录日志测试失败: {e}")

        return True

    async def test_user_management(self):
        """测试用户管理功能"""
        print("\n👥 测试用户管理功能...")

        try:
            # 1. 获取用户列表
            async with self.session.get(
                f"{self.base_url}/api/admin/users?page=1&page_size=10",
                headers=self.get_auth_headers()
            ) as response:
                if response.status == 200:
                    users = await response.json()
                    print(f"✅ 获取用户列表成功，共 {users['total']} 个用户")

                    # 显示用户信息
                    for user in users.get('users', [])[:3]:
                        print(f"   👤 {user['user_name']} ({user['user_role']}) - {user['user_status']}")
                        print(f"      邮箱: {user['user_email']}, 失败次数: {user['user_failed_login_attempts']}")

                        # 如果有失败登录的用户，测试解锁功能
                        if user['user_failed_login_attempts'] > 0:
                            print(f"   🔓 测试解锁用户: {user['user_name']}")
                            async with self.session.post(
                                f"{self.base_url}/api/admin/users/{user['user_id']}/unlock",
                                headers=self.get_auth_headers()
                            ) as unlock_response:
                                if unlock_response.status == 200:
                                    print(f"   ✅ 用户解锁成功")
                                else:
                                    error = await unlock_response.text()
                                    print(f"   ❌ 用户解锁失败: {error}")
                else:
                    error = await response.text()
                    print(f"❌ 获取用户列表失败 ({response.status}): {error}")

        except Exception as e:
            print(f"❌ 用户管理测试失败: {e}")

        return True

    async def test_failed_login_lockout(self):
        """测试登录失败锁定功能"""
        print("\n🔒 测试登录失败锁定功能...")

        test_username = f"test_user_{int(datetime.now().timestamp())}"

        try:
            # 1. 先注册一个测试用户
            register_data = {
                "user_name": test_username,
                "user_email": f"{test_username}@test.com",
                "password": "TestPassword123!",
                "user_full_name": "测试用户"
            }

            async with self.session.post(
                f"{self.base_url}/api/auth/register",
                json=register_data
            ) as response:
                if response.status == 200:
                    print(f"✅ 测试用户注册成功: {test_username}")
                else:
                    # 可能用户已存在，继续测试
                    print(f"⚠️ 用户注册失败，使用现有用户测试")

            # 2. 多次错误登录，触发锁定
            print(f"🔄 开始测试连续错误登录...")
            for i in range(6):  # 超过最大失败次数
                login_data = {
                    "username": test_username,
                    "password": "wrong_password"
                }

                async with self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json=login_data
                ) as response:
                    result = await response.json() if response.content_type == 'application/json' else await response.text()

                    if response.status == 423:  # 账户锁定
                        print(f"   🔒 第 {i+1} 次尝试：账户已锁定")
                        break
                    elif response.status == 401:
                        print(f"   ❌ 第 {i+1} 次尝试：密码错误")
                    else:
                        print(f"   ⚠️ 第 {i+1} 次尝试：状态码 {response.status}")

            # 3. 验证账户确实被锁定
            print(f"🔍 验证账户锁定状态...")
            correct_login = {
                "username": test_username,
                "password": "TestPassword123!"
            }

            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                json=correct_login
            ) as response:
                if response.status == 423:
                    print(f"✅ 账户锁定功能正常 - 即使密码正确也无法登录")
                elif response.status == 200:
                    print(f"⚠️ 账户未被锁定，可能配置有问题")
                else:
                    error = await response.text()
                    print(f"❓ 未预期的响应 ({response.status}): {error}")

        except Exception as e:
            print(f"❌ 登录锁定测试失败: {e}")

        return True


async def main():
    """主测试函数"""
    print("🚀 开始配置管理功能测试...")
    print("=" * 50)

    async with ConfigManagementTester() as tester:
        # 1. 管理员登录
        if not await tester.login_as_admin():
            print("❌ 管理员登录失败，无法继续测试")
            return

        # 2. 测试系统设置管理
        await tester.test_system_settings()

        # 3. 测试安全策略管理
        await tester.test_security_policies()

        # 4. 测试登录日志查询
        await tester.test_login_logs()

        # 5. 测试用户管理
        await tester.test_user_management()

        # 6. 测试登录失败锁定
        await tester.test_failed_login_lockout()

    print("\n" + "=" * 50)
    print("✅ 配置管理功能测试完成")
    print("\n📋 测试结果摘要:")
    print("   🔧 系统设置管理 - 已测试")
    print("   🔒 安全策略管理 - 已测试")
    print("   📊 登录日志查询 - 已测试")
    print("   👥 用户管理功能 - 已测试")
    print("   🔒 登录失败锁定 - 已测试")
    print("\n💡 提示: 请检查数据库中的相关表是否有新增的测试数据")


if __name__ == "__main__":
    asyncio.run(main())