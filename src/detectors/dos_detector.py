"""
DoS 攻击检测器
DoS Attack Detector
"""

import time
from typing import Any, Dict, Optional, Tuple
from collections import deque, defaultdict

from .base_detector import BaseDetector
from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..models.threat_event import ThreatEvent, Severity, ThreatType
from ..models.telemetry import NetworkConnection


class DOSDetector(BaseDetector):
    """拒绝服务攻击检测器"""

    def __init__(self, event_bus: EventBus, config: DetectorConfig):
        super().__init__(event_bus, config)
        self.name = "DOSDetector"

        # 连接跟踪
        self.connection_history: deque = deque(maxlen=1000)
        self.ip_connection_count: defaultdict = defaultdict(lambda: deque(maxlen=100))
        self.connection_timestamps: deque = deque(maxlen=1000)

        # 配置
        self.max_connections_per_second = config.settings.get("max_connections_per_second", 10)
        self.max_connections_per_minute = config.settings.get("max_connections_per_minute", 100)
        self.max_requests_per_second = config.settings.get("max_requests_per_second", 50)
        self.block_duration = config.settings.get("block_duration", 300)  # 秒

        # IP黑名单
        self.blocked_ips: Dict[str, float] = {}

        # 统计
        self.total_connections = 0
        self.total_requests = 0
        self.attack_count = 0

    def initialize(self) -> bool:
        """初始化检测器"""
        self.logger.info("DoS检测器初始化完成")
        return True

    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析网络连接"""
        if not isinstance(data, NetworkConnection):
            conn_data = self._parse_connection_data(data)
            if not conn_data:
                return None
            data = conn_data

        # 检查是否被阻止
        if data.source_ip in self.blocked_ips:
            block_time = self.blocked_ips[data.source_ip]
            if time.time() - block_time < self.block_duration:
                return None
            else:
                del self.blocked_ips[data.source_ip]

        # 记录连接
        self.connection_history.append(data)
        self.ip_connection_count[data.source_ip].append(time.time())
        self.connection_timestamps.append(time.time())
        self.total_connections += 1

        # 检测连接
        rate_event = self._detect_connection_rate(data)
        if rate_event:
            return rate_event

        # 检测IP洪泛
        flood_event = self._detect_ip_flood(data)
        if flood_event:
            return flood_event

        return None

    def _parse_connection_data(self, data: Any) -> Optional[NetworkConnection]:
        """解析连接数据"""
        try:
            if isinstance(data, dict):
                return NetworkConnection(
                    source_ip=data.get("source_ip", ""),
                    source_port=data.get("source_port", 0),
                    dest_ip=data.get("dest_ip", ""),
                    dest_port=data.get("dest_port", 0),
                    protocol=data.get("protocol", ""),
                    bytes_sent=data.get("bytes_sent", 0),
                    bytes_received=data.get("bytes_received", 0)
                )
            elif hasattr(data, "__dict__"):
                return NetworkConnection(
                    source_ip=getattr(data, "source_ip", ""),
                    source_port=getattr(data, "source_port", 0),
                    dest_ip=getattr(data, "dest_ip", ""),
                    dest_port=getattr(data, "dest_port", 0),
                    protocol=getattr(data, "protocol", ""),
                    bytes_sent=getattr(data, "bytes_sent", 0),
                    bytes_received=getattr(data, "bytes_received", 0)
                )
        except Exception as e:
            self.logger.error(f"解析连接数据失败: {e}")

        return None

    def _detect_connection_rate(self, conn: NetworkConnection) -> Optional[ThreatEvent]:
        """检测连接速率异常"""
        now = time.time()

        # 检查每秒连接数
        recent_connections = [t for t in self.connection_timestamps if now - t < 1.0]
        connections_per_second = len(recent_connections)

        if connections_per_second > self.max_connections_per_second:
            self.attack_count += 1
            confidence = min(connections_per_second / (self.max_connections_per_second * 2), 1.0)

            return ThreatEvent(
                threat_type=ThreatType.DOS_ATTACK.value,
                severity=Severity.HIGH if confidence > 0.8 else Severity.MEDIUM,
                detector=self.name,
                source=conn.source_ip,
                evidence={
                    "connections_per_second": connections_per_second,
                    "max_allowed": self.max_connections_per_second,
                    "protocol": conn.protocol,
                    "dest_port": conn.dest_port
                },
                confidence=confidence
            )

        return None

    def _detect_ip_flood(self, conn: NetworkConnection) -> Optional[ThreatEvent]:
        """检测IP洪泛攻击"""
        ip = conn.source_ip
        now = time.time()
        timestamps = self.ip_connection_count[ip]

        # 检查单IP每秒连接数
        recent_connections = [t for t in timestamps if now - t < 1.0]
        connections_per_second = len(recent_connections)

        if connections_per_second > self.max_requests_per_second:
            self.attack_count += 1

            # 自动阻止该IP
            self.blocked_ips[ip] = now

            return ThreatEvent(
                threat_type=ThreatType.DOS_ATTACK.value,
                severity=Severity.CRITICAL,
                detector=self.name,
                source=ip,
                evidence={
                    "ip": ip,
                    "connections_per_second": connections_per_second,
                    "max_allowed": self.max_requests_per_second,
                    "protocol": conn.protocol,
                    "action": "blocked"
                },
                confidence=0.95
            )

        # 检查单IP每分钟连接数
        recent_connections_minute = [t for t in timestamps if now - t < 60.0]
        connections_per_minute = len(recent_connections_minute)

        if connections_per_minute > self.max_connections_per_minute:
            self.attack_count += 1

            return ThreatEvent(
                threat_type=ThreatType.DOS_ATTACK.value,
                severity=Severity.HIGH,
                detector=self.name,
                source=ip,
                evidence={
                    "ip": ip,
                    "connections_per_minute": connections_per_minute,
                    "max_allowed": self.max_connections_per_minute,
                    "protocol": conn.protocol
                },
                confidence=0.8
            )

        return None

    def _loop_iteration(self):
        """单次迭代"""
        # 定期清理过期的阻止记录
        now = time.time()
        expired_ips = [
            ip for ip, block_time in self.blocked_ips.items()
            if now - block_time > self.block_duration
        ]
        for ip in expired_ips:
            del self.blocked_ips[ip]

    def cleanup(self) -> None:
        """清理资源"""
        self.connection_history.clear()
        self.ip_connection_count.clear()
        self.connection_timestamps.clear()
        self.blocked_ips.clear()

    def is_ip_blocked(self, ip: str) -> bool:
        """检查IP是否被阻止"""
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if time.time() - block_time < self.block_duration:
                return True
            else:
                del self.blocked_ips[ip]
        return False

    def block_ip(self, ip: str) -> None:
        """阻止IP"""
        self.blocked_ips[ip] = time.time()
        self.logger.warning(f"IP已被阻止: {ip}")

    def unblock_ip(self, ip: str) -> None:
        """取消阻止IP"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            self.logger.info(f"IP解除阻止: {ip}")

    def get_blocked_ips(self) -> list:
        """获取被阻止的IP列表"""
        now = time.time()
        return [
            {"ip": ip, "remaining": self.block_duration - (now - t)}
            for ip, t in self.blocked_ips.items()
            if now - t < self.block_duration
        ]
