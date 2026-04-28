"""
Web服务器桥接模块
Web Server Bridge Module
"""

import threading
from collections import deque
from typing import Dict, Any, Optional, List
from datetime import datetime

from .event_bus import Event
from ..utils.logger import get_logger


class WebDataManager:
    """线程安全的Web数据管理器"""

    def __init__(self, max_alerts: int = 1000, max_threats: int = 1000, max_events: int = 5000):
        self.max_alerts = max_alerts
        self.max_threats = max_threats
        self.max_events = max_events

        # 使用deque存储数据
        self.alerts = deque(maxlen=max_alerts)
        self.threats = deque(maxlen=max_threats)
        self.events_history = deque(maxlen=max_events)

        # 线程锁
        self.lock = threading.Lock()

        # 实时统计
        self.stats = {
            "total_alerts": 0,
            "total_threats": 0,
            "alerts_by_severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "threats_by_type": {},
            "traffic_timeline": []
        }

    def add_alert(self, alert: dict):
        """添加告警"""
        with self.lock:
            self.alerts.append(alert)
            self.stats["total_alerts"] += 1

            # 更新严重程度统计
            severity = alert.get("severity", "low")
            if severity in self.stats["alerts_by_severity"]:
                self.stats["alerts_by_severity"][severity] += 1

    def add_threat(self, threat: dict):
        """添加威胁"""
        with self.lock:
            self.threats.append(threat)
            self.stats["total_threats"] += 1

            # 更新威胁类型统计
            threat_type = threat.get("threat_type", "unknown")
            if threat_type not in self.stats["threats_by_type"]:
                self.stats["threats_by_type"][threat_type] = 0
            self.stats["threats_by_type"][threat_type] += 1

            # 添加到事件历史
            event_record = {
                "type": "threat",
                "timestamp": threat.get("timestamp"),
                "data": threat
            }
            self.events_history.append(event_record)

            # 更新流量时间线（保留最近100个数据点）
            self._update_traffic_timeline(threat)

    def add_event(self, event_type: str, data: dict):
        """添加事件"""
        with self.lock:
            event_record = {
                "type": event_type,
                "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
                "data": data
            }
            self.events_history.append(event_record)

    def _update_traffic_timeline(self, threat: dict):
        """更新流量时间线"""
        timestamp = threat.get("timestamp", datetime.utcnow().isoformat())
        self.stats["traffic_timeline"].append({
            "timestamp": timestamp,
            "threat_type": threat.get("threat_type"),
            "severity": threat.get("severity")
        })

        # 限制时间线长度
        if len(self.stats["traffic_timeline"]) > 100:
            self.stats["traffic_timeline"] = self.stats["traffic_timeline"][-100:]

    def get_recent_alerts(self, limit: int = 100, status: str = None) -> List[dict]:
        """获取最近的告警"""
        with self.lock:
            alerts = list(self.alerts)
            if status:
                alerts = [a for a in alerts if a.get("status") == status]
            return alerts[-limit:]

    def get_recent_threats(self, limit: int = 100) -> List[dict]:
        """获取最近的威胁"""
        with self.lock:
            return list(self.threats)[-limit:]

    def get_events_history(self, limit: int = 100, event_type: str = None) -> List[dict]:
        """获取事件历史"""
        with self.lock:
            events = list(self.events_history)
            if event_type:
                events = [e for e in events if e["type"] == event_type]
            return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                "total_alerts": self.stats["total_alerts"],
                "total_threats": self.stats["total_threats"],
                "alerts_by_severity": self.stats["alerts_by_severity"].copy(),
                "threats_by_type": self.stats["threats_by_type"].copy(),
                "active_alerts": sum(1 for a in self.alerts if a.get("status") == "new"),
                "traffic_timeline": self.stats["traffic_timeline"][-50:]
            }


class WebBridge:
    """Web服务器桥接模块

    连接守护进程和Web服务器，提供数据访问和控制接口
    """

    def __init__(self, daemon):
        self.daemon = daemon
        self.event_bus = daemon.event_bus
        self.data_manager = WebDataManager()
        self.logger = get_logger("web_bridge")

        # 订阅事件
        self._subscribe_events()

        # 全局实例引用（用于依赖注入）
        _web_bridge_instance = self

    def _subscribe_events(self):
        """订阅关键事件"""
        # 威胁检测事件
        self.event_bus.subscribe("threat.detected", self._on_threat_detected, async_mode=True)

        # 告警创建事件
        self.event_bus.subscribe("alert.created", self._on_alert_created, async_mode=True)

        # IP阻断事件
        self.event_bus.subscribe("block.ip", self._on_block_ip, async_mode=True)

        # 系统状态更新
        self.event_bus.subscribe("system.status", self._on_system_status, async_mode=True)

        self.logger.info("Web桥接模块已订阅事件")

    def _on_threat_detected(self, event: Event):
        """威胁检测事件处理"""
        try:
            event_data = event.data
            if isinstance(event_data, dict):
                threat_data = {
                    "event_id": event_data.get("event_id"),
                    "threat_type": event_data.get("threat_type", ""),
                    "severity": event_data.get("severity", "low"),
                    "detector": event_data.get("detector", ""),
                    "source": event_data.get("source", ""),
                    "evidence": event_data.get("evidence", {}),
                    "confidence": event_data.get("confidence", 1.0),
                    "timestamp": event_data.get("timestamp", datetime.utcnow().isoformat())
                }
                self.data_manager.add_threat(threat_data)
        except Exception as e:
            self.logger.error(f"处理威胁检测事件失败: {e}")

    def _on_alert_created(self, event: Event):
        """告警创建事件处理"""
        try:
            event_data = event.data
            if isinstance(event_data, dict):
                alert_data = {
                    "alert_id": event_data.get("alert_id"),
                    "threat_type": event_data.get("threat_type", ""),
                    "severity": event_data.get("severity", "low"),
                    "status": "new",
                    "source": event_data.get("source", ""),
                    "timestamp": event_data.get("timestamp", datetime.utcnow().isoformat())
                }
                self.data_manager.add_alert(alert_data)
        except Exception as e:
            self.logger.error(f"处理告警创建事件失败: {e}")

    def _on_block_ip(self, event: Event):
        """IP阻断事件处理"""
        try:
            event_data = event.data
            if isinstance(event_data, dict):
                self.data_manager.add_event("block_ip", event_data)
        except Exception as e:
            self.logger.error(f"处理IP阻断事件失败: {e}")

    def _on_system_status(self, event: Event):
        """系统状态更新事件处理"""
        try:
            event_data = event.data
            if isinstance(event_data, dict):
                self.data_manager.add_event("system_status", event_data)
        except Exception as e:
            self.logger.error(f"处理系统状态事件失败: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = self.daemon.get_status()
        # 添加Web数据管理器统计
        status["web_stats"] = self.data_manager.get_stats()
        return status

    def get_alerts(self, limit: int = 100, status: str = None, severity: str = None) -> List[dict]:
        """获取告警列表"""
        # 首先从告警处理器获取
        alert_handler = self.daemon.handlers.get("alert")
        alerts = []

        if alert_handler and hasattr(alert_handler, "get_alerts"):
            alerts = alert_handler.get_alerts(severity=severity, limit=limit)
        else:
            # 从数据管理器获取
            alerts = self.data_manager.get_recent_alerts(limit=limit, status=status)

        # 过滤状态
        if status:
            alerts = [a for a in alerts if a.get("status") == status]

        return alerts

    def get_active_alerts(self, limit: int = 50) -> List[dict]:
        """获取活跃告警"""
        alert_handler = self.daemon.handlers.get("alert")
        if alert_handler and hasattr(alert_handler, "get_active_alerts"):
            return alert_handler.get_active_alerts()[:limit]
        return self.data_manager.get_recent_alerts(limit=limit, status="new")

    def acknowledge_alert(self, alert_id: str, user: str = "web", notes: str = "") -> bool:
        """确认告警"""
        alert_handler = self.daemon.handlers.get("alert")
        if alert_handler and hasattr(alert_handler, "acknowledge_alert"):
            success = alert_handler.acknowledge_alert(alert_id, user, notes)
            if success:
                self.logger.info(f"告警已确认: {alert_id} by {user}")
            return success
        return False

    def resolve_alert(self, alert_id: str, user: str = "web") -> bool:
        """解决告警"""
        alert_handler = self.daemon.handlers.get("alert")
        if alert_handler and hasattr(alert_handler, "resolve_alert"):
            success = alert_handler.resolve_alert(alert_id)
            if success:
                self.logger.info(f"告警已解决: {alert_id} by {user}")
            return success
        return False

    def mark_false_positive(self, alert_id: str, user: str = "web") -> bool:
        """标记为误报"""
        alert_handler = self.daemon.handlers.get("alert")
        if alert_handler and hasattr(alert_handler, "mark_false_positive"):
            success = alert_handler.mark_false_positive(alert_id)
            if success:
                self.logger.info(f"告警已标记为误报: {alert_id} by {user}")
            return success
        return False

    def get_threats(self, limit: int = 100, threat_type: str = None, severity: str = None) -> List[dict]:
        """获取威胁事件列表"""
        threats = self.data_manager.get_recent_threats(limit=limit)

        if threat_type:
            threats = [t for t in threats if t.get("threat_type") == threat_type]

        if severity:
            threats = [t for t in threats if t.get("severity") == severity]

        return threats

    def get_threat_timeline(self, limit: int = 100) -> List[dict]:
        """获取威胁时间线"""
        return self.data_manager.get_events_history(limit=limit, event_type="threat")

    def get_detector_stats(self) -> Dict[str, Any]:
        """获取检测器统计"""
        stats = {}
        for name, detector in self.daemon.detectors.items():
            if hasattr(detector, "get_stats"):
                detector_stats = detector.get_stats()
                stats[name] = detector_stats
            else:
                stats[name] = {
                    "running": getattr(detector, "running", False),
                    "enabled": True,
                    "type": name
                }
        return stats

    def get_detector_status(self, name: str) -> Optional[Dict[str, Any]]:
        """获取单个检测器状态"""
        detector = self.daemon.detectors.get(name)
        if detector:
            if hasattr(detector, "get_stats"):
                return detector.get_stats()
            return {
                "running": getattr(detector, "running", False),
                "enabled": True,
                "type": name
            }
        return None

    def start_detector(self, name: str) -> Dict[str, Any]:
        """启动检测器"""
        result = {"success": False, "message": ""}

        detector = self.daemon.detectors.get(name)
        if detector is None:
            result["message"] = f"检测器不存在: {name}"
            return result

        if hasattr(detector, "start"):
            if not getattr(detector, "running", False):
                try:
                    detector.start()
                    result["success"] = True
                    result["message"] = f"检测器已启动: {name}"
                    self.logger.info(f"检测器已启动: {name}")
                except Exception as e:
                    result["message"] = f"启动检测器失败: {e}"
            else:
                result["message"] = f"检测器已在运行: {name}"
        else:
            result["message"] = f"检测器不支持启动操作: {name}"

        return result

    def stop_detector(self, name: str) -> Dict[str, Any]:
        """停止检测器"""
        result = {"success": False, "message": ""}

        detector = self.daemon.detectors.get(name)
        if detector is None:
            result["message"] = f"检测器不存在: {name}"
            return result

        if hasattr(detector, "stop"):
            if getattr(detector, "running", False):
                try:
                    detector.stop()
                    result["success"] = True
                    result["message"] = f"检测器已停止: {name}"
                    self.logger.info(f"检测器已停止: {name}")
                except Exception as e:
                    result["message"] = f"停止检测器失败: {e}"
            else:
                result["message"] = f"检测器未运行: {name}"
        else:
            result["message"] = f"检测器不支持停止操作: {name}"

        return result

    def reload_config(self) -> bool:
        """重新加载配置"""
        return self.daemon.reload_config()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        stats = {
            "system": self.daemon.stats.copy(),
            "web": self.data_manager.get_stats(),
            "detectors": self.get_detector_stats(),
            "handlers": {}
        }

        # 获取处理器统计
        for name, handler in self.daemon.handlers.items():
            if hasattr(handler, "get_statistics"):
                stats["handlers"][name] = handler.get_statistics()

        return stats

    def get_traffic_trends(self, hours: int = 24) -> List[dict]:
        """获取流量趋势"""
        timeline = self.data_manager.get_events_history(limit=500, event_type="threat")

        # 按小时聚合
        trends = {}
        for event in timeline:
            timestamp = event.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                hour_key = dt.strftime("%Y-%m-%d %H:00")

                if hour_key not in trends:
                    trends[hour_key] = {"timestamp": hour_key, "count": 0, "by_severity": {}}

                trends[hour_key]["count"] += 1

                # 按严重程度统计
                severity = event.get("data", {}).get("severity", "low")
                if severity not in trends[hour_key]["by_severity"]:
                    trends[hour_key]["by_severity"][severity] = 0
                trends[hour_key]["by_severity"][severity] += 1

            except Exception:
                pass

        return list(trends.values())[-hours:]


# 全局实例引用（用于依赖注入）
_web_bridge_instance: Optional[WebBridge] = None


def get_web_bridge() -> Optional[WebBridge]:
    """获取Web桥接实例"""
    return _web_bridge_instance


def set_web_bridge(bridge: WebBridge):
    """设置Web桥接实例"""
    global _web_bridge_instance
    _web_bridge_instance = bridge
