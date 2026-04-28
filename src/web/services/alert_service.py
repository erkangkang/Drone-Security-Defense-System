"""
告警服务
Alert Service
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ...utils.logger import get_logger


class AlertService:
    """告警服务

    提供告警管理功能
    """

    def __init__(self, web_bridge):
        self.web_bridge = web_bridge
        self.logger = get_logger("alert_service")

    def acknowledge_alert(
        self,
        alert_id: str,
        user: str = "web",
        notes: str = ""
    ) -> Dict[str, Any]:
        """确认告警"""
        try:
            success = self.web_bridge.acknowledge_alert(alert_id, user, notes)
            if success:
                return {
                    "success": True,
                    "message": f"告警已确认: {alert_id}",
                    "alert_id": alert_id,
                    "acknowledged_by": user,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "告警确认失败，可能告警不存在或已处理",
                    "alert_id": alert_id
                }
        except Exception as e:
            self.logger.error(f"确认告警失败: {e}")
            return {
                "success": False,
                "message": f"确认告警时发生错误: {str(e)}",
                "alert_id": alert_id
            }

    def resolve_alert(self, alert_id: str, user: str = "web") -> Dict[str, Any]:
        """解决告警"""
        try:
            success = self.web_bridge.resolve_alert(alert_id, user)
            if success:
                return {
                    "success": True,
                    "message": f"告警已解决: {alert_id}",
                    "alert_id": alert_id,
                    "resolved_by": user,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "告警解决失败，可能告警不存在",
                    "alert_id": alert_id
                }
        except Exception as e:
            self.logger.error(f"解决告警失败: {e}")
            return {
                "success": False,
                "message": f"解决告警时发生错误: {str(e)}",
                "alert_id": alert_id
            }

    def mark_false_positive(self, alert_id: str, user: str = "web") -> Dict[str, Any]:
        """标记为误报"""
        try:
            success = self.web_bridge.mark_false_positive(alert_id, user)
            if success:
                return {
                    "success": True,
                    "message": f"告警已标记为误报: {alert_id}",
                    "alert_id": alert_id,
                    "marked_by": user,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "标记失败，可能告警不存在",
                    "alert_id": alert_id
                }
        except Exception as e:
            self.logger.error(f"标记误报失败: {e}")
            return {
                "success": False,
                "message": f"标记误报时发生错误: {str(e)}",
                "alert_id": alert_id
            }

    def batch_acknowledge(
        self,
        alert_ids: List[str],
        user: str = "web",
        notes: str = ""
    ) -> Dict[str, Any]:
        """批量确认告警"""
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }

        for alert_id in alert_ids:
            result = self.acknowledge_alert(alert_id, user, notes)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            results["details"].append(result)

        return {
            "total": len(alert_ids),
            "success": results["success"],
            "failed": results["failed"],
            "details": results["details"]
        }

    def batch_resolve(
        self,
        alert_ids: List[str],
        user: str = "web"
    ) -> Dict[str, Any]:
        """批量解决告警"""
        results = {
            "success": 0,
            "failed": 0,
            "details": []
        }

        for alert_id in alert_ids:
            result = self.resolve_alert(alert_id, user)
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            results["details"].append(result)

        return {
            "total": len(alert_ids),
            "success": results["success"],
            "failed": results["failed"],
            "details": results["details"]
        }

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        try:
            alerts = self.web_bridge.get_alerts(limit=10000)

            # 按状态统计
            by_status = {}
            # 按严重程度统计
            by_severity = {}
            # 按类型统计
            by_type = {}
            # 按来源统计
            by_source = {}

            for alert in alerts:
                status = alert.get("status", "unknown")
                severity = alert.get("severity", "low")
                alert_type = alert.get("threat_type", "unknown")
                source = alert.get("source", "unknown")

                by_status[status] = by_status.get(status, 0) + 1
                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_type[alert_type] = by_type.get(alert_type, 0) + 1
                by_source[source] = by_source.get(source, 0) + 1

            return {
                "total": len(alerts),
                "by_status": by_status,
                "by_severity": by_severity,
                "by_type": by_type,
                "by_source": by_source,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取告警统计失败: {e}")
            return {}

    def get_alert_detail(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """获取告警详情"""
        try:
            alerts = self.web_bridge.get_alerts(limit=10000)
            for alert in alerts:
                if alert.get("alert_id") == alert_id:
                    return alert
            return None
        except Exception as e:
            self.logger.error(f"获取告警详情失败: {e}")
            return None
