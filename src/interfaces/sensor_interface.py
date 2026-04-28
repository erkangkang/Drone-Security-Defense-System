"""
传感器接口
Sensor Interface
"""

import time
from typing import Optional, Dict, Any, Callable, List
from threading import Thread, Lock

from ..utils.logger import get_logger
from ..models.telemetry import SensorData, IMUData


class SensorInterface:
    """传感器数据接口"""

    def __init__(self):
        self.connected = False

        # 传感器数据
        self.current_sensor_data: Optional[SensorData] = None
        self.current_imu_data: Optional[IMUData] = None

        # 配置
        self.update_interval = 0.1  # 秒

        # 消息处理
        self.sensor_handlers: List[Callable[[SensorData], None]] = []
        self.imu_handlers: List[Callable[[IMUData], None]] = []

        self.lock = Lock()

        # 线程
        self.thread: Optional[Thread] = None
        self.running = False

        # 统计
        self.sensor_updates = 0
        self.imu_updates = 0
        self.errors = 0

        self.logger = get_logger("sensor")

    def connect(self, connection_string: str) -> bool:
        """连接到传感器设备"""
        try:
            # 这里简化实现
            # 实际实现可能需要连接I2C、SPI、串口等
            self.connected = True
            self.logger.info(f"传感器已连接: {connection_string}")
            return True

        except Exception as e:
            self.logger.error(f"传感器连接失败: {e}")
            self.errors += 1
            return False

    def disconnect(self) -> None:
        """断开连接"""
        self.running = False

        if self.thread:
            self.thread.join(timeout=3)
            self.thread = None

        self.connected = False
        self.logger.info("传感器已断开")

    def start_reading(self) -> None:
        """开始读取传感器数据"""
        if not self.connected:
            self.logger.error("传感器未连接")
            return

        self.running = True
        self.thread = Thread(
            target=self._read_loop,
            name="SensorReader",
            daemon=True
        )
        self.thread.start()

        self.logger.info("传感器读取已启动")

    def _read_loop(self):
        """读取循环"""
        while self.running:
            try:
                # 在实际实现中，这里会从传感器读取数据
                # 这里是模拟实现
                pass

                time.sleep(self.update_interval)

            except Exception as e:
                self.logger.error(f"读取传感器数据错误: {e}")
                self.errors += 1

    def update_sensor_data(
        self,
        temperature: Optional[float] = None,
        pressure: Optional[float] = None,
        altitude: Optional[float] = None,
        magnetic_x: Optional[float] = None,
        magnetic_y: Optional[float] = None,
        magnetic_z: Optional[float] = None
    ) -> None:
        """更新传感器数据（手动调用）"""
        sensor_data = SensorData(
            temperature=temperature,
            pressure=pressure,
            altitude=altitude,
            magnetic_x=magnetic_x,
            magnetic_y=magnetic_y,
            magnetic_z=magnetic_z
        )

        self.current_sensor_data = sensor_data
        self.sensor_updates += 1

        # 调用处理器
        with self.lock:
            for handler in self.sensor_handlers:
                try:
                    handler(sensor_data)
                except Exception as e:
                    self.logger.error(f"传感器数据处理器错误: {e}")

    def update_imu_data(
        self,
        gyro_x: float = 0.0,
        gyro_y: float = 0.0,
        gyro_z: float = 0.0,
        accel_x: float = 0.0,
        accel_y: float = 0.0,
        accel_z: float = 0.0
    ) -> None:
        """更新IMU数据（手动调用）"""
        imu_data = IMUData(
            gyro_x=gyro_x,
            gyro_y=gyro_y,
            gyro_z=gyro_z,
            accel_x=accel_x,
            accel_y=accel_y,
            accel_z=accel_z
        )

        self.current_imu_data = imu_data
        self.imu_updates += 1

        # 调用处理器
        with self.lock:
            for handler in self.imu_handlers:
                try:
                    handler(imu_data)
                except Exception as e:
                    self.logger.error(f"IMU数据处理器错误: {e}")

    def get_current_sensor_data(self) -> Optional[SensorData]:
        """获取当前传感器数据"""
        return self.current_sensor_data

    def get_current_imu_data(self) -> Optional[IMUData]:
        """获取当前IMU数据"""
        return self.current_imu_data

    def calculate_altitude_from_pressure(self, pressure: float, sea_level_pressure: float = 1013.25) -> float:
        """根据气压计算高度（米）"""
        # 国际标准大气模型
        return 44330 * (1 - (pressure / sea_level_pressure) ** (1 / 5.255))

    def calculate_pressure_from_altitude(self, altitude: float, sea_level_pressure: float = 1013.25) -> float:
        """根据高度计算气压（hPa）"""
        return sea_level_pressure * (1 - altitude / 44330) ** 5.255

    def add_sensor_handler(self, handler: Callable[[SensorData], None]) -> None:
        """添加传感器数据处理器"""
        with self.lock:
            self.sensor_handlers.append(handler)

    def add_imu_handler(self, handler: Callable[[IMUData], None]) -> None:
        """添加IMU数据处理器"""
        with self.lock:
            self.imu_handlers.append(handler)

    def remove_sensor_handler(self, handler: Callable[[SensorData], None]) -> None:
        """移除传感器数据处理器"""
        with self.lock:
            if handler in self.sensor_handlers:
                self.sensor_handlers.remove(handler)

    def remove_imu_handler(self, handler: Callable[[IMUData], None]) -> None:
        """移除IMU数据处理器"""
        with self.lock:
            if handler in self.imu_handlers:
                self.imu_handlers.remove(handler)

    def get_info(self) -> Dict[str, Any]:
        """获取传感器信息"""
        return {
            "connected": self.connected,
            "has_sensor_data": self.current_sensor_data is not None,
            "has_imu_data": self.current_imu_data is not None,
            "sensor_updates": self.sensor_updates,
            "imu_updates": self.imu_updates,
            "errors": self.errors
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connected": self.connected,
            "sensor_updates": self.sensor_updates,
            "imu_updates": self.imu_updates,
            "errors": self.errors,
            "sensor_handlers_count": len(self.sensor_handlers),
            "imu_handlers_count": len(self.imu_handlers)
        }
