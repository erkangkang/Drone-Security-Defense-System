"""
 接口
 Interface
"""

import time
import math
from typing import Optional, Dict, Any, Callable, List
from threading import Thread, Lock
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..models.telemetry import Data


@dataclass
class Position:
    """位置"""
    latitude: float
    longitude: float
    altitude: float
    timestamp: float


class Interface:
    """数据接口"""

    def __init__(self):
        self.connected = False
        self.current_position: Optional[Position] = None
        self.position_history: List[Position] = []

        # 配置
        self.update_interval = 1.0  # 秒
        self.satellite_count = 0
        self.hdop = 0.0
        self.vdop = 0.0
        self.fix_type = 0

        # 消息处理
        self.data_handlers: List[Callable[[Data], None]] = []
        self.lock = Lock()

        # 线程
        self.thread: Optional[Thread] = None
        self.running = False

        # 统计
        self.updates_received = 0
        self.errors = 0

        self.logger = get_logger("")

    def connect(self, connection_string: str) -> bool:
        """连接到设备"""
        try:
            # 这里简化实现
            # 实际实现可能需要连接串口、NTRIP客户端等
            self.connected = True
            self.logger.info(f"已连接: {connection_string}")
            return True

        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            self.errors += 1
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False

        if self.thread:
            self.thread.join(timeout=3)
            self.thread = None

        self.connected = False
        self.logger.info("已断开")

    def start_reading(self, callback: Optional[Callable[[Data], None]] = None) -> None:
        """开始读取数据"""
        if not self.connected:
            self.logger.error("未连接")
            return

        if callback:
            with self.lock:
                self.data_handlers.append(callback)

        self.running = True
        self.thread = Thread(
            target=self._read_loop,
            name="Reader",
            daemon=True
        )
        self.thread.start()

        self.logger.info("读取已启动")

    def _read_loop(self):
        """读取循环"""
        while self.running:
            try:
                # 在实际实现中，这里会从设备读取数据
                # 这里是模拟实现
                pass

                time.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"读取数据错误: {e}")
                self.errors += 1

    def update_position(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        satellite_count: int = 0,
        hdop: float = 0.0,
        vdop: float = 0.0,
        fix_type: int = 0
    ) -> None:
        """更新位置（手动调用）"""
        position = Position(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            timestamp=time.time()
        )

        self.current_position = position
        self.position_history.append(position)

        # 限制历史长度
        if len(self.position_history) > 1000:
            self.position_history = self.position_history[-1000:]

        self.satellite_count = satellite_count
        self.hdop = hdop
        self.vdop = vdop
        self.fix_type = fix_type

        self.updates_received += 1

        # 创建Data并调用处理器
        _data = Data(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            satellite_count=satellite_count,
            hdop=hdop,
            vdop=vdop,
            fix_type=fix_type
        )

        with self.lock:
            for handler in self.data_handlers:
                try:
                    handler(_data)
                except Exception as e:
                    self.logger.error(f"数据处理器错误: {e}")

    def get_current_position(self) -> Optional[Position]:
        """获取当前位置"""
        return self.current_position

    def get_position_history(self, limit: int = 100) -> List[Position]:
        """获取位置历史"""
        return self.position_history[-limit:]

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def calculate_speed(
        self,
        lat1: float,
lon1: float,
        lat2: float,
        lon2: float,
        time_delta: float
    ) -> float:
        """计算速度（m/s）"""
        if time_delta <= 0:
            return 0.0

        distance = self.calculate_distance(lat1, lon1, lat2, lon2)
        return distance / time_delta

    def calculate_bearing(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """计算方位角（度）"""
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad

        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)

        return (bearing + 360) % 360

    def add_data_handler(self, handler: Callable[[Data], None]) -> None:
        """添加数据处理器"""
        with self.lock:
            self.data_handlers.append(handler)

    def remove_data_handler(self, handler: Callable[[Data], None]) -> None:
        """移除数据处理器"""
        with self.lock:
            if handler in self.data_handlers:
                self.data_handlers.remove(handler)

    def get_info(self) -> Dict[str, Any]:
        """获取信息"""
        return {
            "connected": self.connected,
            "has_position": self.current_position is not None,
            "satellite_count": self.satellite_count,
            "hdop": self.hdop,
            "vdop": self.vdop,
            "fix_type": self.fix_type,
            "updates_received": self.updates_received,
            "errors": self.errors
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connected": self.connected,
            "updates_received": self.updates_received,
            "errors": self.errors,
            "position_history_size": len(self.position_history),
            "handlers_count": len(self.data_handlers)
        }
