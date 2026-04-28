"""
告警模型
Alert Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid

from .threat_event import ThreatEvent


class AlertStatus(Enum):
    """告警状态"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass
class Alert:
    """安全告警"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: ThreatEvent = field(default=None)
    status: AlertStatus = AlertStatus.NEW
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notes: str = ""

    def acknowledge(self, user: str, notes: str = "") -> None:
        """确认告警"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user
        self.notes = notes

    def resolve(self) -> None:
        """解决告警"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

    def mark_false_positive(self) -> None:
        """标记为误报"""
        self.status = AlertStatus.FALSE_POSITIVE
        self.resolved_at = datetime.utcnow()

    def is_active(self) -> bool:
        """是否为活跃告警"""
        return self.status == AlertStatus.NEW

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_id": self.alert_id,
            "event": self.event.to_dict() if self.event else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "notes": self.notes
        }
