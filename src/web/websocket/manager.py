"""
WebSocket连接管理器
WebSocket Connection Manager
"""

import json
import asyncio
from typing import List, Set, Dict, Any, Optional
from datetime import datetime

from fastapi import WebSocket

from ...utils.logger import get_logger


class WebSocketManager:
    """WebSocket连接管理器

    管理WebSocket客户端连接、消息处理和广播
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        self.logger = get_logger("websocket_manager")

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None):
        """接受新连接"""
        await websocket.accept()

        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

        # 记录连接信息
        self.connection_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.utcnow().isoformat(),
            "messages_sent": 0,
            "messages_received": 0
        }

        self.logger.info(
            f"WebSocket连接建立: {self.connection_info[websocket]['client_id']}, "
            f"活跃连接: {len(self.active_connections)}"
        )

        # 发送欢迎消息
        await self._send_to_connection(websocket, {
            "type": "connected",
            "client_id": self.connection_info[websocket]["client_id"],
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        client_id = None

        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_info:
            client_id = self.connection_info[websocket]["client_id"]
            del self.connection_info[websocket]

        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

        if client_id:
            self.logger.info(
                f"WebSocket断开: {client_id}, "
                f"活跃连接: {len(self.active_connections)}"
            )

    async def handle_message(self, websocket: WebSocket, message: str):
        """处理客户端消息"""
        if websocket in self.connection_info:
            self.connection_info[websocket]["messages_received"] += 1

        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    self.subscriptions[websocket].add(channel)
                self.logger.info(
                    f"客户端 {self.connection_info.get(websocket, {}).get('client_id', 'unknown')} "
                    f"订阅频道: {channels}"
                )
                await self._send_to_connection(websocket, {
                    "type": "subscribed",
                    "channels": channels
                })

            elif action == "unsubscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    self.subscriptions[websocket].discard(channel)
                await self._send_to_connection(websocket, {
                    "type": "unsubscribed",
                    "channels": channels
                })

            elif action == "ping":
                await self._send_to_connection(websocket, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif action == "get_status":
                await self._send_to_connection(websocket, {
                    "type": "status",
                    "subscriptions": list(self.subscriptions.get(websocket, set())),
                    "active_connections": len(self.active_connections)
                })

            else:
                await self._send_error(websocket, f"未知操作: {action}")

        except json.JSONDecodeError:
            self.logger.error(f"无效的JSON消息: {message}")
            await self._send_error(websocket, "无效的JSON格式")
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            await self._send_error(websocket, str(e))

    async def _send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]):
        """发送消息到指定连接"""
        try:
            message = json.dumps(data, ensure_ascii=False, default=str)
            await websocket.send_text(message)

            if websocket in self.connection_info:
                self.connection_info[websocket]["messages_sent"] += 1

        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.disconnect(websocket)

    async def _send_error(self, websocket: WebSocket, message: str):
        """发送错误消息"""
        await self._send_to_connection(websocket, {
            "type": "error",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def broadcast(self, message: Dict[str, Any], channel: Optional[str] = None):
        """广播消息到所有订阅的客户端"""
        if not self.active_connections:
            return

        # 添加时间戳
        message["timestamp"] = datetime.utcnow().isoformat()

        message_str = json.dumps(message, ensure_ascii=False, default=str)
        failed_connections = []

        for connection in self.active_connections:
            # 如果指定了频道，检查客户端是否订阅
            if channel and channel not in self.subscriptions.get(connection, set()):
                continue

            try:
                await connection.send_text(message_str)

                if connection in self.connection_info:
                    self.connection_info[connection]["messages_sent"] += 1

            except Exception as e:
                self.logger.error(f"广播消息失败: {e}")
                failed_connections.append(connection)

        # 清理失败的连接
        for connection in failed_connections:
            self.disconnect(connection)

    async def broadcast_threat(self, threat: Dict[str, Any]):
        """广播威胁事件"""
        await self.broadcast({
            "type": "threat.detected",
            "data": threat
        }, channel="threats")

    async def broadcast_alert(self, alert: Dict[str, Any]):
        """广播告警事件"""
        await self.broadcast({
            "type": "alert.created",
            "data": alert
        }, channel="alerts")

    async def broadcast_system_update(self, status: Dict[str, Any]):
        """广播系统状态更新"""
        await self.broadcast({
            "type": "system.update",
            "data": status
        }, channel="system")

    async def broadcast_detector_status(self, detector_name: str, status: Dict[str, Any]):
        """广播检测器状态更新"""
        await self.broadcast({
            "type": "detector.update",
            "detector": detector_name,
            "data": status
        }, channel="detectors")

    def get_subscribers(self, channel: str) -> int:
        """获取指定频道的订阅者数量"""
        count = 0
        for subscriptions in self.subscriptions.values():
            if channel in subscriptions:
                count += 1
        return count

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取所有连接信息"""
        return [
            {
                **info,
                "subscriptions": list(self.subscriptions.get(ws, set()))
            }
            for ws, info in self.connection_info.items()
        ]
