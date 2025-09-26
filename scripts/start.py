#!/usr/bin/env python3
"""
TeachAid应用启动脚本
包含性能优化和监控功能
"""
import asyncio
import os
import sys
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger

from app.core.config import settings
from app.core.performance import memory_profiler
from app.core.monitoring import monitoring


class TeachAidApplication:
    """TeachAid应用启动器"""

    def __init__(self):
        self.server = None
        self.monitoring_tasks = []

    def setup_logging(self):
        """设置日志配置"""
        # 移除默认处理器
        logger.remove()

        # 控制台日志
        logger.add(
            sys.stderr,
            level="INFO" if not settings.debug else "DEBUG",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True
        )

        # 文件日志
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        logger.add(
            log_dir / "teachaid.log",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="100 MB",
            retention="30 days",
            compression="zip"
        )

        # 错误日志单独文件
        logger.add(
            log_dir / "error.log",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="50 MB",
            retention="30 days",
            compression="zip"
        )

        logger.info("日志系统初始化完成")

    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}，准备关闭应用...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)

    async def start_monitoring_tasks(self):
        """启动监控任务"""
        try:
            # 内存监控任务
            async def memory_monitor():
                while True:
                    memory_profiler.take_snapshot("periodic")
                    await asyncio.sleep(60)  # 每分钟一次

            # 清理任务
            async def cleanup_task():
                while True:
                    await asyncio.sleep(3600)  # 每小时一次
                    try:
                        # 清理过期告警
                        cleaned = await monitoring.cleanup_old_data(7)
                        if cleaned > 0:
                            logger.info(f"清理了 {cleaned} 个过期监控数据")
                    except Exception as e:
                        logger.error(f"清理任务失败: {e}")

            # 启动监控任务
            self.monitoring_tasks = [
                asyncio.create_task(memory_monitor()),
                asyncio.create_task(cleanup_task())
            ]

            logger.info("监控任务启动完成")

        except Exception as e:
            logger.error(f"启动监控任务失败: {e}")

    async def shutdown(self):
        """优雅关闭应用"""
        logger.info("开始关闭应用...")

        try:
            # 取消监控任务
            for task in self.monitoring_tasks:
                task.cancel()

            # 等待任务完成
            if self.monitoring_tasks:
                await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

            # 关闭服务器
            if self.server:
                self.server.should_exit = True

            logger.info("应用关闭完成")

        except Exception as e:
            logger.error(f"关闭应用时出错: {e}")

    def create_uvicorn_config(self) -> dict:
        """创建Uvicorn配置"""
        config = {
            "app": "app.main:app",
            "host": settings.host,
            "port": settings.port,
            "reload": settings.debug,
            "workers": 1 if settings.debug else 4,
            "log_level": "debug" if settings.debug else "info",
            "access_log": True,
            "use_colors": True,
            "server_header": False,  # 隐藏服务器信息
            "date_header": False,    # 禁用Date头
        }

        # 生产环境优化
        if not settings.debug:
            config.update({
                "loop": "uvloop",  # 使用uvloop提升性能
                "http": "httptools",  # 使用httptools提升HTTP解析性能
                "backlog": 2048,   # 增加backlog
                "limit_concurrency": 1000,  # 并发限制
                "limit_max_requests": 10000,  # 最大请求数
                "timeout_keep_alive": 5,     # Keep-Alive超时
            })

        return config

    async def run(self):
        """运行应用"""
        try:
            # 设置日志
            self.setup_logging()

            # 设置信号处理
            self.setup_signal_handlers()

            # 启动监控
            await self.start_monitoring_tasks()

            # 创建并运行服务器
            config = uvicorn.Config(**self.create_uvicorn_config())
            self.server = uvicorn.Server(config)

            logger.info(f"TeachAid应用启动中...")
            logger.info(f"服务地址: http://{settings.host}:{settings.port}")
            logger.info(f"调试模式: {settings.debug}")
            logger.info(f"API文档: http://{settings.host}:{settings.port}/docs")

            # 启动应用
            await self.server.serve()

        except Exception as e:
            logger.error(f"应用启动失败: {e}")
            raise
        finally:
            await self.shutdown()


def check_dependencies():
    """检查依赖和环境"""
    issues = []

    # 检查Python版本
    if sys.version_info < (3, 8):
        issues.append("Python 3.8或更高版本是必需的")

    # 检查环境变量
    required_env_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"缺少环境变量: {var}")

    # 检查必要的目录
    directories = ["logs", "uploads"]
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)

    if issues:
        print("环境检查失败:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    print("环境检查通过 ✓")


def main():
    """主函数"""
    print("=" * 60)
    print("TeachAid AI辅助教学平台")
    print("=" * 60)

    # 环境检查
    check_dependencies()

    # 创建应用实例
    app = TeachAidApplication()

    try:
        # 运行应用
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n应用被用户中断")
    except Exception as e:
        print(f"应用运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()