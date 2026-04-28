"""
API响应模型
API Response Models
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    running: bool
    platform: str
    detectors: List[str]
    handlers: List[str]
    analyzers: List[str]
    stats: Dict[str, Any]
    web_stats: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    """告警响应"""
    alert_id: str
    threat_type: str
    severity: str
    status: str
    source: str
    timestamp: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    notes: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


class ThreatResponse(BaseModel):
    """威胁事件响应"""
    event_id: str
    threat_type: str
    severity: str
    detector: str
    source: str
    evidence: Dict[str, Any]
    confidence: float
    timestamp: str
    resolved: bool = False


class DetectorStatusResponse(BaseModel):
    """检测器状态响应"""
    name: str
    running: bool
    enabled: bool
    type: str
    stats: Dict[str, Any]


class StatisticsResponse(BaseModel):
    """统计响应"""
    total_alerts: int
    total_threats: int
    active_alerts: int
    alerts_by_severity: Dict[str, int]
    threats_by_type: Dict[str, int]
    traffic_trends: List[Dict[str, Any]]
    detector_stats: Dict[str, Any]


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    timestamp: str


class TimelineResponse(BaseModel):
    """时间线响应"""
    events: List[Dict[str, Any]]
    total: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
