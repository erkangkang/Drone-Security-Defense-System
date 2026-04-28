"""
GPS 欺骗检测器
GPS Spoofing Detector
"""

import math
import time
from typing import Any, Dict, Optional
from collections import deque

from .base_detector import BaseDetector
from ..core.event_bus import EventBus
from ..core.config_manager import DetectorConfig
from ..utils.logger import get_logger
from ..models.threat_event import ThreatEvent, Severity, ThreatType
from ..models.telemetry import GPSData


class GPSDetector(BaseDetector):
    """GPS欺骗检测器"""

    def __init__(self, event_bus: EventBus, config: DetectorConfig):
        super().__init__(event_bus, config)
        self.name = "GPSDetector"

        # 位置跟踪
        self.position_history: deque = deque(maxlen=100)
        self.velocity_history: deque = deque(maxlen=50)
        self.altitude_history: deque = deque(maxlen=50)

        # 配置
        self.max_jump_distance = config.settings.get("max_jump_distance", 1000)  # 米
        self.max_acceleration = config.settings.get("max_acceleration", 10.0)   # m/s²
        self.min_satellites = config.settings.get("min_satellites", 6)
        self.max_velocity_mismatch = config.settings.get("max_velocity_mismatch", 5.0)  # m/s

        # 统计
        self.jump_count = 0
        self.satellite_low_count = 0
        self.velocity_mismatch_count = 0

        # 上一位置
        self.last_position: Optional[tuple] = None
        self.last_time: Optional[float] = None

    def initialize(self) -> bool:
        """初始化检测器"""
        self.logger.info("GPS检测器初始化完成")
        return True

    def analyze(self, data: Any) -> Optional[ThreatEvent]:
        """分析GPS数据"""
        if not isinstance(data, GPSData):
            gps_data = self._parse_gps_data(data)
            if not gps_data:
                return None
            data = gps_data

        # 记录历史
        self.position_history.append(data)
        self.altitude_history.append(data.altitude)

        # 检测位置跳变
        jump_event = self._detect_position_jump(data)
        if jump_event:
            return jump_event

        # 检测卫星数量异常
        sat_event = self._detect_satellite_anomaly(data)
        if sat_event:
            return sat_event

        # 检测信号质量异常
        signal_event = self._detect_signal_quality(data)
        if signal_event:
            return signal_event

        # 更新位置跟踪
        self._update_position_tracking(data)

        return None

    def _parse_gps_data(self, data: Any) -> Optional[GPSData]:
        """解析GPS数据"""
        try:
            if isinstance(data, dict):
                return GPSData(
                    latitude=data.get("latitude", 0.0),
                    longitude=data.get("longitude", 0.0),
                    altitude=data.get("altitude", 0.0),
                    satellite_count=data.get("satellite_count", 0),
                    hdop=data.get("hdop", 0.0),
                    vdop=data.get("vdop", 0.0),
                    fix_type=data.get("fix_type", 0),
                    ground_speed=data.get("ground_speed", 0.0),
                    ground_course=data.get("ground_course", 0.0)
                )
            elif hasattr(data, "__dict__"):
                return GPSData(
                    latitude=getattr(data, "latitude", 0.0),
                    longitude=getattr(data, "longitude", 0.0),
                    altitude=getattr(data, "altitude", 0.0),
                    satellite_count=getattr(data, "satellite_count", 0),
                    hdop=getattr(data, "hdop", 0.0),
                    vdop=getattr(data, "vdop", 0.0),
                    fix_type=getattr(data, "fix_type", 0),
                    ground_speed=getattr(data, "ground_speed", 0.0),
                    ground_course=getattr(data, "ground_course", 0.0)
                )
        except Exception as e:
            self.logger.error(f"解析GPS数据失败: {e}")

        return None

    def _detect_position_jump(self, gps: GPSData) -> Optional[ThreatEvent]:
        """检测位置跳变"""
        if self.last_position is None or self.last_time is None:
            self.last_position = (gps.latitude, gps.longitude, gps.altitude)
            self.last_time = time.time()
            return None

        current_time = time.time()
        dt = current_time - self.last_time

        if dt < 0.1:  # 时间间隔太短，跳过
            return None

        # 计算距离
        last_lat, last_lon, last_alt = self.last_position
        distance = self._haversine_distance(
            last_lat, last_lon,
            gps.latitude, gps.longitude
        )

        # 计算垂直距离
        alt_diff = abs(gps.altitude - last_alt)
        total_distance = math.sqrt(distance**2 + alt_diff**2)

        # 计算允许的最大距离（基于速度约束）
        max_allowed = self.max_velocity_mismatch * dt

        # 检测跳变
        if total_distance > max_allowed and total_distance > 10:  # 至少10米才算跳变
            self.jump_count += 1
            confidence = min(total_distance / self.max_jump_distance, 1.0)

            return ThreatEvent(
                threat_type=ThreatType.GPS_POSITION_JUMP.value,
                severity=Severity.HIGH if confidence > 0.7 else Severity.MEDIUM,
                detector=self.name,
                source=gps.source,
                evidence={
                    "previous_position": self.last_position,
                    "current_position": (gps.latitude, gps.longitude, gps.altitude),
                    "distance": total_distance,
                    "horizontal_distance": distance,
                    "vertical_distance": alt_diff,
                    "time_delta": dt,
                    "max_allowed": max_allowed
                },
                confidence=confidence
            )

        self.last_position = (gps.latitude, gps.longitude, gps.altitude)
        self.last_time = current_time
        return None

    def _detect_satellite_anomaly(self, gps: GPSData) -> Optional[ThreatEvent]:
        """检测卫星数量异常"""
        if gps.satellite_count < self.min_satellites:
            self.satellite_low_count += 1

            # 持续低卫星数
            if self.satellite_low_count > 10:
                return ThreatEvent(
                    threat_type=ThreatType.GPS_SPOOFING.value,
                    severity=Severity.MEDIUM,
                    detector=self.name,
                    source=gps.source,
                    evidence={
                        "satellite_count": gps.satellite_count,
                        "min_required": self.min_satellites,
                        "fix_type": gps.fix_type,
                        "hdop": gps.hdop,
                        "vdop": gps.vdop
                    },
                    confidence=0.6
                )
        else:
            self.satellite_low_count = 0

        return None

    def _detect_signal_quality(self, gps: GPSData) -> Optional[ThreatEvent]:
        """检测信号质量异常"""
        # HDOP值过高表示精度差
        if gps.hdop > 20.0 or gps.vdop > 20.0:
            return ThreatEvent(
                threat_type=ThreatType.GPS_SPOOFING.value,
                severity=Severity.LOW,
                detector=self.name,
                source=gps.source,
                evidence={
                    "hdop": gps.hdop,
                    "vdop": gps.vdop,
                    "satellite_count": gps.satellite_count,
                    "fix_type": gps.fix_type
                },
                confidence=0.5
            )

        # 检测HDOP异常（正常值在1-2，突然变化）
        if len(self.position_history) > 10:
            recent_hdop = [g.hdop for g in list(self.position_history)[-10:] if g.hdop > 0]
            if recent_hdop:
                avg_hdop = sum(recent_hdop) / len(recent_hdop)
                if gps.hdop > 0 and abs(gps.hdop - avg_hdop) > avg_hdop * 3:
                    return ThreatEvent(
                        threat_type=ThreatType.GPS_SPOOFING.value,
                        severity=Severity.MEDIUM,
                        detector=self.name,
                        source=gps.source,
                        evidence={
                            "current_hdop": gps.hdop,
                            "average_hdop": avg_hdop,
                            "hdop_change": abs(gps.hdop - avg_hdop)
                        },
                        confidence=0.65
                    )

        return None

    def _update_position_tracking(self, gps: GPSData) -> None:
        """更新位置跟踪"""
        # 计算速度
        if gps.ground_speed > 0:
            self.velocity_history.append(gps.ground_speed)

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点间的大圆距离（Haversine公式），单位：米"""
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

    def _loop_iteration(self):
        """单次迭代（被动模式）"""
        pass

    def cleanup(self) -> None:
        """清理资源"""
        self.position_history.clear()
        self.velocity_history.clear()
        self.altitude_history.clear()
        self.last_position = None
        self.last_time = None
