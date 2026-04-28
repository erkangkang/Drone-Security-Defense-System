"""
系统状态API路由
System Status API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...core.web_bridge import get_web_bridge, WebBridge
from ...utils.logger import get_logger
from ..models.responses import SystemStatusResponse, HealthResponse, SuccessResponse
from ..models.requests import ConfigReloadRequest

router = APIRouter()
logger = get_logger("api_system")


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(bridge: WebBridge = Depends(get_web_bridge)) -> Dict[str, Any]:
    """获取系统状态"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        return bridge.get_system_status()
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "drone-security-defense",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/config/reload", response_model=SuccessResponse)
async def reload_config(
    request: ConfigReloadRequest,
    bridge: WebBridge = Depends(get_web_bridge)
) -> Dict[str, Any]:
    """重新加载配置"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        success = bridge.reload_config()
        if success:
            return {
                "success": True,
                "message": "配置重新加载成功"
            }
        else:
            return {
                "success": False,
                "message": "配置重新加载失败"
            }
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_system_info(bridge: WebBridge = Depends(get_web_bridge)) -> Dict[str, Any]:
    """获取系统信息"""
    try:
        if bridge is None:
            raise HTTPException(status_code=503, detail="Web bridge not available")

        status = bridge.get_system_status()
        return {
            "version": "1.0.0",
            "name": "Drone Security Defense System",
            "platform": status.get("platform", "unknown"),
            "detectors": status.get("detectors", []),
            "handlers": status.get("handlers", []),
            "analyzers": status.get("analyzers", [])
        }
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
