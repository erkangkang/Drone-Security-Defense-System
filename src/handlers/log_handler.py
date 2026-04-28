"""
日志处理器
Log Handler
"""

import json
import time
from typing import Any, Dict, Optional
from pathlib import Path

from .base_handler import BaseHandler
from ..core.event_bus import EventBus
from ..utils.logger import get_logger


class LogHandler(BaseHandler):
    """日志处理器"""

    def __init__(self, event_bus: EventBus, config: Optional[Dict[str, Any]] = None):
        super().__init__(event_bus)
        self.name = "LogHandler"

        # 配置
        config = config or {}
        self.log_path = config.get("log_path", "logs/")
        self.threat_log_file = config.get("threat_log", "logs/threats.log")
        self.alert_log_file = config.get("alert_log", "logs/alerts.log")
        self.max_file_size = config.get("max_file_size", 10 * 1024 * 1024)  # 10MB

        # 统计
        self.threats_logged = 0
        self.alerts_logged = 0

    def initialize(self) -> bool:
        """初始化处理器"""
        # 确保日志目录存在
        Path(self.log_path).mkdir(parents=True, exist_ok=True)

        # 订阅事件
        self.event_bus.subscribe(
            "threat.detected",
            self._on_threat_detected
        )

        self.event_bus.subscribe(
            "alert.created",
            self._on_alert_created
        )

        self.logger.info("日志处理器初始化完成")
        return True

    def _on_threat_detected(self, event) -> None:
        """威胁检测事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                self._log_threat(event.data)

        except Exception as e:
            self.logger.error(f"记录威胁失败: {e}")

    def _on_alert_created(self, event) -> None:
        """告警创建事件处理"""
        if not self.enabled:
            return

        try:
            if isinstance(event.data, dict):
                self._log_alert(event.data)

        except Exception as e:
            self.logger.error(f"记录告警失败: {e}")

    def _log_threat(self, threat_data: Dict[str, Any]) -> None:
        """记录威胁"""
        log_entry = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "type": "threat",
            "data": threat_data
        }

        self._write_to_file(self.threat_log_file, json.dumps(log_entry, default=str))
        self.threats_logged += 1

    def _log_alert(self, alert_data: Dict[str, Any]) -> None:
        """记录告警"""
        log_entry = {
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "type": "alert",
            "data": alert_data
        }

        self._write_to_file(self.alert_log_file, json.dumps(log_entry, default=str))
        self.alerts_logged += 1

    def _write_to_file(self, file_path: str, content: str) -> None:
        """写入文件"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # 检查文件大小，必要时轮转
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                if file_size > self.max_file_size:
                    self._rotate_file(file_path)

            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content + "\n")

        except Exception as e:
            self.logger.error(f"写入文件失败 ({file_path}): {e}")

    def _rotate_file(self, file_path: str) -> None:
        """轮转日志文件"""
        try:
            from datetime import datetime

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}.{timestamp}.bak"

            Path(file_path).rename(backup_path)
            self.logger.info(f"日志文件已轮转: {file_path} -> {backup_path}")

        except Exception as e:
            self.logger.error(f"日志文件轮转失败: {e}")

    def handle(self, data: Any) -> None:
        """处理数据（被动模式）"""
        if isinstance(data, dict):
            if "threat_type" in data:
                self._log_threat(data)
            elif "alert_id" in data:
                self._log_alert(data)

    def cleanup(self) -> None:
        """清理资源"""
        self.logger.info(
            f"日志处理器已清理 (威胁: {self.threats_logged}, "
            f"告警: {self.alerts_logged})"
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "threats_logged": self.threats_logged,
            "alerts_logged": self.alerts_logged,
            "enabled": self.enabled
        }
