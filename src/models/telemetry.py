"""
遥测数据模型
Telemetry Data Model
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class GPSData:
    """GPS数据"""
    latitude: float = 0.0
    longitude: float = 0.0
    altitude: float = 0.0
    timestamp: datetime = None
    satellite_count: int = 0
    hdop: float = 0.0  # 水平精度因子
    vdop: float = 0.0  # 垂直精度因子
    fix_type: int = 0
    ground_speed: float = 0.0
    ground_course: float = 0.0
    source: str = "gps"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "timestamp": self.timestamp.isoformat(),
            "satellite_count": self.satellite_count,
            "hdop": self.hdop,
            "vdop": self.vdop,
            "fix_type": self.fix_type,
            "ground_speed": self.ground_speed,
            "ground_course": self.ground_course,
            "source": self.source
        }


@dataclass
class IMUData:
    """IMU数据"""
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 0.0
    timestamp: datetime = None
    source: str = "imu"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gyro": [self.gyro_x, self.gyro_y, self.gyro_z],
            "accel": [self.accel_x, self.accel_y, self.accel_z],
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


@dataclass
class SensorData:
    """传感器数据"""
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    altitude: Optional[float] = None
    magnetic_x: Optional[float] = None
    magnetic_y: Optional[float] = None
    magnetic_z: Optional[float] = None
    timestamp: datetime = None
    source: str = "sensor"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "altitude": self.altitude,
            "magnetic": [self.magnetic_x, self.magnetic_y, self.magnetic_z],
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


@dataclass
class MAVLinkMessage:
    """MAVLink消息"""
    msg_id: int = 0
    sys_id: int = 0
    comp_id: int = 0
    seq: int = 0
    timestamp: datetime = None
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "mavlink"

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sys_id": self.sys_id,
            "comp_id": self.comp_id,
            "seq": self.seq,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "source": self.source
        }


@dataclass
class NetworkConnection:
    """网络连接"""
    source_ip: str = ""
    source_port: int = 0
    dest_ip: str = ""
    dest_port: int = 0
    protocol: str = ""
    timestamp: datetime = None
    bytes_sent: int = 0
    bytes_received: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_ip": self.source_ip,
            "source_port": self.source_port,
            "dest_ip": self.dest_ip,
            "dest_port": self.dest_port,
            "protocol": self.protocol,
            "timestamp": self.timestamp.isoformat(),
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received
        }
