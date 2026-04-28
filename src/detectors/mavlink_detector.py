"""
MAVLink 检测器
MAVLink Detector
"""

from typing import Any, Dict, Optional
from collections import deque
import time

from .base_detector import BaseDetector
from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..models.threat_event import ThreatEvent, Severity, ThreatType
from ..models.telemetry import MAVLinkMessage


class MAVLinkDetector(BaseDetector):
    """MAVLink通信检测器"""

    def __init__(self, event_bus: EventBus, config: DetectorConfig):
        super().__init__(event_bus, config)
        self.name = "MAVLinkDetector"

        # 消息跟踪
        self.message_history: deque = deque(maxlen=1000)
        self.sequence_numbers: Dict[tuple, int] = {}
        self.system_ids: Dict[int, int] = {}
        self.component_ids: Dict[tuple, int] = {}
        self.last_message_time: Dict[tuple, float] = {}

        # 配置
        self.max_message_gap = config.settings.get("max_message_gap", 10)
        self.allowed_commands = set(config.settings.get("allowed_commands", []))
        self.allowed_system_ids = set(config.settings.get("allowed_system_ids", [1, 255]))
        self.allowed_component_ids = set(config.settings.get("allowed_component_ids", [1, 50, 190]))

        # 统计
        self.message_rate_history: deque = deque(maxlen=100)
        self.gap_count = 0
        self.unknown_command_count = 0
        self.id_change_count = 0

    def initialize(self) -> bool:
        """初始化检测器"""
        self.logger.info("MAVLink检测器初始化完成")
        return True

    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析MAVLink消息"""
        if not isinstance(data, MAVLinkMessage):
            # 尝试解析原始数据
            mavlink_data = self._parse_mavlink_data(data)
            if not mavlink_data:
                return None
            data = mavlink_data

        # 记录消息历史
        self.message_history.append(data)
        key = (data.sys_id, data.comp_id)

        # 检测序列号异常
        seq_event = self._detect_sequence_anomaly(data, key)
        if seq_event:
            return seq_event

        # 检测系统/组件ID变更
        id_event = self._detect_id_change(data)
        if id_event:
            return id_event

        # 检测异常命令
        cmd_event = self._detect_suspicious_command(data)
        if cmd_event:
            return cmd_event

        # 检测频率异常
        rate_event = self._detect_rate_anomaly(data)
        if rate_event:
            return rate_event

        return None

    def _parse_mavlink_data(self, data: Any) -> Optional[MAVLinkMessage]:
        """解析MAVLink数据"""
        try:
            if isinstance(data, dict):
                return MAVLinkMessage(
                    msg_id=data.get("msg_id", 0),
                    sys_id=data.get("sys_id", 0),
                    comp_id=data.get("comp_id", 0),
                    seq=data.get("seq", 0),
                    payload=data.get("payload", {}),
                    source=data.get("source", "mavlink")
                )
            elif hasattr(data, "__dict__"):
                return MAVLinkMessage(
                    msg_id=getattr(data, "msg_id", 0),
                    sys_id=getattr(data, "sys_id", 0),
                    comp_id=getattr(data, "comp_id", 0),
                    seq=getattr(data, "seq", 0),
                    payload=getattr(data, "payload", {}),
                    source=getattr(data, "source", "mavlink")
                )
        except Exception as e:
            self.logger.error(f"解析MAVLink数据失败: {e}")

        return None

    def _detect_sequence_anomaly(self, msg: MAVLinkMessage, key: tuple) -> Optional[ThreatEvent]:
        """检测序列号异常"""
        if key not in self.sequence_numbers:
            self.sequence_numbers[key] = msg.seq
            return None

        expected_seq = (self.sequence_numbers[key] + 1) % 256
        actual_seq = msg.seq

        # 检测序列号跳变
        gap = (actual_seq - expected_seq) % 256
        if gap > self.max_message_gap:
            self.gap_count += 1
            self.sequence_numbers[key] = actual_seq

            return ThreatEvent(
                threat_type=ThreatType.MAVLINK_HIJACKING.value,
                severity=Severity.MEDIUM,
                detector=self.name,
                source=f"{msg.sys_id}:{msg.comp_id}",
                evidence={
                    "expected_seq": expected_seq,
                    "actual_seq": actual_seq,
                    "gap": gap,
                    "message_id": msg.msg_id
                },
                confidence=min(gap / 50.0, 1.0)
            )

        self.sequence_numbers[key] = actual_seq
        return None

    def _detect_id_change(self, msg: MAVLinkMessage) -> Optional[ThreatEvent]:
        """检测系统/组件ID变更"""
        key = (msg.sys_id, msg.comp_id)

        # 检查系统ID
        if msg.sys_id not in self.allowed_system_ids:
            if msg.sys_id not in self.system_ids:
                self.system_ids[msg.sys_id] = 1
            else:
                self.system_ids[msg.sys_id] += 1

                return ThreatEvent(
                    threat_type=ThreatType.MAVLINK_HIJACKING.value,
                    severity=Severity.HIGH,
                    detector=self.name,
                    source=f"{msg.sys_id}:{msg.comp_id}",
                    evidence={
                        "system_id": msg.sys_id,
                        "allowed_system_ids": list(self.allowed_system_ids),
                        "message_id": msg.msg_id
                    },
                    confidence=0.9
                )

        # 检查组件ID
        if msg.comp_id not in self.allowed_component_ids:
            key_id = (msg.sys_id, msg.comp_id)
            if key_id not in self.component_ids:
                self.component_ids[key_id] = 1
            else:
                self.component_ids[key_id] += 1

                return ThreatEvent(
                    threat_type=ThreatType.MAVLINK_HIJACKING.value,
                    severity=Severity.HIGH,
                    detector=self.name,
                    source=f"{msg.sys_id}:{msg.comp_id}",
                    evidence={
                        "system_id": msg.sys_id,
                        "component_id": msg.comp_id,
                        "allowed_component_ids": list(self.allowed_component_ids),
                        "message_id": msg.msg_id
                    },
                    confidence=0.9
                )

        return None

    def _detect_suspicious_command(self, msg: MAVLinkMessage) -> Optional[ThreatEvent]:
        """检测可疑命令"""
        # MAVLink命令长消息
        if msg.msg_id == 76:  # MAV_CMD_LONG
            command = msg.payload.get("command", 0)

            if self.allowed_commands and command not in self.allowed_commands:
                self.unknown_command_count += 1

                # 连续收到多个未授权命令
                if self.unknown_command_count > 5:
                    return ThreatEvent(
                        threat_type=ThreatType.MAVLINK_COMMAND_INJECTION.value,
                        severity=Severity.CRITICAL,
                        detector=self.name,
                        source=f"{msg.sys_id}:{msg.comp_id}",
                        evidence={
                            "command": command,
                            "allowed_commands": list(self.allowed_commands),
                            "count": self.unknown_command_count,
                            "parameters": msg.payload.get("params", [])
                        },
                        confidence=0.95
                    )

        return None

    def _detect_rate_anomaly(self, msg: MAVLinkMessage) -> Optional[ThreatEvent]:
        """检测消息频率异常"""
        key = (msg.sys_id, msg.comp_id)
        now = time.time()

        if key in self.last_message_time:
            interval = now - self.last_message_time[key]
            self.message_rate_history.append(interval)

            # 计算平均间隔
            if len(self.message_rate_history) > 10:
                avg_interval = sum(self.message_rate_history) / len(self.message_rate_history)

                # 检测突然的高频消息（可能是重放攻击）
                if interval < avg_interval * 0.1 and len(self.message_rate_history) > 50:
                    return ThreatEvent(
                        threat_type=ThreatType.MAVLINK_MITM.value,
                        severity=Severity.MEDIUM,
                        detector=self.name,
                        source=f"{msg.sys_id}:{msg.comp_id}",
                        evidence={
                            "current_interval": interval,
                            "average_interval": avg_interval,
                            "message_id": msg.msg_id
                        },
                        confidence=0.7
                    )

        self.last_message_time[key] = now
        return None

    def _loop_iteration(self):
        """单次迭代（被动模式）"""
        pass

    def cleanup(self) -> None:
        """清理资源"""
        self.message_history.clear()
        self.sequence_numbers.clear()
        self.system_ids.clear()
        self.component_ids.clear()
        self.last_message_time.clear()
        self.message_rate_history.clear()
