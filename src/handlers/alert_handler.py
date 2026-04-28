"""
告警处理器
Alert Handler
"""

import time
import json
from typing import Any, Dict, List, Optional
from collections import deque
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4

from .base_handler import BaseHandler
from ..core.event_bus import EventBus
from ..utils.logger import get_logger
from ..models.alert import Alert, AlertStatus
from ..models.threat_event import ThreatEvent, Severity


@dataclass
class AlertCooldown:
    """告警冷却"""
    alert_type: str
    source: str
    last_alert_time: float = 0.0
    alert_count: int = 0
    suppressed_count: int = 0


class AlertHandler(BaseHandler):
    """告警处理器"""

    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        super().__init__(event_bus)
        self.name = "AlertHandler"

        # 配置
        self.enabled = config.get("enabled", True)
        self.handlers_config = config.get("handlers", [])
        self.severity_configs = config.get("severity_levels", {})

        # 默认冷却时间（秒）
        self.default_cooldown = {
            "low": 60,
            "medium": 30,
            "high": 10,
            "critical": 0
        }

        # 告警跟踪
        self.alerts: deque = deque(maxlen=1000)
        self.alert_history: deque = deque(maxlen=1000)
        self.cooldowns: Dict[str, AlertCooldown] = {}

        # 统计
        self.total_alerts = 0
        self.suppressed_alerts = 0
        self.active_alerts = 0

    def initialize(self) -> bool:
        """初始化处理器"""
        # 订阅威胁事件
        self.subscription_id = self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

        # 订阅原始威胁事件
        self.event_bus.subscribe(
            "threat.raw",
            self._on_threat_raw
        )

        self.logger.info(f"告警处理器初始化完成")
        return True

    def _on_threat_detected(self, event) -> None:
        """威胁检测事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                self._create_alert_from_data(event.data)

        except Exception as e:
            self.logger.error(f"处理威胁事件失败: {e}")

    def _on_threat_raw(self, event) -> None:
        """原始威胁事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                # 直接创建告警
                self._create_alert(event.data)

        except Exception as e:
            self.logger.error(f"处理原始威胁事件失败: {e}")

    def _create_alert_from_data(self, data: Dict[str, Any]) -> None:
        """从数据创建告警"""
        # 创建威胁事件
        threat_event = ThreatEvent(
            event_id=data.get("event_id", str(uuid4())),
            threat_type=data.get("threat_type", ""),
            severity=Severity(data.get("severity", "low")),
            detector=data.get("detector", ""),
            source=data.get("source", ""),
            evidence=data.get("evidence", {}),
            confidence=data.get("confidence", 1.0)
        )

        # 创建告警
        self._create_alert(threat_event.to_dict())

    def _create_alert(self, threat_data: Dict[str, Any]) -> None:
        """创建告警"""
        threat_type = threat_data.get("threat_type", "")
        source = threat_data.get("source", "")
        severity = Severity(threat_data.get("severity", "low"))

        # 检查冷却
        if self._is_on_cooldown(threat_type, source, severity):
            self.suppressed_alerts += 1
            self.logger.debug(f"告警已抑制: {threat_type} from {source}")
            return

        # 创建告警
        alert = Alert(event=ThreatEvent(
            event_id=threat_data.get("event_id", str(uuid4())),
            threat_type=threat_type,
            severity=severity,
            detector=threat_data.get("detector", ""),
            source=source,
            evidence=threat_data.get("evidence", {}),
            confidence=threat_data.get("confidence", 1.0)
        ))

        self.alerts.append(alert)
        self.alert_history.append(alert)
        self.total_alerts += 1
        self.active_alerts += 1

        # 更新冷却
        self._update_cooldown(threat_type, source, severity)

        # 分发告警
        self._distribute_alert(alert)

        # 发布告警创建事件
        self.event_bus.publish_sync(
            "alert.created",
            {
                "alert_id": alert.alert_id,
                "threat_type": threat_type,
                "severity": severity.value,
                "source": source,
                "timestamp": alert.created_at.isoformat()
            }
        )

    def _is_on_cooldown(self, threat_type: str, source: str, severity: Severity) -> bool:
        """检查是否在冷却期"""
        cooldown_key = f"{threat_type}:{source}"
        cooldown = self.cooldowns.get(cooldown_key)

        if cooldown is None:
            return False

        cooldown_time = self._get_cooldown_time(severity)
        elapsed = time.time() - cooldown.last_alert_time

        # 检查是否需要立即告警警）
        severity_config = self.severity_configs.get(severity.value, {})
        if severity_config.get("immediate", False):
            return False

        return elapsed < cooldown_time

    def _get_cooldown_time(self, severity: Severity) -> int:
        """获取冷却时间"""
        severity_config = self.severity_configs.get(severity.value, {})
        cooldown = severity_config.get("cooldown", self.default_cooldown.get(severity.value, 60))
        return cooldown

    def _update_cooldown(self, threat_type: str, source: str, severity: Severity) -> None:
        """更新冷却时间"""
        cooldown_key = f"{threat_type}:{source}"

        if cooldown_key not in self.cooldowns:
            self.cooldowns[cooldown_key] = AlertCooldown(
                alert_type=threat_type,
                source=source
            )

        cooldown = self.cooldowns[cooldown_key]
        cooldown.last_alert_time = time.time()
        cooldown.alert_count += 1

    def _distribute_alert(self, alert: Alert) -> None:
        """分发告警到各个处理器"""
        for handler_config in self.handlers_config:
            handler_type = handler_config.get("type", "")

            try:
                if handler_type == "log":
                    self._handle_log(alert, handler_config)
                elif handler_type == "console":
                    self._handle_console(alert)
                elif handler_type == "file":
                    self._handle_file(alert, handler_config)
                elif handler_type == "callback":
                    self._handle_callback(alert, handler_config)

            except Exception as e:
                self.logger.error(f"告警分发失败 ({handler_type}): {e}")

    def _handle_log(self, alert: Alert, config: Dict[str, Any]) -> None:
        """日志处理器"""
        level = config.get("level", "INFO")

        message = f"[ALERT] {alert.alert_id} | {alert.event.threat_type} | {alert.event.severity.value} | {alert.event.source}"
        message += f" | 置信度: {alert.event.confidence:.2f}"

        if alert.event.evidence:
            message += f" | 证据: {json.dumps(alert.event.evidence, ensure_ascii=False)}"

        self.logger.log(
            getattr(__import__("logging"), level),
            message
        )

    def _handle_console(self, alert: Alert) -> None:
        """控制台处理器"""
        severity = alert.event.severity.value.upper()
        timestamp = alert.created_at.strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{timestamp}] [{severity}] ALERT: {alert.event.threat_type}")
        print(f"  来源: {alert.event.source}")
        print(f"  检测器: {alert.event.detector}")
        print(f"  置信度: {alert.event.confidence:.2f}")
        if alert.event.evidence:
            print(f"  证据: {json.dumps(alert.event.evidence, ensure_ascii=False, indent=2)}")
        print()

    def _handle_file(self, alert: Alert, config: Dict[str, Any]) -> None:
        """文件处理器"""
        file_path = config.get("path", "logs/alerts.log")

        try:
            from pathlib import Path
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert.to_dict(), ensure_ascii=False, default=str) + "\n")

        except Exception as e:
            self.logger.error(f"写入告警文件失败: {e}")

    def _handle_callback(self, alert: Alert, config: Dict[str, Any]) -> None:
        """回调处理器"""
        callback = config.get("callback")
        if callback and callable(callback):
            callback(alert)

    def handle(self, data: Any) -> None:
        """处理数据（被动模式）"""
        if isinstance(data, dict):
            self._create_alert(data)

    def acknowledge_alert(self, alert_id: str, user: str = "system", notes: str = "") -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id and alert.is_active():
                alert.acknowledge(user, notes)
                self.active_alerts -= 1

                self.logger.info(f"告警已确认: {alert_id} by {user}")
                return True

        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                if alert.is_active():
                    self.active_alerts -= 1
                alert.resolve()

                self.logger.info(f"告警已解决: {alert_id}")
                return True

        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [
            alert.to_dict()
            for alert in self.alerts
            if alert.is_active()
        ]

    def get_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取告警"""
        alerts = list(self.alerts)

        if severity:
            alerts = [a for a in alerts if a.event.severity.value == severity]

        alerts = alerts[-limit:]

        return [alert.to_dict() for alert in alerts]

    def cleanup(self) -> None:
        """清理资源"""
        if self.subscription_id:
            self.event_bus.unsubscribe(self.subscription_id)

        self.alerts.clear()
        self.cooldowns.clear()

        self.logger.info(
            f"告警处理器已清理 (总计: {self.total_alerts}, "
            f"抑制: {self.suppressed_alerts})"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_alerts": self.total_alerts,
            "active_alerts": self.active_alerts,
            "suppressed_alerts": self.suppressed_alerts,
            "cooldowns_active": len(self.cooldowns),
            "enabled": self.enabled
        }
