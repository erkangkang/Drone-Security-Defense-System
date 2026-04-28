"""
检测器控制API路由
Detector Control API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from ...core.web_bridge import get_web_bridge, WebBridge
from ...utils.logger import get_logger
from ..models.responses import DetectorStatusResponse, SuccessResponse
from ..models.requests import DetectorControlRequest

router = APIRouter()
logger = get_logger("api_detectors")


@router.get("/", response_model=List[DetectorStatusResponse])
async def get_detectors(bridge: WebBridge = Depends(get_web_bridge)) -> List[dict]:
    """获取所有检测器状态"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        stats = bridge.get_detector_stats()
        detectors = []

        for name, stat in stats.items():
            detectors.append({
                "name": name,
                "running": stat.get("running", False),
                "enabled": stat.get("enabled", True),
                "type": stat.get("type", name),
                "stats": stat
            })

        return detectors
    except Exception as e:
        logger.error(f"获取检测器列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=DetectorStatusResponse)
async def get_detector(
    name: str,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """获取指定检测器状态"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        status = bridge.get_detector_status(name)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Detector not found: {name}")

        return {
            "name": name,
            "running": status.get("running", False),
            "enabled": status.get("enabled", True),
            "type": status.get("type", name),
            "stats": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取检测器状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/control", response_model=SuccessResponse)
async def control_detector(
    name: str,
    request: DetectorControlRequest,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """控制检测器（启动/停止）"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        if request.action == "start":
            result = bridge.start_detector(name)
        elif request.action == "stop":
            result = bridge.stop_detector(name)
        else:
            return {
                "success": False,
                "message": f"无效的操作: {request.action}，支持的操作: start, stop"
            }

        return result
    except Exception as e:
        logger.error(f"控制检测器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/start", response_model=SuccessResponse)
async def start_detector(
    name: str,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """启动检测器"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        result = bridge.start_detector(name)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动检测器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/stop", response_model=SuccessResponse)
async def stop_detector(
    name: str,
    bridge: WebBridge = Depends(get_web_bridge)
) -> dict:
    """停止检测器"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        result = bridge.stop_detector(name)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止检测器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary")
async def get_detectors_summary(bridge: WebBridge = Depends(get_web_bridge)) -> dict:
    """获取检测器摘要"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        from ..services.data_service import DataService
        service = DataService(bridge)
        summary = service.get_detector_summary()

        return {
            "detectors": summary,
            "total": len(summary),
            "running": sum(1 for d in summary if d["running"])
        }
    except Exception as e:
        logger.error(f"获取检测器摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
