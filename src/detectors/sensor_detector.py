"""
传感器欺骗检测器
Sensor Spoofing Detector
"""

import math
import time
from typing import Any, Dict, Optional, List
from collections import deque

from .base_detector import BaseDetector
from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..models.threat_event import ThreatEvent, Severity, ThreatType
from ..models.telemetry import SensorData, IMUData


class SensorDetector(BaseDetector):
    """传感器欺骗检测器"""

    def __init__(self, event_bus: EventBus, config: DetectorConfig):
        super().__init__(event_bus, config)
        self.name = "SensorDetector"

        # 历史数据
        self.sensor_history: deque = deque(maxlen=100)
        self.imu_history: deque = deque(maxlen=50)
        self.altitude_history: deque = deque(maxlen=50)

        # 配置
        self.temperature_range = config.settings.get("temperature_range", [-40, 85])
        self.pressure_range = config.settings.get("pressure_range", [300, 1100])
        self.max_noise_level = config.settings.get("max_noise_level", 5.0)
        self.imu_max_rate = config.settings.get("imu_max_rate", 1000.0)  # rad/s

        # 统计
        self.range_violation_count = 0
        self.inconsistency_count = 0

    def initialize(self) -> bool:
        """初始化检测器"""
        self.logger.info("传感器检测器初始化完成")
        return True

    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析传感器数据"""
        # 处理IMU数据
        if isinstance(data, IMUData) or (hasattr(data, 'accel_x') and hasattr(data, 'gyro_x')):
            imu_data = self._parse_imu_data(data)
            if imu_data:
                self.imu_history.append(imu_data)
                return self._analyze_imu(imu_data)

        # 处理传感器数据
        elif isinstance(data, SensorData) or (hasattr(data, 'pressure') or hasattr(data, 'altitude')):
            sensor_data = self._parse_sensor_data(data)
            if sensor_data:
                self.sensor_history.append(sensor_data)

                # 有高度数据则记录
                if sensor_data.altitude is not None:
                    self.altitude_history.append(sensor_data.altitude)

                return self._analyze_sensor(sensor_data)

        return None

    def _parse_sensor_data(self, data: Any) -> Optional[SensorData]:
        """解析传感器数据"""
        try:
            if isinstance(data, dict):
                return SensorData(
                    temperature=data.get("temperature"),
                    pressure=data.get("pressure"),
                    altitude=data.get("altitude"),
                    magnetic_x=data.get("magnetic_x"),
                    magnetic_y=data.get("magnetic_y"),
                    magnetic_z=data.get("magnetic_z")
                )
            elif hasattr(data, "__dict__"):
                return SensorData(
                    temperature=getattr(data, "temperature", None),
                    pressure=getattr(data, "pressure", None),
                    altitude=getattr(data, "altitude", None),
                    magnetic_x=getattr(data, "magnetic_x", None),
                    magnetic_y=getattr(data, "magnetic_y", None),
                    magnetic_z=getattr(data, "magnetic_z", None)
                )
        except Exception as e:
            self.logger.error(f"解析传感器数据失败: {e}")

        return None

    def _parse_imu_data(self, data: Any) -> Optional[IMUData]:
        """解析IMU数据"""
        try:
            if isinstance(data, dict):
                return IMUData(
                    gyro_x=data.get("gyro_x", 0.0),
                    gyro_y=data.get("gyro_y", 0.0),
                    gyro_z=data.get("gyro_z", 0.0),
                    accel_x=data.get("accel_x", 0.0),
                    accel_y=data.get("accel_y", 0.0),
                    accel_z=data.get("accel_z", 0.0)
                )
            elif hasattr(data, "__dict__"):
                return IMUData(
                    gyro_x=getattr(data, "gyro_x", 0.0),
                    gyro_y=getattr(data, "gyro_y", 0.0),
                    gyro_z=getattr(data, "gyro_z", 0.0),
                    accel_x=getattr(data, "accel_x", 0.0),
                    accel_y=getattr(data, "accel_y", 0.0),
                    accel_z=getattr(data, "accel_z", 0.0)
                )
        except Exception as e:
            self.logger.error(f"解析IMU数据失败: {e}")

        return None

    def _analyze_sensor(self, sensor: SensorData) -> Optional[ThreatEvent]:
        """分析传感器数据"""
        # 检测范围违规
        range_event = self._detect_range_violation(sensor)
        if range_event:
            return range_event

        # 检测异常噪声
        noise_event = self._detect_noise_anomaly(sensor)
        if noise_event:
            return noise_event

        return None

    def _analyze_imu(self, imu: IMUData) -> Optional[ThreatEvent]:
        """分析IMU数据"""
        # 检测IMU异常值
        gyro_magnitude = math.sqrt(imu.gyro_x**2 + imu.gyro_y**2 + imu.gyro_z**2)
        accel_magnitude = math.sqrt(imu.accel_x**2 + imu.accel_y**2 + imu.accel_z**2)

        # 检测陀螺仪异常
        if gyro_magnitude > self.imu_max_rate:
            return ThreatEvent(
                threat_type=ThreatType.SENSOR_SPOOFING.value,
                severity=Severity.HIGH,
                detector=self.name,
                source="imu",
                evidence={
                    "gyro_x": imu.gyro_x,
                    "gyro_y": imu.gyro_y,
                    "gyro_z": imu.gyro_z,
                    "gyro_magnitude": gyro_magnitude,
                    "max_allowed": self.imu_max_rate
                },
                confidence=0.9
            )

        # 检测加速度异常（正常应该接近9.8m/s²）
        if abs(accel_magnitude - 9.8) > 20.0:
            return ThreatEvent(
                threat_type=ThreatType.SENSOR_SPOOFING.value,
                severity=Severity.MEDIUM,
                detector=self.name,
                source="imu",
                evidence={
                    "accel_x": imu.accel_x,
                    "accel_y": imu.accel_y,
                    "accel_z": imu.accel_z,
                    "accel_magnitude": accel_magnitude,
                    "expected": 9.8
                },
                confidence=0.7
            )

        return None

    def _detect_range_violation(self, sensor: SensorData) -> Optional[ThreatEvent]:
        """检测范围违规"""
        violations = {}

        # 温度范围检查
        if sensor.temperature is not None:
            min_temp, max_temp = self.temperature_range
            if sensor.temperature < min_temp or sensor.temperature > max_temp:
                violations["temperature"] = {
                    "value": sensor.temperature,
                    "range": self.temperature_range
                }

        # 压力范围检查
        if sensor.pressure is not None:
            min_press, max_press = self.pressure_range
            if sensor.pressure < min_press or sensor.pressure > max_press:
                violations["pressure"] = {
                    "value": sensor.pressure,
                    "range": self.pressure_range
                }

        if violations:
            self.range_violation_count += 1

            if self.range_violation_count > 5:
                return ThreatEvent(
                    threat_type=ThreatType.SENSOR_SPOOFING.value,
                    severity=Severity.MEDIUM,
                    detector=self.name,
                    source=sensor.source,
                    evidence={
                        "violations": violations,
                        "count": self.range_violation_count
                    },
                    confidence=0.8
                )

        return None

    def _detect_noise_anomaly(self, sensor: SensorData) -> Optional[ThreatEvent]:
        """检测噪声异常"""
        if len(self.sensor_history) < 10:
            return None

        # 检测高度数据异常
        if sensor.altitude is not None and len(self.altitude_history) >= 10:
            recent_altitudes = list(self.altitude_history)[-10:]
            mean_alt = sum(recent_altitudes) / len(recent_altitudes)
            std_alt = math.sqrt(sum((a - mean_alt) ** 2 for a in recent_altitudes) / len(recent_altitudes))

            # 如果某个值偏离超过3个标准差
            if std_alt > 0 and abs(sensor.altitude - mean_alt) > 3 * std_alt:
                return ThreatEvent(
                                       threat_type=ThreatType.SENSOR_SPOOFING.value,
                    severity=Severity.LOW,
                    detector=self.name,
                    source=sensor.source,
                    evidence={
                        "altitude": sensor.altitude,
                        "mean": mean_alt,
                        "std": std_alt,
                        "deviation": abs(sensor.altitude - mean_alt)
                    },
                    confidence=0.6
                )

        return None

    def _loop_iteration(self):
        """单次迭代（被动模式）"""
        pass

    def cleanup(self) -> None:
        """清理资源"""
        self.sensor_history.clear()
        self.imu_history.clear()
        self.altitude_history.clear()
