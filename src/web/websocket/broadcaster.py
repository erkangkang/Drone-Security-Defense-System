"""
实时数据广播器
Real-time Data Broadcaster
"""

import asyncio
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ...utils.logger import get_logger


class Broadcaster:
    """实时数据广播器

    定期收集数据并通过WebSocket广播给客户端
    """

    def __init__(self, websocket_manager, web_bridge, interval: float = 5.0):
        self.websocket_manager = websocket_manager
        self.web_bridge = web_bridge
        self.interval = interval
        self.running = False
        self.broadcast_thread: Optional[threading.Thread] = None
        self.loop = None
        self.logger = get_logger("broadcaster")

    def start(self):
        """启动广播器"""
        if self.running:
            return

        self.running = True

        # 在新线程中运行事件循环
        self.broadcast_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.broadcast_thread.start()

        self.logger.info("广播器已启动")

    def stop(self):
        """停止广播器"""
        if not self.running:
            return

        self.running = False

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2.0)

        self.logger.info("广播器已停止")

    def _run_loop(self):
        """运行事件循环"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._broadcast_loop())
        except Exception as e:
            self.logger.error(f"广播循环异常: {e}")
        finally:
            self.loop.close()

    async def _broadcast_loop(self):
        """广播循环"""
        while self.running:
            try:
                # 广播系统状态
                await self._broadcast_system_status()

                # 广播检测器状态
                await self._broadcast_detector_stats()

                # 等待指定间隔
                await asyncio.sleep(self.interval)

            except Exception as e:
                self.logger.error(f"广播失败: {e}")
                await asyncio.sleep(1.0)

    async def _broadcast_system_status(self):
        """广播系统状态"""
        try:
            status = self.web_bridge.get_system_status()
            await self.websocket_manager.broadcast_system_update(status)
        except Exception as e:
            self.logger.error(f"广播系统状态失败: {e}")

    async def _broadcast_detector_stats(self):
        """广播检测器统计"""
        try:
            stats = self.web_bridge.get_detector_stats()
            for name, stat in stats.items():
                await self.websocket_manager.broadcast_detector_status(name, stat)
        except Exception as e:
            self.logger.error(f"广播检测器统计失败: {e}")

    async def broadcast_immediate(self, event_type: str, data: Dict[str, Any]):
        """立即广播事件"""
        try:
            if event_type == "threat":
                await self.websocket_manager.broadcast_threat(data)
            elif event_type == "alert":
                await self.websocket_manager.broadcast_alert(data)
            elif event_type == "system":
                await self.websocket_manager.broadcast_system_update(data)
            else:
                await self.websocket_manager.broadcast({
                    "type": event_type,
                    "data": data
                })
        except Exception as e:
            self.logger.error(f"立即广播失败: {e}")

    def set_interval(self, interval: float):
        """设置广播间隔"""
        self.interval = max(1.0, interval)
        self.logger.info(f"广播间隔已设置为: {self.interval}秒")
