"""
FastAPI应用配置
FastAPI Application Configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from ..utils.logger import get_logger


def create_app(web_config: Dict[str, Any]) -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="Drone Security Defense System",
        version="1.0.0",
        description="无人机安全防御系统 Web API",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=web_config.get("cors_origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册启动和关闭事件
    @app.on_event("startup")
    async def startup_event():
        logger = get_logger("web_app")
        logger.info("FastAPI应用启动")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger = get_logger("web_app")
        logger.info("FastAPI应用关闭")

    return app
