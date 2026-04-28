"""
威胁事件模型
Threat Event Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class Severity(Enum):
    """威胁严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """威胁类型"""
    MAVLINK_HIJACKING = "mavlink_hijacking"
    MAVLINK_MITM = "mavlink_mitm"
    MAVLINK_COMMAND_INJECTION = "mavlink_command_injection"
    GPS_SPOOFING = "gps_spoofing"
    GPS_POSITION_JUMP = "gps_position_jump"
    GPS_TIME_SYNC = "gps_time_sync"
    SENSOR_SPOOFING = "sensor_spoofing"
    SENSOR_INCONSISTENCY = "sensor_inconsistency"
    DOS_ATTACK = "dos_attack"
    FIRMWARE_TAMPERING = "firmware_tampering"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


@dataclass
class ThreatEvent:
    """威胁事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    threat_type: str = ""
    severity: Severity = Severity.LOW
    detector: str = ""
    source: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "threat_type": self.threat_type,
            "severity": self.severity.value,
            "detector": self.detector,
            "source": self.source,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "resolved": self.resolved
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThreatEvent":
        """从字典创建"""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            threat_type=data.get("threat_type", ""),
            severity=Severity(data.get("severity", "low")),
            detector=data.get("detector", ""),
            source=data.get("source", ""),
            evidence=data.get("evidence", {}),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {}),
            resolved=data.get("resolved", False)
        )

    def is_critical(self) -> bool:
        """是否为关键威胁"""
        return self.severity == Severity.CRITICAL

    def requires_immediate_action(self) -> bool:
        """是否需要立即采取行动"""
        return self.severity in [Severity.HIGH, Severity.CRITICAL] and self.confidence > 0.8
