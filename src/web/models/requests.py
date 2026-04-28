"""
API请求模型
API Request Models
"""

from pydantic import BaseModel, Field
from typing import Optional


class AcknowledgeRequest(BaseModel):
    """告警确认请求"""
    user: str = Field(default="web", description="确认用户")
    notes: str = Field(default="", description="备注信息")


class ResolveRequest(BaseModel):
    """告警解决请求"""
    user: str = Field(default="web", description="解决用户")


class FalsePositiveRequest(BaseModel):
    """误报标记请求"""
    user: str = Field(default="web", description="操作用户")


class DetectorControlRequest(BaseModel):
    """检测器控制请求"""
    action: str = Field(..., description="操作类型: start 或 stop")


class ConfigReloadRequest(BaseModel):
    """配置重新加载请求"""
    force: bool = Field(default=False, description="强制重新加载")


class TimelineRequest(BaseModel):
    """时间线请求"""
    start_time: Optional[str] = Field(None, description="开始时间 (ISO 8601)")
    end_time: Optional[str] = Field(None, description="结束时间 (ISO 8601)")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")


class StatisticsRequest(BaseModel):
    """统计请求"""
    hours: int = Field(default=24, ge=1, le=168, description="统计时间范围（小时）")
    group_by: Optional[str] = Field(None, description="分组方式: severity, type, detector")
