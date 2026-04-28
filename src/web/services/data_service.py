"""
数据聚合服务
Data Aggregation Service
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ...utils.logger import get_logger


class DataService:
    """数据聚合服务

    提供数据聚合、统计和查询功能
    """

    def __init__(self, web_bridge):
        self.web_bridge = web_bridge
        self.logger = get_logger("data_service")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        try:
            system_status = self.web_bridge.get_system_status()
            alerts = self.web_bridge.get_active_alerts(limit=20)
            threats = self.web_bridge.get_threats(limit=20)
            detector_stats = self.web_bridge.get_detector_stats()
            statistics = self.web_bridge.get_statistics()

            return {
                "system": system_status,
                "alerts": alerts,
                "threats": threats,
                "detectors": detector_stats,
                "statistics": statistics,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取仪表盘数据失败: {e}")
            return {}

    def get_alerts_data(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取告警数据"""
        try:
            alerts = self.web_bridge.get_alerts(limit=limit, status=status, severity=severity)
            return alerts
        except Exception as e:
            self.logger.error(f"获取告警数据失败: {e}")
            return []

    def get_threats_data(
        self,
        limit: int = 100,
        threat_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取威胁数据"""
        try:
            threats = self.web_bridge.get_threats(limit=limit, threat_type=threat_type, severity=severity)
            return threats
        except Exception as e:
            self.logger.error(f"获取威胁数据失败: {e}")
            return []

    def get_traffic_trends(self, hours: int = 24) -> Dict[str, Any]:
        """获取流量趋势"""
        try:
            trends = self.web_bridge.get_traffic_trends(hours=hours)

            # 聚合数据
            hourly_data = defaultdict(lambda: {"count": 0, "by_severity": defaultdict(int)})
            now = datetime.utcnow()

            for trend in trends:
                hour_key = trend.get("timestamp", "")
                if hour_key:
                    hourly_data[hour_key]["count"] += trend.get("count", 0)
                    for severity, count in trend.get("by_severity", {}).items():
                        hourly_data[hour_key]["by_severity"][severity] += count

            # 生成时间序列
            time_series = []
            for i in range(hours):
                hour_time = now - timedelta(hours=hours - i - 1)
                hour_key = hour_time.strftime("%Y-%m-%d %H:00")
                data = hourly_data.get(hour_key, {"count": 0, "by_severity": {}})
                time_series.append({
                    "timestamp": hour_key,
                    "count": data["count"],
                    "by_severity": dict(data["by_severity"])
                })

            return {
                "time_series": time_series,
                "total_events": sum(t["count"] for t in time_series),
                "peak_hour": max(time_series, key=lambda x: x["count"]) if time_series else None
            }
        except Exception as e:
            self.logger.error(f"获取流量趋势失败: {e}")
            return {"time_series": [], "total_events": 0, "peak_hour": None}

    def get_threat_distribution(self) -> Dict[str, Any]:
        """获取威胁分布"""
        try:
            threats = self.web_bridge.get_threats(limit=1000)

            # 按类型分布
            by_type = defaultdict(int)
            # 按严重程度分布
            by_severity = defaultdict(int)
            # 按检测器分布
            by_detector = defaultdict(int)

            for threat in threats:
                threat_type = threat.get("threat_type", "unknown")
                severity = threat.get("severity", "low")
                detector = threat.get("detector", "unknown")

                by_type[threat_type] += 1
                by_severity[severity] += 1
                by_detector[detector] += 1

            return {
                "by_type": dict(by_type),
                "by_severity": dict(by_severity),
                "by_detector": dict(by_detector),
                "total": len(threats)
            }
        except Exception as e:
            self.logger.error(f"获取威胁分布失败: {e}")
            return {"by_type": {}, "by_severity": {}, "by_detector": {}, "total": 0}

    def get_detector_summary(self) -> List[Dict[str, Any]]:
        """获取检测器摘要"""
        try:
            stats = self.web_bridge.get_detector_stats()

            summary = []
            for name, stat in stats.items():
                summary.append({
                    "name": name,
                    "running": stat.get("running", False),
                    "type": stat.get("type", name),
                    "events_processed": stat.get("events_processed", 0),
                    "threats_detected": stat.get("threats_detected", 0),
                    "last_activity": stat.get("last_activity")
                })

            return summary
        except Exception as e:
            self.logger.error(f"获取检测器摘要失败: {e}")
            return []

    def get_timeline_data(
        self,
        hours: int = 24,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取时间线数据"""
        try:
            if event_type == "threat":
                events = self.web_bridge.get_threats(limit=500)
            elif event_type == "alert":
                events = self.web_bridge.get_alerts(limit=500)
            else:
                # 合并所有事件
                threats = self.web_bridge.get_threats(limit=250)
                alerts = self.web_bridge.get_alerts(limit=250)
                events = threats + alerts

            # 过滤时间范围
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            filtered_events = []

            for event in events:
                try:
                    timestamp_str = event.get("timestamp")
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp >= cutoff_time:
                            filtered_events.append(event)
                except Exception:
                    pass

            # 按时间排序
            filtered_events.sort(key=lambda x: x.get("timestamp", ""))

            return filtered_events
        except Exception as e:
            self.logger.error(f"获取时间线数据失败: {e}")
            return []

    def get_statistics_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        try:
            stats = self.web_bridge.get_statistics()

            return {
                "system": {
                    "uptime": stats["system"].get("uptime", 0),
                    "events_processed": stats["system"].get("events_processed", 0),
                    "threats_detected": stats["system"].get("threats_detected", 0)
                },
                "web": {
                    "total_alerts": stats["web"].get("total_alerts", 0),
                    "total_threats": stats["web"].get("total_threats", 0),
                    "active_alerts": stats["web"].get("active_alerts", 0)
                },
                "alerts_by_severity": stats["web"].get("alerts_by_severity", {}),
                "threats_by_type": stats["web"].get("threats_by_type", {}),
                "detectors": list(stats["detectors"].keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"获取统计摘要失败: {e}")
            return {}
