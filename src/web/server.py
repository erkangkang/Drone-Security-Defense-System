"""
Web服务器
Web Server
"""

import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from .app import create_app
from .websocket.manager import WebSocketManager
from .websocket.broadcaster import Broadcaster
from .routers import system, alerts, threats, detectors, statistics
from ..core.web_bridge import set_web_bridge
from ..utils.logger import get_logger


class WebServer:
    """Web服务器

    提供RESTful API和WebSocket接口
    """

    def __init__(self, web_bridge, config: Dict[str, Any]):
        self.web_bridge = web_bridge
        self.config = config
        self.logger = get_logger("web_server")

        # 设置全局web_bridge实例
        set_web_bridge(web_bridge)

        # WebSocket管理器
        self.websocket_manager = WebSocketManager()

        # 广播器
        self.broadcaster = Broadcaster(self.websocket_manager, web_bridge)

        # 创建FastAPI应用
        self.app = self._create_app()

        # 服务器线程
        self.server_thread: Optional[threading.Thread] = None
        self.uvicorn_config: Optional[uvicorn.Config] = None
        self.uvicorn_server: Optional[uvicorn.Server] = None

    def _create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        app = create_app(self.config)

        # 包含路由
        app.include_router(
            system.router,
            prefix="/api/system",
            tags=["system"]
        )
        app.include_router(
            alerts.router,
            prefix="/api/alerts",
            tags=["alerts"]
        )
        app.include_router(
            threats.router,
            prefix="/api/threats",
            tags=["threats"]
        )
        app.include_router(
            detectors.router,
            prefix="/api/detectors",
            tags=["detectors"]
        )
        app.include_router(
            statistics.router,
            prefix="/api/statistics",
            tags=["statistics"]
        )

        # WebSocket端点
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.websocket_manager.handle_message(websocket, data)
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)
            except Exception as e:
                self.logger.error(f"WebSocket错误: {e}")
                self.websocket_manager.disconnect(websocket)

        # API信息端点（仅当无前端静态文件时返回JSON）
        static_path = self.config.get("static_files", "src/frontend/dist")
        static_dir = Path(static_path) if static_path else None
        frontend_available = static_dir and static_dir.exists() and any(static_dir.iterdir())

        if not frontend_available:
            @app.get("/")
            async def root():
                return {
                    "message": "Drone Security Defense System API",
                    "docs": "/api/docs",
                    "version": "1.0.0"
                }

        # 静态文件服务（前端构建产物）
        if frontend_available:
            try:
                app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
                self.logger.info(f"静态文件服务已启用: {static_path}")
            except Exception as e:
                self.logger.warning(f"静态文件目录无法加载: {static_path}, 错误: {e}")

        return app

    def run_in_thread(self):
        """在线程中运行服务器"""
        def run_server():
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 配置uvicorn
            self.uvicorn_config = uvicorn.Config(
                self.app,
                host=self.config.get("host", "0.0.0.0"),
                port=self.config.get("port", 8080),
                log_level=self.config.get("log_level", "info").lower(),
                access_log=True,
                loop=loop
            )
            self.uvicorn_server = uvicorn.Server(self.uvicorn_config)

            # 启动广播器
            self.broadcaster.start()

            # 运行服务器
            loop.run_until_complete(self.uvicorn_server.serve())

        self.server_thread = threading.Thread(target=run_server, daemon=True, name="WebServerThread")
        self.server_thread.start()

        self.logger.info(
            f"Web服务器已启动: "
            f"http://{self.config.get('host', '0.0.0.0')}:{self.config.get('port', 8080)}"
        )

    def run(self):
        """直接运行服务器（阻塞模式）"""
        # 启动广播器
        self.broadcaster.start()

        # 配置uvicorn
        self.uvicorn_config = uvicorn.Config(
            self.app,
            host=self.config.get("host", "0.0.0.0"),
            port=self.config.get("port", 8080),
            log_level=self.config.get("log_level", "info").lower(),
            access_log=True
        )
        self.uvicorn_server = uvicorn.Server(self.uvicorn_config)

        # 运行服务器
        uvicorn.run(
            self.app,
            host=self.config.get("host", "0.0.0.0"),
            port=self.config.get("port", 8080),
            log_level=self.config.get("log_level", "info").lower()
        )

    def stop(self):
        """停止服务器"""
        self.logger.info("正在停止Web服务器...")

        # 停止广播器
        if self.broadcaster:
            self.broadcaster.stop()

        # 停止uvicorn服务器
        if self.uvicorn_server:
            self.uvicorn_server.should_exit = True

        # 等待线程结束
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=3.0)

        self.logger.info("Web服务器已停止")

    def get_connection_count(self) -> int:
        """获取WebSocket连接数"""
        return len(self.websocket_manager.active_connections)

    def get_connection_info(self) -> list:
        """获取连接信息"""
        return self.websocket_manager.get_connection_info()
