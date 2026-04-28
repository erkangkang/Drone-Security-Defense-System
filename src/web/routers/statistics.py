"""
统计数据API路由
Statistics API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any

from ...core.web_bridge import get_web_bridge, WebBridge
from ...utils.logger import get_logger
from ..models.responses import StatisticsResponse

router = APIRouter()
logger = get_logger("api_statistics")


@router.get("/", response_model=StatisticsResponse)
async def get_statistics(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取统计数据"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)

        stats = bridge.get_statistics()
        traffic_trends = service.get_traffic_trends(hours=hours)
        threat_distribution = service.get_threat_distribution()

        return {
            "total_alerts": stats["web"].get("total_alerts", 0),
            "total_threats": stats["web"].get("total_threats", 0),
            "active_alerts": stats["web"].get("active_alerts", 0),
            "alerts_by_severity": stats["web"].get("alerts_by_severity", {}),
            "threats_by_type": threat_distribution.get("by_type", {}),
            "traffic_trends": traffic_trends.get("time_series", []),
            "detector_stats": stats.get("detectors", {})
        }
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traffic")
async def get_traffic_trends(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取流量趋势"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        return service.get_traffic_trends(hours=hours)
    except Exception as e:
        logger.error(f"获取流量趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threats")
async def get_threat_statistics(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取威胁统计"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        return service.get_threat_distribution()
    except Exception as e:
        logger.error(f"获取威胁统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取仪表盘数据"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        return service.get_dashboard_data()
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_timeline_data(
    hours: int = Query(24, ge=1, le=168, description="统计时间范围（小时）"),
    event_type: str = Query(None, description="事件类型: threat, alert"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取时间线数据"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        events = service.get_timeline_data(hours=hours, event_type=event_type)

        return {
            "events": events,
            "total": len(events),
            "hours": hours,
            "event_type": event_type or "all"
        }
    except Exception as e:
        logger.error(f"获取时间线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
