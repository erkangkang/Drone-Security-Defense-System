"""
告警管理API路由
Alert Management API Router
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...core.web_bridge import get_web_bridge, WebBridge
from ...utils.logger import get_logger
from ..models.responses import AlertResponse, SuccessResponse
from ..models.requests import AcknowledgeRequest, ResolveRequest, FalsePositiveRequest

router = APIRouter()
logger = get_logger("api_alerts")


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    status: Optional[str] = Query(None, description="过滤状态"),
    severity: Optional[str] = Query(None, description="过滤严重程度"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> List[dict]:
    """获取告警列表"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        alerts = bridge.get_alerts(limit=limit, status=status, severity=severity)
        return alerts
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(
    limit: int = Query(50, ge=1, le=500, description="返回数量限制"),
    bridge: WebBridge = Depends(get_web_bridge)
) -> List[dict]:
    """获取活跃告警"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        alerts = bridge.get_active_alerts(limit=limit)
        return alerts
    except Exception as e:
        logger.error(f"获取活跃告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取告警详情"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        alerts = bridge.get_alerts(limit=10000)
        for alert in alerts:
            if alert.get("alert_id") == alert_id:
                return alert

        raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取告警详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge", response_model=SuccessResponse)
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeRequest,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """确认告警"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.alert_service import AlertService
        service = AlertService(bridge)
        result = service.acknowledge_alert(alert_id, request.user, request.notes)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("message", "Alert not found"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve", response_model=SuccessResponse)
async def resolve_alert(
    alert_id: str,
    request: ResolveRequest,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """解决告警"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.alert_service import AlertService
        service = AlertService(bridge)
        result = service.resolve_alert(alert_id, request.user)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("message", "Alert not found"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/false_positive", response_model=SuccessResponse)
async def mark_false_positive(
    alert_id: str,
    request: FalsePositiveRequest,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """标记为误报"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.alert_service import AlertService
        service = AlertService(bridge)
        result = service.mark_false_positive(alert_id, request.user)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result.get("message", "Alert not found"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记误报失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary")
async def get_alert_statistics(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取告警统计"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.alert_service import AlertService
        service = AlertService(bridge)
        return service.get_alert_statistics()
    except Exception as e:
        logger.error(f"获取告警统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
