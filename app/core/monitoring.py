"""
应用监控和告警服务
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

from loguru import logger

class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """告警信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class Metric:
    """指标数据"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]

class MonitoringService:
    """监控服务"""

    def __init__(self):
        # 指标存储
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # 告警存储
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict] = {}

        # 性能监控
        self.response_times: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.request_counts: Dict[str, int] = defaultdict(int)

        # 系统监控
        self.system_stats: Dict[str, Any] = {}

        # 配置告警规则
        self._setup_alert_rules()

        logger.info("监控服务已启动")

    def _setup_alert_rules(self):
        """设置告警规则"""
        self.alert_rules = {
            "high_response_time": {
                "metric": "response_time",
                "threshold": 5.0,  # 5秒
                "operator": ">",
                "level": AlertLevel.WARNING,
                "title": "响应时间过长"
            },
            "high_error_rate": {
                "metric": "error_rate",
                "threshold": 0.1,  # 10%
                "operator": ">",
                "level": AlertLevel.ERROR,
                "title": "错误率过高"
            },
            "high_memory_usage": {
                "metric": "memory_usage",
                "threshold": 0.8,  # 80%
                "operator": ">",
                "level": AlertLevel.WARNING,
                "title": "内存使用率过高"
            },
            "database_connection_error": {
                "metric": "db_errors",
                "threshold": 5,
                "operator": ">=",
                "level": AlertLevel.CRITICAL,
                "title": "数据库连接异常"
            }
        }

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标"""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            tags=tags or {}
        )

        self.metrics[name].append(metric)

        # 检查告警规则
        self._check_alert_rules(name, value)

    def record_request(self, method: str, path: str, status_code: int, response_time: float):
        """记录请求信息"""
        # 记录响应时间
        self.response_times.append(response_time)
        self.record_metric("response_time", response_time, {
            "method": method,
            "path": path,
            "status": str(status_code)
        })

        # 记录请求计数
        request_key = f"{method}:{path}"
        self.request_counts[request_key] += 1

        # 记录错误计数
        if status_code >= 400:
            error_key = f"{method}:{path}:{status_code}"
            self.error_counts[error_key] += 1

            # 记录错误率
            error_rate = self.error_counts[error_key] / self.request_counts[request_key]
            self.record_metric("error_rate", error_rate, {
                "method": method,
                "path": path,
                "status": str(status_code)
            })

    def record_error(self, error_type: str, error_message: str, source: str = "application"):
        """记录错误"""
        self.record_metric(f"{source}_errors", 1, {
            "error_type": error_type,
            "source": source
        })

        # 生成告警
        self.create_alert(
            level=AlertLevel.ERROR,
            title=f"{source}错误",
            message=f"{error_type}: {error_message}",
            source=source,
            data={
                "error_type": error_type,
                "error_message": error_message
            }
        )

    def record_database_event(self, event_type: str, duration: float = 0, error: str = None):
        """记录数据库事件"""
        if error:
            self.record_metric("db_errors", 1, {"error": error})
        else:
            self.record_metric("db_query_time", duration, {"type": event_type})

    def record_ai_request(self, model: str, tokens: int, cost: float, success: bool):
        """记录AI请求"""
        self.record_metric("ai_tokens_used", tokens, {"model": model})
        self.record_metric("ai_cost", cost, {"model": model})

        if not success:
            self.record_metric("ai_errors", 1, {"model": model})

    def _check_alert_rules(self, metric_name: str, value: float):
        """检查告警规则"""
        for rule_name, rule in self.alert_rules.items():
            if rule["metric"] == metric_name:
                threshold = rule["threshold"]
                operator = rule["operator"]

                should_alert = False
                if operator == ">" and value > threshold:
                    should_alert = True
                elif operator == ">=" and value >= threshold:
                    should_alert = True
                elif operator == "<" and value < threshold:
                    should_alert = True
                elif operator == "<=" and value <= threshold:
                    should_alert = True
                elif operator == "==" and value == threshold:
                    should_alert = True

                if should_alert:
                    self.create_alert(
                        level=rule["level"],
                        title=rule["title"],
                        message=f"{metric_name}值为{value}，超过阈值{threshold}",
                        source="monitoring",
                        data={
                            "metric": metric_name,
                            "value": value,
                            "threshold": threshold,
                            "rule": rule_name
                        }
                    )

    def create_alert(self, level: AlertLevel, title: str, message: str,
                    source: str, data: Optional[Dict[str, Any]] = None):
        """创建告警"""
        import uuid

        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            source=source,
            data=data or {}
        )

        self.alerts[alert_id] = alert

        # 记录告警日志
        if level == AlertLevel.CRITICAL:
            logger.critical(f"告警 [{level.value.upper()}] {title}: {message}")
        elif level == AlertLevel.ERROR:
            logger.error(f"告警 [{level.value.upper()}] {title}: {message}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"告警 [{level.value.upper()}] {title}: {message}")
        else:
            logger.info(f"告警 [{level.value.upper()}] {title}: {message}")

        # TODO: 发送告警通知（邮件、短信、Webhook等）
        asyncio.create_task(self._send_alert_notification(alert))

        return alert_id

    async def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        try:
            # 这里可以实现各种通知方式
            # 例如：邮件、短信、Slack、钉钉等

            if alert.level in [AlertLevel.CRITICAL, AlertLevel.ERROR]:
                # 关键告警需要立即通知
                await self._send_urgent_notification(alert)

            # 记录通知发送
            logger.info(f"告警通知已发送: {alert.id} - {alert.title}")

        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")

    async def _send_urgent_notification(self, alert: Alert):
        """发送紧急通知"""
        # 实现紧急通知逻辑
        pass

    def resolve_alert(self, alert_id: str, resolver: str = "system"):
        """解决告警"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()

            logger.info(f"告警已解决: {alert_id} - {alert.title} (解决人: {resolver})")
            return True

        return False

    def get_metrics_summary(self, time_range: int = 300) -> Dict[str, Any]:
        """获取指标摘要（最近N秒）"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_range)

        summary = {
            "time_range": time_range,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }

        for metric_name, metric_list in self.metrics.items():
            recent_metrics = [
                m for m in metric_list
                if m.timestamp >= cutoff_time
            ]

            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary["metrics"][metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1]
                }

        return summary

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.response_times:
            return {"message": "暂无性能数据"}

        times = list(self.response_times)
        times.sort()

        count = len(times)
        avg_time = sum(times) / count
        p50 = times[int(count * 0.5)]
        p90 = times[int(count * 0.9)]
        p95 = times[int(count * 0.95)]
        p99 = times[int(count * 0.99)]

        return {
            "total_requests": count,
            "avg_response_time": round(avg_time, 3),
            "percentiles": {
                "p50": round(p50, 3),
                "p90": round(p90, 3),
                "p95": round(p95, 3),
                "p99": round(p99, 3)
            },
            "min_time": round(min(times), 3),
            "max_time": round(max(times), 3)
        }

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())

        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # 按错误类型统计
        error_by_type = {}
        for error_key, count in self.error_counts.items():
            parts = error_key.split(":")
            if len(parts) >= 3:
                status_code = parts[2]
                error_by_type[status_code] = error_by_type.get(status_code, 0) + count

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(error_rate, 2),
            "errors_by_status": error_by_type
        }

    def get_alerts(self, level: Optional[AlertLevel] = None,
                  resolved: Optional[bool] = None, limit: int = 100) -> List[Dict]:
        """获取告警列表"""
        alerts = list(self.alerts.values())

        # 过滤
        if level:
            alerts = [a for a in alerts if a.level == level]

        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # 排序（最新的在前）
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        # 限制数量
        alerts = alerts[:limit]

        # 转换为字典
        return [
            {
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "source": alert.source,
                "data": alert.data,
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            }
            for alert in alerts
        ]

    def get_health_status(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        # 计算最近5分钟的错误率
        recent_metrics = self.get_metrics_summary(300)
        error_rate = 0

        if "error_rate" in recent_metrics["metrics"]:
            error_rate = recent_metrics["metrics"]["error_rate"]["avg"]

        # 计算平均响应时间
        avg_response_time = 0
        if "response_time" in recent_metrics["metrics"]:
            avg_response_time = recent_metrics["metrics"]["response_time"]["avg"]

        # 未解决的告警数量
        unresolved_alerts = len([a for a in self.alerts.values() if not a.resolved])
        critical_alerts = len([
            a for a in self.alerts.values()
            if not a.resolved and a.level == AlertLevel.CRITICAL
        ])

        # 健康评分 (0-100)
        health_score = 100

        if error_rate > 0.1:  # 错误率超过10%
            health_score -= 30
        elif error_rate > 0.05:  # 错误率超过5%
            health_score -= 15

        if avg_response_time > 5:  # 响应时间超过5秒
            health_score -= 20
        elif avg_response_time > 2:  # 响应时间超过2秒
            health_score -= 10

        if critical_alerts > 0:
            health_score -= 40
        elif unresolved_alerts > 5:
            health_score -= 20

        health_score = max(0, health_score)

        # 确定健康状态
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "warning"
        elif health_score >= 40:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "health_score": health_score,
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "error_rate": round(error_rate * 100, 2),
                "avg_response_time": round(avg_response_time, 3),
                "unresolved_alerts": unresolved_alerts,
                "critical_alerts": critical_alerts
            }
        }

    async def cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        # 清理旧告警
        old_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_time and alert.resolved
        ]

        for alert_id in old_alerts:
            del self.alerts[alert_id]

        logger.info(f"清理了 {len(old_alerts)} 个过期告警")

        return len(old_alerts)

# 全局监控服务实例
monitoring = MonitoringService()