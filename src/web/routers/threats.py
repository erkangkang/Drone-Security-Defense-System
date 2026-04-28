"""
威胁事件API路由
Threat Events API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...core.web_bridge import get_web_bridge, WebBridge
from ...utils.logger import get_logger
from ..models.responses import ThreatResponse, TimelineResponse

router = APIRouter()
logger = get_logger("api_threats")


@router.get("/", response_model=List[ThreatResponse])
async def get_threats(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    threat_type: Optional[str] = Query(None, description="过滤威胁类型"),
    severity: Optional[str] = Query(None, description="过滤严重程度"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> List[dict]:
    """获取威胁事件列表"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        threats = bridge.get_threats(limit=limit, threat_type=threat_type, severity=severity)
        return threats
    except Exception as e:
        logger.error(f"获取威胁列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline", response_model=TimelineResponse)
async def get_threat_timeline(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取威胁时间线"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        events = bridge.get_threat_timeline(limit=limit)
        return {
            "events": events,
            "total": len(events)
        }
    except Exception as e:
        logger.error(f"获取威胁时间线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_threat_types(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取威胁类型列表"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        distribution = service.get_threat_distribution()

        return {
            "types": list(distribution.get("by_type", {}).keys()),
            "distribution": distribution.get("by_type", {})
        }
    except Exception as e:
        logger.error(f"获取威胁类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribution")
async def get_threat_distribution(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取威胁分布"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        return service.get_threat_distribution()
    except Exception as e:
        logger.error(f"获取威胁分布失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=ThreatResponse)
async def get_threat(
    event_id: str,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取威胁事件详情"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        threats = bridge.get_threats(limit=10000)
        for threat in threats:
            if threat.get("event_id") == event_id:
                return threat

        raise HTTPException(status_code=404, detail="Threat event not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取威胁详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
